from django.contrib import admin

from .models import Item, OrderItem, Order, Coupon, Address, Service, Booking


class OrderAdmin(admin.ModelAdmin):
    list_display = ['username_or_guest_id',
                    'ordered',
                    'being_delivered',
                    'received',
                    'shipping_address',
                    'billing_address',
                    'coupon'
                    ]
    list_display_links = [
        'username_or_guest_id',
        'shipping_address',
        'billing_address',
        'coupon'
    ]
    list_filter = ['ordered',
                   'being_delivered',
                   'received',]
    search_fields = [
        'user__username',
    ]
    
    def username_or_guest_id(self, obj):
        if obj.user:
            return obj.user.username
        elif obj.guest_id:
            return obj.guest_id


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'username_or_guest_id',
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'address_type',
        'default'
    ]
    list_filter = ['default', 'address_type', 'country']
    search_fields = ['username_or_guest_id', 'street_address', 'apartment_address', 'zip']

    def username_or_guest_id(self, obj):
        if obj.user:
            return obj.user.username
        elif obj.guest_id:
            return obj.guest_id


admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Service)
admin.site.register(Booking)
admin.site.register(Order, OrderAdmin)
admin.site.register(Address, AddressAdmin)
