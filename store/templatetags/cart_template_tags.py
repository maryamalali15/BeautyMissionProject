from django import template
from store.models import Order, OrderItem
from django.contrib.auth.models import User


register = template.Library()


@register.simple_tag
def cart_item_count(user, guest_id):
    if user.is_authenticated:
        order_qs = Order.objects.filter(user=user, ordered=False)
    else:
        if guest_id:
            order_qs = Order.objects.filter(guest_id=guest_id, ordered=False)
        else:
            return 0

    if order_qs.exists():
        order = order_qs[0]
        return order.items.count()
    return 0

