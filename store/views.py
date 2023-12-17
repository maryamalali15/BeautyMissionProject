import random
import string

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .forms import CheckoutForm, CouponForm, PaymentForm
from .models import Item, OrderItem, Order, Address, Coupon, Service, Booking



def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            if self.request.user.is_authenticated:
                user = self.request.user
                guest_id = None
            else:
                user = None
                guest_id = self.request.session.session_key
                if not guest_id:
                    # Create a new session if one doesn't exist
                    self.request.session.create()
                    guest_id = self.request.session.session_key
           
            order = Order.objects.get(user=user, guest_id=guest_id, ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform': CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM': True
            }

            shipping_address_qs = Address.objects.filter(
                user=user, guest_id=guest_id,
                address_type='S',
                default=True
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address': shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(
                user=user, guest_id=guest_id,
                address_type='B',
                default=True
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address': billing_address_qs[0]})
            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST)
        try:
            if self.request.user.is_authenticated:
                user = self.request.user
                guest_id = None
            else:
                user = None
                guest_id = self.request.session.session_key
                if not guest_id:
                    # Create a new session if one doesn't exist
                    self.request.session.create()
                    guest_id = self.request.session.session_key

            order = Order.objects.get(user=user, guest_id=guest_id, ordered=False)
            if form.is_valid():

                use_default_shipping = form.cleaned_data.get(
                    'use_default_shipping')
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        user=user, guest_id=guest_id,
                        address_type='S',
                        default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.ordered = True
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get(
                        'shipping_address')
                    shipping_address2 = form.cleaned_data.get(
                        'shipping_address2')
                    shipping_country = form.cleaned_data.get(
                        'shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
                        shipping_address = Address(
                            user=user, guest_id=guest_id,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.ordered = True
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            'set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request, "Please fill in the required shipping address fields")

                use_default_billing = form.cleaned_data.get(
                    'use_default_billing')
                same_billing_address = form.cleaned_data.get(
                    'same_billing_address')

                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.ordered = True
                    order.save()
                    print("set default none")
                    messages.info(self.request, "Your order is placed successfully.")
                    return redirect('core:home')

                elif use_default_billing:
                    print("Using the defualt billing address")
                    address_qs = Address.objects.filter(
                        user=user, guest_id=guest_id,
                        address_type='B',
                        default=True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.ordered = True
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default billing address available")
                        return redirect('core:checkout')
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get(
                        'billing_address')
                    billing_address2 = form.cleaned_data.get(
                        'billing_address2')
                    billing_country = form.cleaned_data.get(
                        'billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    if is_valid_form([billing_address1, billing_country, billing_zip]):
                        billing_address = Address(
                            user=user, guest_id=guest_id,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()

                        order.billing_address = billing_address
                        order.ordered = True
                        order.save()
                        print("test")

                        set_default_billing = form.cleaned_data.get(
                            'set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                            messages.info(self.request, "Your order is placed successfully.")
                            return redirect('core:home')
                        else:
                            print("test1")
                            messages.info(self.request, "Your order is placed successfully.")
                            return redirect('core:home')

                    else:
                        messages.info(
                            self.request, "Please fill in the required billing address fields")

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")


class HomeView(ListView):
    model = Item
    paginate_by = 8
    template_name = "home.html"
    context_object_name = 'items'

    def get_queryset(self):
        query = self.request.GET.get('q')
        
        if query:
            return Item.objects.filter(Q(title__icontains=query))
        else:
            return Item.objects.all()
        
    def get(self, request, *args, **kwargs):
        # Call the parent class's get method to get the queryset
        response = super().get(request, *args, **kwargs)

        # If the queryset is empty and there was a search query, redirect to home
        if not self.get_queryset() and self.request.GET.get('q'):
            return redirect('core:home')

        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # pagination for services
        services_list = Service.objects.all()
        page = self.request.GET.get('service_page', 1)
        paginator = Paginator(services_list, 8) # 8 services per page

        try:
            services = paginator.page(page)
        except PageNotAnInteger:
            services = paginator.page(1)
        except EmptyPage:
            services = paginator.page(paginator.num_pages)

        context['services'] = services
        return context


from django.contrib.sessions.models import Session
class OrderSummaryView( View):
    def get(self, *args, **kwargs):
        try:
            if self.request.user.is_authenticated:
                user = self.request.user
                guest_id = None
            else:
                user = None
                guest_id = self.request.session.session_key
                if not guest_id:
                    # Create a new session if one doesn't exist
                    self.request.session.create()
                    guest_id = self.request.session.session_key

            order = Order.objects.get(user=user, guest_id=guest_id, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"


#@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    # Check if the user is authenticated
    if request.user.is_authenticated:
        user = request.user
        guest_id = None
    else:
        user = None
        guest_id = request.session.session_key
        if not guest_id:
            # Create a new session if one doesn't exist
            request.session.create()
            guest_id = request.session.session_key
    
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=user,
        guest_id=guest_id,
        ordered=False
    )
    order_qs = Order.objects.filter(user=user, guest_id=guest_id, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            user=user, guest_id=guest_id, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("core:order-summary")


#@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if request.user.is_authenticated:
        user = request.user
        guest_id = None
    else:
        user = None
        guest_id = request.session.session_key
        if not guest_id:
            # Create a new session if one doesn't exist
            request.session.create()
            guest_id = request.session.session_key
    order_qs = Order.objects.filter(
        user=user,
        guest_id=guest_id,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=user,
                guest_id=guest_id,
                ordered=False
            )[0]
            order.items.remove(order_item)
            #order.delete()
            order_item.delete()
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


#@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    if request.user.is_authenticated:
        user = request.user
        guest_id = None
    else:
        user = None
        guest_id = request.session.session_key
        if not guest_id:
            # Create a new session if one doesn't exist
            request.session.create()
            guest_id = request.session.session_key
    order_qs = Order.objects.filter(
        user=user,
        guest_id=guest_id,
        ordered=False
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item_queryset = OrderItem.objects.filter(
                item=item,
                user=user,
                guest_id=guest_id,
                ordered=True
            )
            if order_item_queryset.exists():
                order_item = order_item_queryset[0]
                if order_item.quantity > 1:
                    order_item.quantity -= 1
                    order_item.save()
                else:
                    order.items.remove(order_item)
                messages.info(request, "This item quantity was updated.")
                return redirect("core:order-summary")
            else:
                messages.info(request, "This item was not found in your cart")
                return redirect("core:product", slug=slug)
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request, "This coupon does not exist")
        return redirect("core:checkout")


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(
                    user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, "Successfully added coupon")
                return redirect("core:checkout")
            except ObjectDoesNotExist:
                messages.info(self.request, "You do not have an active order")
                return redirect("core:checkout")


# Service booking
def book_service(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    user = None
    guest_id = None

    if request.user.is_authenticated:
        user = request.user
        guest_id = None
    else:
        user = None
        guest_id = request.session.session_key
        if not guest_id:
            request.session.create()
            guest_id = request.session.session_key

    if request.method == 'POST':
        booking_name = request.POST.get('booking_name')
        date = request.POST.get('date')
        time = request.POST.get('time')

        booking = Booking(service=service, user=user, guest_id=guest_id, date=date, time=time, booking_name=booking_name)
        booking.save()
        messages.success(request, f"You have successfully booked '{service.name}'.")

    return render(request, 'service.html', {'service': service})