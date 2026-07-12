from django import forms

from apps.core.models import Category, Coupon, MenuItem, RestaurantSettings


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = [
            "category",
            "name",
            "description",
            "price",
            "image",
            "image_url",
            "is_veg",
            "is_spicy",
            "is_available",
            "rating",
            "is_chef_special",
            "is_today_offer",
            "is_popular",
            "is_recommended",
            "origin",
            "district",
            "state",
            "preparation_time",
            "calories",
            "spice_level",
            "is_today_special",
            "is_new_arrival",
            "is_trending",
        ]
        widgets = {
            "category": forms.Select(
                attrs={
                    "class": "form-select bg-dark border-secondary text-white"
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "placeholder": "Item Name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "rows": 3,
                    "placeholder": "Item Description",
                }
            ),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "step": "0.01",
                }
            ),
            "image": forms.FileInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "image_url": forms.URLInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "placeholder": "https://images.unsplash.com/...",
                }
            ),
            "rating": forms.NumberInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "step": "0.1",
                    "max": "5.0",
                    "min": "0.0",
                }
            ),
            "origin": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "district": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "state": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "preparation_time": forms.NumberInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "min": 1,
                }
            ),
            "calories": forms.NumberInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "min": 0,
                }
            ),
            "spice_level": forms.Select(
                attrs={
                    "class": "form-select bg-dark border-secondary text-white"
                }
            ),
            "is_today_special": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "is_new_arrival": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "is_trending": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "icon", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "placeholder": "e.g. Biryani",
                }
            ),
            "icon": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "placeholder": "e.g. bi-egg-fried",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "rows": 3,
                }
            ),
        }


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            "code",
            "discount_percent",
            "active",
            "valid_from",
            "valid_to",
        ]
        widgets = {
            "code": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "placeholder": "e.g. GOURMET20",
                }
            ),
            "discount_percent": forms.NumberInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "min": 1,
                    "max": 100,
                }
            ),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "valid_from": forms.DateTimeInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "type": "datetime-local",
                }
            ),
            "valid_to": forms.DateTimeInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "type": "datetime-local",
                }
            ),
        }


class RestaurantSettingsForm(forms.ModelForm):
    class Meta:
        model = RestaurantSettings
        fields = [
            "restaurant_name",
            "opening_hours",
            "happy_hours",
            "contact_phone",
            "contact_email",
            "address",
            "instagram",
            "facebook",
            "whatsapp_number",
            "google_maps_url",
            "description",
            "logo",
            "banner_image",
            "theme_color",
            "footer_copyright",
            "delivery_charges",
            "gst_percentage",
            "is_open",
        ]
        widgets = {
            "restaurant_name": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "opening_hours": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "happy_hours": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "contact_phone": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "contact_email": forms.EmailInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "rows": 2,
                }
            ),
            "instagram": forms.URLInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "facebook": forms.URLInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "whatsapp_number": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "google_maps_url": forms.Textarea(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "rows": 2,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "rows": 3,
                }
            ),
            "logo": forms.FileInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "banner_image": forms.FileInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "theme_color": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "placeholder": "#FF6B35",
                }
            ),
            "footer_copyright": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "delivery_charges": forms.NumberInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "step": "0.01",
                }
            ),
            "gst_percentage": forms.NumberInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "step": "0.01",
                }
            ),
            "is_open": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }


class BlogPostForm(forms.ModelForm):
    class Meta:
        from apps.core.models import BlogPost

        model = BlogPost
        fields = [
            "title",
            "author",
            "content",
            "summary",
            "image",
            "image_url",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "placeholder": "Article Title",
                }
            ),
            "author": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "rows": 6,
                }
            ),
            "summary": forms.Textarea(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "rows": 2,
                }
            ),
            "image": forms.FileInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "image_url": forms.URLInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "placeholder": "Optional cover image URL",
                }
            ),
        }


class TableReservationForm(forms.ModelForm):
    class Meta:
        from apps.core.models import TableReservation

        model = TableReservation
        fields = [
            "name",
            "phone",
            "email",
            "num_guests",
            "reservation_date",
            "reservation_time",
            "status",
            "special_requests",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white"
                }
            ),
            "num_guests": forms.NumberInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "min": 1,
                }
            ),
            "reservation_date": forms.DateInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "type": "date",
                }
            ),
            "reservation_time": forms.TimeInput(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "type": "time",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-select bg-dark border-secondary text-white"
                }
            ),
            "special_requests": forms.Textarea(
                attrs={
                    "class": "form-control bg-dark border-secondary text-white",
                    "rows": 2,
                }
            ),
        }
