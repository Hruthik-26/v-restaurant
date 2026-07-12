from django.contrib import admin

from .models import (
    Address,
    BlogPost,
    Category,
    Coupon,
    Customer,
    FavouriteItem,
    MenuItem,
    Notification,
    Order,
    OrderItem,
    Payment,
    RestaurantSettings,
    Review,
    TableReservation,
)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "is_available",
        "is_veg",
        "is_spicy",
        "rating",
        "is_chef_special",
    )
    list_filter = (
        "category",
        "is_available",
        "is_veg",
        "is_spicy",
        "is_chef_special",
        "is_today_offer",
    )
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "email",
        "reward_points",
        "is_mobile_verified",
        "is_email_verified",
        "created_at",
    )
    list_filter = ("is_mobile_verified", "is_email_verified", "created_at")
    search_fields = ("name", "phone", "email")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer_name",
        "dining_option",
        "status",
        "total_amount",
        "payment_status",
        "created_at",
    )
    list_filter = (
        "status",
        "dining_option",
        "payment_method",
        "payment_status",
        "created_at",
    )
    search_fields = ("order_number", "customer_name", "customer_phone")
    inlines = [OrderItemInline]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_percent",
        "active",
        "valid_from",
        "valid_to",
    )
    list_filter = ("active", "valid_from", "valid_to")
    search_fields = ("code",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("menu_item", "customer_name", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("customer_name", "comment")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "payment_method",
        "amount",
        "status",
        "transaction_id",
        "created_at",
    )
    list_filter = ("status", "payment_method", "created_at")


@admin.register(RestaurantSettings)
class RestaurantSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "restaurant_name",
        "opening_hours",
        "contact_phone",
        "contact_email",
        "delivery_charges",
        "gst_percentage",
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("customer", "address_line", "city", "is_default")
    list_filter = ("is_default", "city")
    search_fields = ("customer__name", "address_line", "city")


@admin.register(FavouriteItem)
class FavouriteItemAdmin(admin.ModelAdmin):
    list_display = ("customer", "menu_item", "created_at")
    search_fields = ("customer__name", "menu_item__name")


@admin.register(TableReservation)
class TableReservationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone",
        "num_guests",
        "reservation_date",
        "reservation_time",
        "status",
    )
    list_filter = ("status", "reservation_date")
    search_fields = ("name", "phone", "email")


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "content")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("customer", "title", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("customer__name", "title")
