from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.models import (
    Category,
    Coupon,
    Customer,
    MenuItem,
    Order,
    RestaurantSettings,
)


class GourmetSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name="Appetizers", slug="appetizers"
        )
        self.menu_item = MenuItem.objects.create(
            name="Bruschetta",
            slug="bruschetta",
            category=self.category,
            price=10.00,
            is_available=True,
        )
        self.coupon = Coupon.objects.create(
            code="SAVE10",
            discount_percent=10,
            active=True,
            valid_from=timezone.now() - timezone.timedelta(days=1),
            valid_to=timezone.now() + timezone.timedelta(days=1),
        )
        self.settings = RestaurantSettings.objects.create(
            restaurant_name="V Restaurant",
            delivery_charges=5.00,
            gst_percentage=5.00,
        )

    def test_coupon_validity(self):
        self.assertTrue(self.coupon.is_valid())

        # Test expired coupon
        expired_coupon = Coupon.objects.create(
            code="EXPIRED",
            discount_percent=20,
            active=True,
            valid_from=timezone.now() - timezone.timedelta(days=2),
            valid_to=timezone.now() - timezone.timedelta(days=1),
        )
        self.assertFalse(expired_coupon.is_valid())

    def test_ajax_menu_search(self):
        url = reverse("core:menu_search")
        response = self.client.get(url, {"q": "Bruschetta"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bruschetta")

    def test_cart_session_sync(self):
        url = reverse("core:cart_sync")
        payload = {"cart": [{"id": self.menu_item.id, "qty": 2}]}
        response = self.client.post(
            url, data=payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["subtotal"], 20.00)
        self.assertEqual(json_data["tax"], 1.00)  # 5% of 20
        self.assertEqual(
            json_data["grand_total"], 26.00
        )  # 20 + 1 + 5 (delivery)

    def test_coupon_apply_api(self):
        # Sync cart first
        self.client.post(
            reverse("core:cart_sync"),
            data={"cart": [{"id": self.menu_item.id, "qty": 2}]},
            content_type="application/json",
        )

        # Apply coupon
        url = reverse("core:coupon_apply")
        response = self.client.post(
            url, data={"code": "SAVE10"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        json_data = response.json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["discount_amount"], 2.00)  # 10% of 20
        self.assertEqual(
            json_data["grand_total"], 24.00
        )  # 20 + 1 + 5 (delivery) - 2 (discount)

    def test_pdf_invoice_download(self):
        customer = Customer.objects.create(name="Alice", phone="9876543210")
        order = Order.objects.create(
            customer=customer,
            customer_name="Alice",
            customer_phone="9876543210",
            subtotal=10.00,
            tax=0.50,
            delivery_charge=0.00,
            discount=0.00,
            total_amount=10.50,
            dining_option="DINE_IN",
            status="RECEIVED",
        )
        url = reverse("core:order_invoice", args=[order.order_number])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_customer_registration_and_dual_login(self):
        # 1. Register a new customer
        url = reverse("core:register")
        payload = {
            "name": "Gourmet Tester",
            "phone": "+918888888888",
            "email": "gourmet_tester@gmail.com",
            "password": "testpassword123",
            "confirm_password": "testpassword123",
        }
        response = self.client.post(url, data=payload)

        # Verify it redirects directly to the login page
        self.assertRedirects(response, reverse("core:login"))

        # Verify User and Customer profiles were created
        from django.contrib.auth.models import User

        self.assertTrue(
            User.objects.filter(email="gourmet_tester@gmail.com").exists()
        )
        self.assertTrue(
            Customer.objects.filter(phone="+918888888888").exists()
        )

        # 2. Login using Email
        login_url = reverse("core:login")
        login_payload_email = {
            "login_type": "customer",
            "username": "gourmet_tester@gmail.com",
            "password": "testpassword123",
        }
        response = self.client.post(login_url, data=login_payload_email)
        self.assertRedirects(response, reverse("core:customer_dashboard"))
        self.client.post(reverse("core:logout"))

        # 3. Login using Mobile
        login_payload_phone = {
            "login_type": "customer",
            "username": "+918888888888",
            "password": "testpassword123",
        }
        response = self.client.post(login_url, data=login_payload_phone)
        self.assertRedirects(response, reverse("core:customer_dashboard"))

    def test_new_pages(self):
        from apps.core.models import BlogPost

        BlogPost.objects.create(
            title="Test Post",
            content="Some test content",
            summary="Summary text",
        )

        # Test Blog List Page template rendering
        response = self.client.get(reverse("core:blog_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Post")

        # Test Blog Detail Page template rendering
        response = self.client.get(
            reverse("core:blog_detail", args=["test-post"])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Some test content")

        # Test Reserve Table Page template rendering
        response = self.client.get(reverse("core:reserve"))
        self.assertEqual(response.status_code, 200)
