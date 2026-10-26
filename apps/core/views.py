import json
import uuid
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db.models import Case, Count, Q, Sum, When
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .models import (
    Address,
    Category,
    Coupon,
    Customer,
    FavouriteItem,
    MenuItem,
    Order,
    OrderItem,
    Payment,
    RestaurantSettings,
    Review,
)


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings"] = (
            RestaurantSettings.objects.first()
            or RestaurantSettings.objects.create()
        )
        context["categories"] = Category.objects.all()
        context["chef_specials"] = MenuItem.objects.filter(
            is_chef_special=True, is_available=True
        )[:4]
        context["popular_foods"] = MenuItem.objects.filter(
            is_popular=True, is_available=True
        )[:4]
        context["recommended_foods"] = MenuItem.objects.filter(
            is_recommended=True, is_available=True
        )[:4]
        context["today_offers"] = MenuItem.objects.filter(
            is_today_offer=True, is_available=True
        )[:3]

        # Testimonials mock data
        context["testimonials"] = [
            {
                "name": "Sophia Laurent",
                "role": "Gastronomy Critic",
                "comment": "An absolute masterpiece of tastes and sights. The Glassmorphism interface matches their aesthetic, and the food was celestial.",
                "rating": 5,
            },
            {
                "name": "Marcus Vance",
                "role": "Tech Entrepreneur",
                "comment": "Fast Ordering, real-time tracking, and design elements reminiscent of Stripe. Truly a luxury dining convenience.",
                "rating": 5,
            },
            {
                "name": "Elena Rostova",
                "role": "Regular Patron",
                "comment": "The V Restaurant sets a new standard for dining. Order tracking makes pickup incredibly seamless.",
                "rating": 5,
            },
        ]
        return context


class MenuView(TemplateView):
    template_name = "core/menu.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings"] = (
            RestaurantSettings.objects.first()
            or RestaurantSettings.objects.create()
        )
        context["categories"] = Category.objects.all()
        context["menu_items"] = MenuItem.objects.filter(is_available=True)

        fav_ids = []
        if self.request.user.is_authenticated:
            customer = getattr(self.request.user, "customer", None)
            if customer:
                fav_ids = list(
                    customer.favourites.values_list("menu_item_id", flat=True)
                )
        context["fav_ids"] = fav_ids
        return context


class MenuSearchAPIView(View):
    def get(self, request):
        query = request.GET.get("q", "")
        category_slug = request.GET.get("category", "")
        is_veg = request.GET.get("veg", "false") == "true"
        is_non_veg = request.GET.get("non_veg", "false") == "true"
        meat_type = request.GET.get("meat", "")
        available_only = request.GET.get("available", "false") == "true"
        sort_by = request.GET.get("sort", "")

        spice = request.GET.get("spice_level", "")
        today_special = request.GET.get("today_special", "false") == "true"
        trending = request.GET.get("trending", "false") == "true"
        new_arrival = request.GET.get("new_arrival", "false") == "true"
        max_prep_time = request.GET.get("max_prep_time", "")

        items = MenuItem.objects.all()

        if spice:
            items = items.filter(spice_level=spice)
        if today_special:
            items = items.filter(is_today_special=True)
        if trending:
            items = items.filter(is_trending=True)
        if new_arrival:
            items = items.filter(is_new_arrival=True)
        if max_prep_time:
            try:
                items = items.filter(preparation_time__lte=int(max_prep_time))
            except ValueError:
                pass

        if available_only:
            items = items.filter(is_available=True)

        if query:
            items = items.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(district__icontains=query)
                | Q(origin__icontains=query)
            )

        if category_slug:
            items = items.filter(category__slug=category_slug)

        if is_veg:
            items = items.filter(is_veg=True)

        if is_non_veg:
            items = items.filter(is_veg=False)

        if meat_type:
            items = items.filter(
                Q(name__icontains=meat_type)
                | Q(description__icontains=meat_type)
            )

        if sort_by == "price_asc":
            items = items.order_by("price")
        elif sort_by == "price_desc":
            items = items.order_by("-price")
        elif sort_by == "rating":
            items = items.order_by("-rating")
        elif sort_by == "popular":
            items = items.order_by("-is_popular", "-is_recommended")
        elif sort_by == "alpha":
            items = items.order_by("name")
        else:
            items = items.order_by("-created_at")

        fav_ids = []
        if request.user.is_authenticated:
            customer = getattr(request.user, "customer", None)
            if customer:
                fav_ids = list(
                    customer.favourites.values_list("menu_item_id", flat=True)
                )

        html = render_to_string(
            "core/components/menu_grid.html",
            {"menu_items": items, "request": request, "fav_ids": fav_ids},
        )
        return JsonResponse({"html": html})


class CartSyncView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            cart_items = data.get("cart", [])

            # Recalculate totals
            subtotal = Decimal("0.00")
            items_count = 0
            synced_items = []

            for item in cart_items:
                item_id = item.get("id")
                qty = int(item.get("qty", 1))
                if qty < 1:
                    continue
                try:
                    menu_item = MenuItem.objects.get(
                        id=item_id, is_available=True
                    )
                    item_total = menu_item.price * qty
                    subtotal += item_total
                    items_count += qty
                    synced_items.append(
                        {
                            "id": menu_item.id,
                            "name": menu_item.name,
                            "price": float(menu_item.price),
                            "qty": qty,
                            "total": float(item_total),
                            "image_url": menu_item.get_image_url(),
                            "is_veg": menu_item.is_veg,
                        }
                    )
                except MenuItem.DoesNotExist:
                    continue

            # Dynamic settings
            settings_obj = (
                RestaurantSettings.objects.first()
                or RestaurantSettings.objects.create()
            )
            gst_percent = Decimal(str(settings_obj.gst_percentage)) / Decimal(
                "100.0"
            )
            tax = round(subtotal * gst_percent, 2)

            # Delivery charges
            delivery_charge = Decimal("0.00")
            if subtotal > 0 and subtotal < Decimal("50.00"):
                delivery_charge = Decimal(str(settings_obj.delivery_charges))

            # Discount from session coupon
            discount = Decimal("0.00")
            coupon_code = request.session.get("coupon_code", "")
            coupon_discount_percent = 0
            if coupon_code:
                try:
                    coupon = Coupon.objects.get(code=coupon_code)
                    if coupon.is_valid():
                        coupon_discount_percent = coupon.discount_percent
                        discount = round(
                            subtotal
                            * (
                                Decimal(str(coupon_discount_percent))
                                / Decimal("100.0")
                            ),
                            2,
                        )
                    else:
                        del request.session["coupon_code"]
                except Coupon.DoesNotExist:
                    del request.session["coupon_code"]

            grand_total = max(
                Decimal("0.00"), subtotal + tax + delivery_charge - discount
            )

            # Save cart details to session for server-side checkout validation
            request.session["cart_items"] = synced_items
            request.session["cart_subtotal"] = float(subtotal)
            request.session["cart_tax"] = float(tax)
            request.session["cart_delivery"] = float(delivery_charge)
            request.session["cart_discount"] = float(discount)
            request.session["cart_total"] = float(grand_total)

            return JsonResponse(
                {
                    "success": True,
                    "subtotal": float(subtotal),
                    "tax": float(tax),
                    "delivery_charge": float(delivery_charge),
                    "discount": float(discount),
                    "coupon_code": coupon_code,
                    "coupon_discount_percent": coupon_discount_percent,
                    "grand_total": float(grand_total),
                    "items_count": items_count,
                    "items": synced_items,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": str(e)}, status=400
            )


class CouponApplyView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            code = data.get("code", "").strip().upper()

            coupon = Coupon.objects.filter(code=code).first()
            if not coupon or not coupon.is_valid():
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid or expired coupon code",
                    }
                )

            request.session["coupon_code"] = coupon.code

            # Force cart session updates
            subtotal = request.session.get("cart_subtotal", 0.0)
            discount = round(subtotal * (coupon.discount_percent / 100.0), 2)
            tax = request.session.get("cart_tax", 0.0)
            delivery_charge = request.session.get("cart_delivery", 0.0)

            grand_total = max(
                0.00,
                float(subtotal)
                + float(tax)
                + float(delivery_charge)
                - float(discount),
            )

            request.session["cart_discount"] = float(discount)
            request.session["cart_total"] = grand_total

            return JsonResponse(
                {
                    "success": True,
                    "message": f'Coupon "{coupon.code}" applied successfully!',
                    "discount_percent": coupon.discount_percent,
                    "discount_amount": float(discount),
                    "grand_total": grand_total,
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": str(e)}, status=400
            )


class CheckoutView(LoginRequiredMixin, TemplateView):
    login_url = "core:login"
    redirect_field_name = "next"
    template_name = "core/checkout.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = getattr(self.request.user, "customer", None)
        context["settings"] = (
            RestaurantSettings.objects.first()
            or RestaurantSettings.objects.create()
        )
        context["cart_items"] = self.request.session.get("cart_items", [])
        context["cart_subtotal"] = self.request.session.get(
            "cart_subtotal", 0.0
        )
        context["cart_tax"] = self.request.session.get("cart_tax", 0.0)
        context["cart_delivery"] = self.request.session.get(
            "cart_delivery", 0.0
        )
        context["cart_discount"] = self.request.session.get(
            "cart_discount", 0.0
        )
        context["cart_total"] = self.request.session.get("cart_total", 0.0)
        context["coupon_code"] = self.request.session.get("coupon_code", "")
        context["customer_profile"] = customer
        if customer:
            context["saved_addresses"] = customer.saved_addresses.all()
        return context

    def post(self, request):
        cart_items = request.session.get("cart_items", [])
        if not cart_items:
            return redirect("core:menu")

        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email", "")
        dining_option = request.POST.get("dining_option")
        table_number = request.POST.get("table_number", "")
        address = request.POST.get("address", "")
        payment_method = request.POST.get("payment_method", "CASH")

        # Link to authenticated customer
        customer = getattr(request.user, "customer", None)
        if not customer:
            customer = Customer.objects.create(
                user=request.user,
                name=name or request.user.username,
                phone=phone,
                email=email or request.user.email,
                address=address,
            )
        else:
            if name:
                customer.name = name
            if phone:
                customer.phone = phone
            if email:
                customer.email = email
            if address:
                customer.address = address
            customer.save()

        # Add to saved addresses if it is delivery and not already saved
        if dining_option == "DELIVERY" and address:
            if not customer.saved_addresses.filter(
                address_line=address
            ).exists():
                # Make first address default
                is_default = not customer.saved_addresses.exists()
                Address.objects.create(
                    customer=customer,
                    address_line=address,
                    city=customer.city or "Ramannapalem",
                    is_default=is_default,
                )

        # Pricing calculations
        subtotal = float(request.session.get("cart_subtotal", 0.0))
        tax = float(request.session.get("cart_tax", 0.0))
        delivery_charge = float(request.session.get("cart_delivery", 0.0))
        discount = float(request.session.get("cart_discount", 0.0))
        total_amount = float(request.session.get("cart_total", 0.0))

        coupon = None
        coupon_code = request.session.get("coupon_code")
        if coupon_code:
            coupon = Coupon.objects.filter(code=coupon_code).first()

        # Create Order
        order = Order.objects.create(
            customer=customer,
            customer_name=name,
            customer_phone=phone,
            customer_email=email,
            customer_address=address if dining_option == "DELIVERY" else "",
            table_number=table_number if dining_option == "DINE_IN" else "",
            dining_option=dining_option,
            payment_method=payment_method,
            payment_status="PENDING",
            subtotal=subtotal,
            tax=tax,
            delivery_charge=(
                delivery_charge if dining_option == "DELIVERY" else 0.00
            ),
            discount=discount,
            total_amount=(
                total_amount
                if dining_option == "DELIVERY"
                else (total_amount - delivery_charge)
            ),
            coupon=coupon,
            status="RECEIVED",
        )

        # Create Order Items
        for item in cart_items:
            try:
                menu_item = MenuItem.objects.get(id=item["id"])
                OrderItem.objects.create(
                    order=order,
                    menu_item=menu_item,
                    quantity=item["qty"],
                    price=item["price"],
                )
            except MenuItem.DoesNotExist:
                continue

        # Create Payment
        Payment.objects.create(
            order=order,
            payment_method=payment_method,
            amount=order.total_amount,
            status="PENDING",
            transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
        )

        # Award reward points (e.g., 10% of order total amount)
        try:
            points_earned = int(order.total_amount * Decimal("0.10"))
            customer.reward_points += points_earned
            customer.save()
        except Exception:
            pass

        # Clear session cart details
        if "cart_items" in request.session:
            del request.session["cart_items"]
        if "cart_subtotal" in request.session:
            del request.session["cart_subtotal"]
        if "cart_tax" in request.session:
            del request.session["cart_tax"]
        if "cart_delivery" in request.session:
            del request.session["cart_delivery"]
        if "cart_discount" in request.session:
            del request.session["cart_discount"]
        if "cart_total" in request.session:
            del request.session["cart_total"]
        if "coupon_code" in request.session:
            del request.session["coupon_code"]

        return redirect("core:payment_portal", order_number=order.order_number)


class CheckoutSuccessView(DetailView):
    model = Order
    template_name = "core/checkout_success.html"
    context_object_name = "order"

    def get_object(self, queryset=None):
        return get_object_or_404(
            Order, order_number=self.kwargs.get("order_number")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["settings"] = (
            RestaurantSettings.objects.first()
            or RestaurantSettings.objects.create()
        )
        return context


class OrderTrackingView(DetailView):
    model = Order
    template_name = "core/track.html"
    context_object_name = "order"

    def get_object(self, queryset=None):
        return get_object_or_404(
            Order, order_number=self.kwargs.get("order_number")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context["settings"] = (
            RestaurantSettings.objects.first()
            or RestaurantSettings.objects.create()
        )

        # QR Code url generation using javascript dynamic QRCode on tracking page
        # Map statuses to steps 1-6
        status_steps = {
            "RECEIVED": 1,
            "PREPARING": 2,
            "COOKING": 3,
            "PACKED": 4,
            "READY": 5,
            "OUT_FOR_DELIVERY": 6,
            "DELIVERED": 7,
        }
        context["current_step"] = status_steps.get(order.status, 1)

        # Percentage calculation for progress bar (dividing by 6 gaps between 7 steps)
        context["progress_percentage"] = int(
            ((context["current_step"] - 1) / 6) * 100
        )
        return context


class InvoicePDFView(View):
    def get(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        buffer = BytesIO()

        # Custom 1-page compact design
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        story = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontSize=22,
            textColor=colors.HexColor("#FF6B35"),
            spaceAfter=6,
        )
        subtitle_style = ParagraphStyle(
            "SubTitleStyle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#718096"),
            spaceAfter=15,
        )
        heading_style = ParagraphStyle(
            "HeadStyle",
            parent=styles["Heading3"],
            fontSize=12,
            textColor=colors.HexColor("#1A202C"),
            spaceAfter=4,
        )
        text_style = ParagraphStyle(
            "TextStyle",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#2D3748"),
        )

        # Restaurant Details Header
        rest_settings = (
            RestaurantSettings.objects.first()
            or RestaurantSettings.objects.create()
        )
        story.append(Paragraph(rest_settings.restaurant_name, title_style))
        story.append(
            Paragraph(
                f"{rest_settings.address} | Email: {rest_settings.contact_email} | Tel: {rest_settings.contact_phone}",
                subtitle_style,
            )
        )
        story.append(Spacer(1, 10))

        # Order info Table
        info_data = [
            [
                Paragraph(
                    f"<b>Order Number:</b> {order.order_number}", text_style
                ),
                Paragraph(
                    f"<b>Date:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}",
                    text_style,
                ),
            ],
            [
                Paragraph(
                    f"<b>Customer Name:</b> {order.customer_name}", text_style
                ),
                Paragraph(
                    f"<b>Dining Option:</b> {order.get_dining_option_display()}",
                    text_style,
                ),
            ],
            [
                Paragraph(f"<b>Phone:</b> {order.customer_phone}", text_style),
                Paragraph(
                    f"<b>Payment:</b> {order.get_payment_method_display()} ({order.get_payment_status_display()})",
                    text_style,
                ),
            ],
        ]
        if order.dining_option == "DINE_IN":
            info_data.append(
                [
                    Paragraph(
                        f"<b>Table Number:</b> {order.table_number or 'N/A'}",
                        text_style,
                    ),
                    "",
                ]
            )
        elif order.dining_option == "DELIVERY":
            info_data.append(
                [
                    Paragraph(
                        f"<b>Delivery Address:</b> {order.customer_address or 'N/A'}",
                        text_style,
                    ),
                    "",
                ]
            )

        info_table = Table(info_data, colWidths=[270, 270])
        info_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )

        story.append(info_table)
        story.append(Spacer(1, 15))
        story.append(Paragraph("<b>Order Summary</b>", heading_style))
        story.append(Spacer(1, 5))

        # Order items table
        items_data = [["Item Name", "Price", "Qty", "Total"]]
        for item in order.items.all():
            items_data.append(
                [
                    item.menu_item.name,
                    f"Rs. {item.price}",
                    str(item.quantity),
                    f"Rs. {item.get_total()}",
                ]
            )

        # Add totals
        items_data.append(["", "", "Subtotal:", f"Rs. {order.subtotal}"])
        items_data.append(
            [
                "",
                "",
                f"Tax ({rest_settings.gst_percentage}%):",
                f"Rs. {order.tax}",
            ]
        )
        if order.dining_option == "DELIVERY":
            items_data.append(
                ["", "", "Delivery:", f"Rs. {order.delivery_charge}"]
            )
        if order.discount > 0:
            items_data.append(["", "", "Discount:", f"-Rs. {order.discount}"])
        items_data.append(
            ["", "", "Grand Total:", f"Rs. {order.total_amount}"]
        )

        items_table = Table(items_data, colWidths=[280, 80, 80, 100])
        items_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#F7FAFC"),
                    ),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1A202C")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                    ("TOPPADDING", (0, 0), (-1, 0), 6),
                    (
                        "LINEBELOW",
                        (0, 0),
                        (-1, 0),
                        1,
                        colors.HexColor("#E2E8F0"),
                    ),
                    (
                        "LINEABOVE",
                        (2, -5),
                        (3, -5),
                        1,
                        colors.HexColor("#E2E8F0"),
                    ),
                    (
                        "LINEBELOW",
                        (0, -1),
                        (-1, -1),
                        1.5,
                        colors.HexColor("#FF6B35"),
                    ),
                    ("FONTNAME", (2, -1), (3, -1), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                    ("TOPPADDING", (0, 1), (-1, -1), 4),
                ]
            )
        )

        story.append(items_table)
        story.append(Spacer(1, 30))

        # Thank you note
        thank_style = ParagraphStyle(
            "ThankStyle",
            parent=styles["Normal"],
            fontSize=10,
            alignment=1,  # Center
            textColor=colors.HexColor("#718096"),
        )
        story.append(
            Paragraph(
                f"Thank you for dining with {rest_settings.restaurant_name}. We hope to serve you again soon!",
                thank_style,
            )
        )

        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="Invoice-{order.order_number}.pdf"'
        )
        return response


class PaymentView(DetailView):
    model = Order
    template_name = "core/payment.html"
    context_object_name = "order"

    def get_object(self, queryset=None):
        return get_object_or_404(
            Order, order_number=self.kwargs.get("order_number")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context["settings"] = (
            RestaurantSettings.objects.first()
            or RestaurantSettings.objects.create()
        )

        # upi://pay?pa=vrestaurant@upi&pn=V%20Restaurant&am=...&cu=INR&tn=Food%20Order
        upi_pa = "vrestaurant@upi"
        upi_pn = "V Restaurant"
        upi_tn = f"Food Order {order.order_number}"
        upi_am = str(order.total_amount)
        upi_cu = "INR"

        context["upi_uri"] = (
            f"upi://pay?pa={upi_pa}&pn={upi_pn}&am={upi_am}&cu={upi_cu}&tn={upi_tn}"
        )
        return context


class PaymentConfirmAPIView(View):
    def post(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)
        order.payment_status = "COMPLETED"
        order.save()

        # Also sync Payment table
        try:
            payment = order.payment_details
            payment.status = "COMPLETED"
            payment.save()
        except Exception:
            pass

        return JsonResponse(
            {"success": True, "message": "Payment confirmed successfully"}
        )


class ContactView(View):
    def get(self, request):
        settings_obj = (
            RestaurantSettings.objects.first()
            or RestaurantSettings.objects.create()
        )
        return render(request, "core/contact.html", {"settings": settings_obj})

    def post(self, request):
        # AJAX form handler
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")
        # We simulate email transmission and save/confirm
        return JsonResponse(
            {
                "success": True,
                "message": "Your feedback has been delivered securely. Thank you!",
            }
        )


class NewsletterSubscribeView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get("email", "").strip()
            if not email:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Email address cannot be empty.",
                    }
                )
            # Mock newsletter save
            return JsonResponse(
                {
                    "success": True,
                    "message": "Subscribed successfully to our fine-dining newsletter!",
                }
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": str(e)}, status=400
            )


def custom_404_view(request, exception):
    return render(request, "core/404.html", status=404)


def custom_500_view(request):
    return render(request, "core/500.html", status=500)


class UnifiedLoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return redirect("dashboard:home")
            return redirect("core:customer_dashboard")
        return render(request, "core/login.html")

    def post(self, request):
        login_type = request.POST.get("login_type")
        username_or_phone = request.POST.get("username", "").strip()
        password = request.POST.get("password")
        next_url = request.POST.get("next", "")

        # Standard Django authentication
        user = None
        if "@" in username_or_phone:
            # Email lookup
            try:
                user_obj = User.objects.get(email=username_or_phone)
                user = authenticate(
                    request, username=user_obj.username, password=password
                )
            except User.DoesNotExist:
                pass
        else:
            # Username lookup
            user = authenticate(
                request, username=username_or_phone, password=password
            )

            # Mobile lookup for customer
            if not user:
                try:
                    customer = Customer.objects.get(phone=username_or_phone)
                    if customer.user:
                        user = authenticate(
                            request,
                            username=customer.user.username,
                            password=password,
                        )
                except Customer.DoesNotExist:
                    pass

        if user is not None:
            if login_type == "admin" and not (
                user.is_staff or user.is_superuser
            ):
                messages.error(
                    request,
                    "Access denied. You do not have staff/admin permissions.",
                )
                return render(request, "core/login.html")

            if login_type == "customer" and (
                user.is_staff or user.is_superuser
            ):
                messages.error(
                    request, "Please use the Staff/Admin login portal."
                )
                return render(request, "core/login.html")

            if not user.is_active:
                messages.error(
                    request,
                    "This account is inactive. Please contact support.",
                )
                return render(request, "core/login.html")

            auth_login(request, user)

            # Sync session cart if items are saved in user context (optional)
            if next_url:
                return redirect(next_url)

            if user.is_staff or user.is_superuser:
                return redirect("dashboard:home")
            return redirect("core:customer_dashboard")
        else:
            messages.error(
                request, "Invalid username/email/mobile or password."
            )
            return render(request, "core/login.html")


class CustomerLogoutView(View):
    def post(self, request):
        auth_logout(request)
        return redirect("core:home")


class CustomerRegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("core:customer_dashboard")
        return render(request, "core/register.html")

    def post(self, request):
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        form_data = {
            "name": name,
            "phone": phone,
            "email": email,
        }

        # Validation
        if not (name and phone and email and password and confirm_password):
            messages.error(request, "All fields are required.")
            return render(
                request, "core/register.html", {"form_data": form_data}
            )

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(
                request, "core/register.html", {"form_data": form_data}
            )

        if (
            User.objects.filter(username=email).exists()
            or User.objects.filter(email=email).exists()
        ):
            messages.error(request, "A user with this email already exists.")
            return render(
                request, "core/register.html", {"form_data": form_data}
            )

        if Customer.objects.filter(phone=phone).exists():
            messages.error(
                request, "A customer with this mobile number already exists."
            )
            return render(
                request, "core/register.html", {"form_data": form_data}
            )

        # Create active User and Customer directly
        user = User.objects.create_user(
            username=email, email=email, password=password, is_active=True
        )

        Customer.objects.create(
            user=user,
            name=name,
            phone=phone,
            email=email,
            is_mobile_verified=True,
            is_email_verified=True,
        )

        messages.success(
            request,
            "Registration successful! Please log in with your credentials.",
        )
        return redirect("core:login")


class ForgotPasswordView(View):
    def get(self, request):
        return render(request, "core/forgot_password.html")

    def post(self, request):
        email = request.POST.get("email", "").strip()
        user = User.objects.filter(email=email).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = request.build_absolute_uri(
                redirect("core:reset_password", uidb64=uid, token=token).url
            )

            subject = "Reset Your V Restaurant Password"
            body = f"Hello,\n\nPlease click the link below to reset your V Restaurant password:\n{reset_link}\n\nIf you did not request this, please ignore this email."
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email])

            # QoL message
            messages.success(
                request,
                f"[DEBUG] Password reset link sent! Click to reset: {reset_link}",
            )
            messages.success(
                request,
                "A password reset link has been sent to your email address.",
            )
        else:
            messages.error(request, "No account matches this email address.")

        return render(request, "core/forgot_password.html")


class ResetPasswordView(View):
    def get(self, request, uidb64, token):
        return render(request, "core/reset_password.html")

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(
            user, token
        ):
            password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")

            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, "core/reset_password.html")

            user.set_password(password)
            user.save()
            messages.success(
                request, "Password has been reset successfully. Please log in."
            )
            return redirect("core:login")
        else:
            messages.error(
                request, "This password reset link is invalid or has expired."
            )
            return redirect("core:login")


class CustomerDashboardView(LoginRequiredMixin, TemplateView):
    login_url = "core:login"
    template_name = "core/customer_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = get_object_or_404(Customer, user=self.request.user)

        # Calculate stats
        orders = Order.objects.filter(customer=customer).order_by(
            "-created_at"
        )
        total_orders = orders.count()
        completed_orders = orders.filter(status="DELIVERED").count()
        pending_orders = total_orders - completed_orders

        # Favorite count
        favorites = customer.favourites.all()

        # Most ordered item
        most_ordered_item = (
            OrderItem.objects.filter(order__customer=customer)
            .values(
                "menu_item",
                "menu_item__name",
                "menu_item__price",
                "menu_item__image",
                "menu_item__image_url",
            )
            .annotate(total_qty=Sum("quantity"))
            .order_by("-total_qty")
            .first()
        )

        # Parse it nicely
        most_ordered_item_obj = None
        if most_ordered_item:
            try:
                menu_item = MenuItem.objects.get(
                    id=most_ordered_item["menu_item"]
                )
                most_ordered_item_obj = {
                    "menu_item": menu_item,
                    "total_qty": most_ordered_item["total_qty"],
                }
            except MenuItem.DoesNotExist:
                pass

        # Active order
        active_order = (
            Order.objects.filter(customer=customer)
            .exclude(status="DELIVERED")
            .order_by("-created_at")
            .first()
        )

        # Available coupons
        coupons = Coupon.objects.filter(
            active=True, valid_to__gte=timezone.now()
        )

        # Total amount spent
        total_spent = (
            orders.filter(payment_status="PAID").aggregate(
                total=Sum("total_amount")
            )["total"]
            or 0.00
        )

        # AI Recommendations based on top ordered categories
        fav_categories = (
            OrderItem.objects.filter(order__customer=customer)
            .values("menu_item__category")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        recommended_dishes = []
        if fav_categories:
            top_cat_id = fav_categories[0]["menu_item__category"]
            recommended_dishes = MenuItem.objects.filter(
                category_id=top_cat_id, is_available=True
            )[:4]

        if not recommended_dishes:
            recommended_dishes = MenuItem.objects.filter(
                is_chef_special=True, is_available=True
            )[:4]

        # Recently viewed items (from session)
        recently_viewed_ids = self.request.session.get("recently_viewed", [])
        recently_viewed_items = []
        if recently_viewed_ids:
            preserved_order = Case(
                *[
                    When(pk=pk, then=pos)
                    for pos, pk in enumerate(recently_viewed_ids)
                ]
            )
            recently_viewed_items = MenuItem.objects.filter(
                id__in=recently_viewed_ids
            ).order_by(preserved_order)

        # Customer Notifications
        notifications = customer.notifications.all().order_by("-created_at")[
            :10
        ]

        # Customer Reservations
        reservations = customer.reservations.all().order_by(
            "-reservation_date", "-reservation_time"
        )

        context["customer"] = customer
        context["orders"] = orders
        context["favorites"] = favorites
        context["addresses"] = customer.saved_addresses.all()
        context["coupons"] = coupons
        context["active_order"] = active_order
        context["stats"] = {
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "pending_orders": pending_orders,
            "most_ordered_item": most_ordered_item_obj,
            "total_spent": total_spent,
        }
        context["ai_recommendations"] = recommended_dishes
        context["recently_viewed"] = recently_viewed_items
        context["notifications"] = notifications
        context["reservations"] = reservations
        return context

    def post(self, request):
        customer = get_object_or_404(Customer, user=request.user)
        action = request.POST.get("action")

        if action == "add_address":
            address_line = request.POST.get("address_line")
            city = request.POST.get("city")
            is_default = request.POST.get("is_default") == "on"

            if is_default:
                # Set all other default addresses to False
                customer.saved_addresses.filter(is_default=True).update(
                    is_default=False
                )

            Address.objects.create(
                customer=customer,
                address_line=address_line,
                city=city,
                is_default=is_default or not customer.saved_addresses.exists(),
            )
            messages.success(request, "Address added successfully.")

        elif action == "delete_address":
            address_id = request.POST.get("address_id")
            customer.saved_addresses.filter(id=address_id).delete()
            messages.success(request, "Address deleted successfully.")

        elif action == "set_default_address":
            address_id = request.POST.get("address_id")
            customer.saved_addresses.filter(is_default=True).update(
                is_default=False
            )
            customer.saved_addresses.filter(id=address_id).update(
                is_default=True
            )
            messages.success(request, "Default address updated.")

        elif action == "remove_favorite":
            fav_id = request.POST.get("favorite_id")
            customer.favourites.filter(id=fav_id).delete()
            messages.success(request, "Item removed from favorites.")

        elif action == "update_profile":
            name = request.POST.get("name")
            phone = request.POST.get("phone")
            email = request.POST.get("email")
            city = request.POST.get("city")
            address = request.POST.get("address")
            photo = request.FILES.get("profile_photo")

            # Update User email
            user = request.user
            user.email = email
            user.save()

            # Update Customer
            customer.name = name
            customer.phone = phone
            customer.email = email
            customer.city = city
            customer.address = address
            if photo:
                customer.profile_photo = photo
            customer.save()
            messages.success(request, "Profile updated successfully.")

        elif action == "update_password":
            old_password = request.POST.get("old_password")
            new_password = request.POST.get("new_password")

            user = request.user
            if user.check_password(old_password):
                user.set_password(new_password)
                user.save()
                auth_login(request, user)  # keep logged in
                messages.success(request, "Password changed successfully.")
            else:
                messages.error(request, "Incorrect current password.")

        return redirect("core:customer_dashboard")


class ReorderView(LoginRequiredMixin, View):
    def get(self, request, order_number):
        customer = get_object_or_404(Customer, user=request.user)
        order = get_object_or_404(
            Order, order_number=order_number, customer=customer
        )

        items_list = []
        for item in order.items.all():
            items_list.append(
                {
                    "id": item.menu_item.id,
                    "name": item.menu_item.name,
                    "price": float(item.price),
                    "qty": item.quantity,
                    "total": float(item.get_total()),
                    "image_url": item.menu_item.get_image_url(),
                    "is_veg": item.menu_item.is_veg,
                }
            )

        return JsonResponse({"success": True, "items": items_list})


class ToggleFavoriteView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        customer = get_object_or_404(Customer, user=request.user)
        menu_item = get_object_or_404(MenuItem, id=item_id)

        fav, created = FavouriteItem.objects.get_or_create(
            customer=customer, menu_item=menu_item
        )
        if not created:
            fav.delete()
            return JsonResponse(
                {
                    "success": True,
                    "favorited": False,
                    "message": f'Removed "{menu_item.name}" from favorites.',
                }
            )

        return JsonResponse(
            {
                "success": True,
                "favorited": True,
                "message": f'Saved "{menu_item.name}" to favorites.',
            }
        )


class MenuItemDetailView(View):
    def get(self, request, pk):
        item = get_object_or_404(MenuItem, pk=pk)

        # Track recently viewed in session
        recently_viewed = request.session.get("recently_viewed", [])
        if item.id in recently_viewed:
            recently_viewed.remove(item.id)
        recently_viewed.insert(0, item.id)
        request.session["recently_viewed"] = recently_viewed[:6]

        is_favorite = False
        if request.user.is_authenticated:
            customer = getattr(request.user, "customer", None)
            if customer:
                is_favorite = customer.favourites.filter(
                    menu_item=item
                ).exists()

        # AI Suggestions: similar and frequently ordered together
        similar_dishes = MenuItem.objects.filter(
            category=item.category, is_available=True
        ).exclude(id=item.id)[:4]
        frequent_dishes = MenuItem.objects.filter(
            is_popular=True, is_available=True
        ).exclude(id=item.id)[:4]

        html = render_to_string(
            "core/menu_item_detail.html",
            {
                "item": item,
                "is_favorite": is_favorite,
                "similar_dishes": similar_dishes,
                "frequent_dishes": frequent_dishes,
                "request": request,
            },
        )
        return HttpResponse(html)


class SubmitReviewView(LoginRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(MenuItem, pk=pk)
        customer = get_object_or_404(Customer, user=request.user)

        rating = int(request.POST.get("rating", 5))
        comment = request.POST.get("comment", "").strip()

        if comment:
            Review.objects.create(
                menu_item=item,
                customer_name=customer.name,
                rating=rating,
                comment=comment,
            )
            # Recompute menu item average rating
            reviews = item.reviews.all()
            avg_rating = (
                reviews.aggregate(avg=Sum("rating"))["avg"] / reviews.count()
            )
            item.rating = round(avg_rating, 1)
            item.save()

            return JsonResponse(
                {"success": True, "message": "Review submitted successfully!"}
            )
        return JsonResponse(
            {"success": False, "message": "Comment field cannot be empty."}
        )


class ReserveTableView(View):
    def get(self, request):
        return render(request, "core/reserve.html")

    def post(self, request):
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        email = request.POST.get("email", "").strip()
        num_guests = int(request.POST.get("num_guests", 2))
        res_date = request.POST.get("reservation_date")
        res_time = request.POST.get("reservation_time")
        requests = request.POST.get("special_requests", "").strip()

        customer = None
        if request.user.is_authenticated:
            customer = getattr(request.user, "customer", None)

        if not (name and phone and email and res_date and res_time):
            messages.error(request, "All fields marked with * are required.")
            return render(request, "core/reserve.html")

        from .models import TableReservation

        TableReservation.objects.create(
            customer=customer,
            name=name,
            phone=phone,
            email=email,
            num_guests=num_guests,
            reservation_date=res_date,
            reservation_time=res_time,
            special_requests=requests,
        )
        messages.success(
            request,
            "Table reserved successfully! We will contact you shortly to confirm.",
        )
        return redirect("core:home")


class BlogListView(View):
    def get(self, request):
        from .models import BlogPost

        posts = BlogPost.objects.all().order_by("-created_at")
        return render(request, "core/blog_list.html", {"posts": posts})


class BlogDetailView(View):
    def get(self, request, slug):
        from .models import BlogPost

        post = get_object_or_404(BlogPost, slug=slug)
        return render(request, "core/blog_detail.html", {"post": post})


class MarkNotificationReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        customer = get_object_or_404(Customer, user=request.user)
        from .models import Notification

        notification = get_object_or_404(
            Notification, pk=pk, customer=customer
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({"success": True})


class RobotsTxtView(View):
    def get(self, request):
        content = (
            "User-agent: *\nDisallow: /checkout/\nDisallow: /customer/\nDisallow: /dashboard/\nSitemap: "
            + request.build_absolute_uri("/sitemap.xml")
        )
        return HttpResponse(content, content_type="text/plain")


class SitemapXmlView(View):
    def get(self, request):
        from django.urls import reverse

        from .models import BlogPost

        urls = [
            request.build_absolute_uri("/"),
            request.build_absolute_uri("/menu/"),
            request.build_absolute_uri("/contact/"),
            request.build_absolute_uri("/reserve/"),
            request.build_absolute_uri("/blog/"),
        ]
        for post in BlogPost.objects.all():
            urls.append(
                request.build_absolute_uri(
                    reverse("core:blog_detail", args=[post.slug])
                )
            )

        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        for url in urls:
            xml_content += f"  <url>\n    <loc>{url}</loc>\n    <changefreq>daily</changefreq>\n  </url>\n"
        xml_content += "</urlset>"
        return HttpResponse(xml_content, content_type="application/xml")
