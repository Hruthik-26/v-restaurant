import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    icon = models.CharField(
        max_length=50,
        default="bi-egg-fried",
        help_text="Bootstrap Icons class e.g. bi-egg-fried",
    )
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="items"
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="menu_items/", blank=True, null=True)
    image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Fallback web URL for mock food images",
    )
    is_veg = models.BooleanField(default=True)
    is_spicy = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=5.0)
    is_chef_special = models.BooleanField(default=False)
    is_today_offer = models.BooleanField(default=False)
    is_popular = models.BooleanField(default=False)
    is_recommended = models.BooleanField(default=False)
    origin = models.CharField(max_length=150, blank=True, default="Andhra")
    district = models.CharField(max_length=100, blank=True, default="Guntur")
    state = models.CharField(
        max_length=100, blank=True, default="Andhra Pradesh"
    )
    preparation_time = models.PositiveIntegerField(
        default=15, help_text="Preparation time in minutes"
    )
    calories = models.PositiveIntegerField(
        default=250, help_text="Calorie count"
    )
    spice_level = models.CharField(
        max_length=50,
        default="MEDIUM",
        choices=[
            ("MILD", "Mild"),
            ("MEDIUM", "Medium"),
            ("HOT", "Hot"),
            ("EXTRA_HOT", "Extra Hot"),
        ],
    )
    is_today_special = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_image_url(self):
        if self.image:
            return self.image.url
        return self.image_url or "/static/images/food-placeholder.png"

    def __str__(self):
        return self.name


class Customer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="customer",
    )
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True, default="")
    profile_photo = models.ImageField(
        upload_to="customer_profiles/", blank=True, null=True
    )
    reward_points = models.PositiveIntegerField(default=0)
    is_mobile_verified = models.BooleanField(default=True)
    is_email_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.PositiveIntegerField()
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField()

    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to

    def __str__(self):
        return f"{self.code} ({self.discount_percent}%)"


class Order(models.Model):
    DINING_OPTIONS = [
        ("DINE_IN", "Dine-In"),
        ("TAKE_AWAY", "Take Away"),
        ("DELIVERY", "Delivery"),
    ]

    STATUS_CHOICES = [
        ("RECEIVED", "Order Received"),
        ("PREPARING", "Preparing"),
        ("COOKING", "Cooking"),
        ("PACKED", "Packed"),
        ("READY", "Ready"),
        ("OUT_FOR_DELIVERY", "Out for Delivery"),
        ("DELIVERED", "Delivered"),
    ]

    PAYMENT_METHODS = [
        ("CASH", "Cash"),
        ("UPI", "UPI"),
        ("CARD", "Card/Net Banking"),
    ]

    PAYMENT_STATUS = [
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    order_number = models.CharField(max_length=50, unique=True, blank=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.SET_NULL, null=True, blank=True
    )
    customer_name = models.CharField(max_length=150)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(blank=True)
    customer_address = models.TextField(blank=True, null=True)
    table_number = models.CharField(max_length=20, blank=True, null=True)
    dining_option = models.CharField(
        max_length=20, choices=DINING_OPTIONS, default="DINE_IN"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="RECEIVED"
    )
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHODS, default="CASH"
    )
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS, default="PENDING"
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    delivery_charge = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_time = models.DateTimeField(blank=True, null=True)
    priority = models.IntegerField(
        default=0, help_text="Priority ordering weight for kitchen queue"
    )

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"SR-{uuid.uuid4().hex[:8].upper()}"
        if not self.estimated_time and self.created_at:
            self.estimated_time = self.created_at + timezone.timedelta(
                minutes=30
            )
        elif not self.estimated_time:
            self.estimated_time = timezone.now() + timezone.timedelta(
                minutes=30
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_number} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.name} for Order {self.order.order_number}"

    def get_total(self):
        return self.quantity * self.price


class Review(models.Model):
    menu_item = models.ForeignKey(
        MenuItem, on_delete=models.CASCADE, related_name="reviews"
    )
    customer_name = models.CharField(max_length=150)
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review ({self.rating}*) by {self.customer_name} for {self.menu_item.name}"


class Payment(models.Model):
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="payment_details"
    )
    payment_method = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="PENDING")
    transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.transaction_id} for Order {self.order.order_number}"


class RestaurantSettings(models.Model):
    restaurant_name = models.CharField(max_length=150, default="V Restaurant")
    opening_hours = models.CharField(
        max_length=200,
        default="Mon - Fri: 11:00 AM - 11:00 PM, Sat - Sun: 10:00 AM - Midnight",
    )
    happy_hours = models.CharField(
        max_length=200, default="04:00 PM - 07:00 PM"
    )
    contact_phone = models.CharField(max_length=20, default="+91 7601098423")
    contact_email = models.EmailField(default="vrestaurant@gmail.com")
    address = models.TextField(default="Tiruvuru, NTR District, Andhra Pradesh, India")
    instagram = models.URLField(
        blank=True, null=True, default="https://instagram.com"
    )
    facebook = models.URLField(
        blank=True, null=True, default="https://facebook.com"
    )
    whatsapp_number = models.CharField(max_length=20, default="+917601098423")
    google_maps_url = models.TextField(
        default="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3801.378945618195!2d80.6095033!3d17.1171896!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3a35ab5bcf41d2f7%3A0xe21262eb127c59!2sTiruvuru%2C%20Andhra%20Pradesh!5e0!3m2!1sen!2sin!4v1700000000000"
    )
    description = models.TextField(
        default="An avant-garde gastronomic experience combining modern culinary artistry with real-time restaurant technology."
    )
    logo = models.ImageField(upload_to="settings/", blank=True, null=True)
    banner_image = models.ImageField(
        upload_to="settings/", blank=True, null=True
    )
    theme_color = models.CharField(
        max_length=20,
        default="#FF6B35",
        help_text="Theme color in hex format e.g. #FF6B35",
    )
    footer_copyright = models.CharField(
        max_length=250, default="V Restaurant. All Rights Reserved."
    )
    delivery_charges = models.DecimalField(
        max_digits=6, decimal_places=2, default=50.00
    )
    gst_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.00
    )
    is_open = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Restaurant Settings"

    def __str__(self):
        return self.restaurant_name


class Address(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="saved_addresses"
    )
    address_line = models.TextField()
    city = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_line}, {self.city}"


class FavouriteItem(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="favourites"
    )
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("customer", "menu_item")

    def __str__(self):
        return f"{self.customer.name}'s Favorite: {self.menu_item.name}"


class TableReservation(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
    ]
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reservations",
    )
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    num_guests = models.PositiveIntegerField(default=2)
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    special_requests = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Table for {self.name} on {self.reservation_date} at {self.reservation_time}"


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.CharField(max_length=100, default="Chef V")
    content = models.TextField()
    summary = models.TextField(blank=True)
    image = models.ImageField(upload_to="blog_posts/", blank=True, null=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_image_url(self):
        if self.image:
            return self.image.url
        return (
            self.image_url
            or "https://images.unsplash.com/photo-1546069901-ba9599a7e63c"
        )


class Notification(models.Model):
    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="notifications"
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.customer.name}: {self.title}"
