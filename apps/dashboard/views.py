from .forms import BlogPostForm, TableReservationForm
from apps.core.models import BlogPost, TableReservation
import csv
import json
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.core.models import (
    Category,
    Coupon,
    Customer,
    MenuItem,
    Order,
    OrderItem,
    Payment,
    RestaurantSettings,
    Review,
)

from .forms import (
    CategoryForm,
    CouponForm,
    MenuItemForm,
    RestaurantSettingsForm,
)


class AdminStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "dashboard:login"
    redirect_field_name = "next"

    def test_func(self):
        return self.request.user.is_active and (
            self.request.user.is_staff or self.request.user.is_superuser
        )


class AdminLoginView(LoginView):
    template_name = "dashboard/login.html"

    def get_success_url(self):
        return self.request.GET.get("next") or reverse_lazy("dashboard:home")


class AdminLogoutView(LogoutView):
    next_page = reverse_lazy("dashboard:login")


class AdminHomeView(AdminStaffRequiredMixin, TemplateView):
    template_name = "dashboard/admin_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Stats summary
        context["items_count"] = MenuItem.objects.count()
        context["categories_count"] = Category.objects.count()
        context["orders_count"] = Order.objects.count()
        context["customer_count"] = Customer.objects.count()

        total_rev = Order.objects.filter(payment_status="COMPLETED").aggregate(
            total=Sum("total_amount")
        )["total"]
        context["total_revenue"] = float(total_rev or 0.0)

        # Today's stats
        today_rev = Order.objects.filter(
            created_at__date=today, payment_status="COMPLETED"
        ).aggregate(total=Sum("total_amount"))["total"]
        context["today_revenue"] = float(today_rev or 0.0)
        context["today_orders_count"] = Order.objects.filter(
            created_at__date=today
        ).count()

        # Popular Items
        popular_items = (
            OrderItem.objects.values("menu_item__name", "menu_item__price")
            .annotate(total_qty=Sum("quantity"))
            .order_by("-total_qty")[:5]
        )
        context["popular_items"] = list(popular_items)

        # Weekly & Monthly revenue
        weekly_rev = Order.objects.filter(
            created_at__date__gte=today - timedelta(days=7),
            payment_status="COMPLETED",
        ).aggregate(total=Sum("total_amount"))["total"]
        context["weekly_revenue"] = float(weekly_rev or 0.0)

        monthly_rev = Order.objects.filter(
            created_at__date__gte=today - timedelta(days=30),
            payment_status="COMPLETED",
        ).aggregate(total=Sum("total_amount"))["total"]
        context["monthly_revenue"] = float(monthly_rev or 0.0)

        # Peak ordering hour
        peak_hour_data = (
            Order.objects.extra(select={"hour": "strftime('%H', created_at)"})
            .values("hour")
            .annotate(count=Count("id"))
            .order_by("-count")
            .first()
        )
        peak_hour = "N/A"
        if peak_hour_data:
            try:
                hour_val = int(peak_hour_data["hour"])
                am_pm = "AM" if hour_val < 12 else "PM"
                display_hour = hour_val % 12
                if display_hour == 0:
                    display_hour = 12
                peak_hour = f"{display_hour} {am_pm}"
            except (ValueError, TypeError):
                pass
        context["peak_ordering_hour"] = peak_hour

        # Pending Reservations count
        from apps.core.models import TableReservation

        context["pending_reservations"] = TableReservation.objects.filter(
            status="PENDING"
        ).count()

        # Order statuses counts
        context["received_orders"] = Order.objects.filter(
            status="RECEIVED"
        ).count()
        context["preparing_orders"] = Order.objects.filter(
            status__in=["PREPARING", "COOKING"]
        ).count()
        context["ready_orders"] = Order.objects.filter(status="READY").count()
        context["completed_orders"] = Order.objects.filter(
            status="DELIVERED"
        ).count()

        # Recent orders
        context["recent_orders"] = Order.objects.all().order_by("-created_at")[
            :8
        ]

        # Charts helper - 7 Days Revenue
        end_date = today
        start_date = today - timedelta(days=6)

        revenue_by_day = (
            Order.objects.filter(
                created_at__date__range=[start_date, end_date],
                status="DELIVERED",
            )
            .values("created_at__date")
            .annotate(revenue=Sum("total_amount"))
            .order_by("created_at__date")
        )

        chart_labels = []
        chart_data = []

        # Build consecutive list of 7 days
        day_map = {
            item["created_at__date"]: float(item["revenue"] or 0.0)
            for item in revenue_by_day
        }
        for i in range(7):
            d = start_date + timedelta(days=i)
            chart_labels.append(d.strftime("%b %d"))
            chart_data.append(day_map.get(d, 0.0))

        context["chart_labels"] = json.dumps(chart_labels)
        context["chart_data"] = json.dumps(chart_data)

        # Category breakdown
        category_breakdown = MenuItem.objects.values(
            "category__name"
        ).annotate(count=Count("id"))
        cat_labels = [item["category__name"] for item in category_breakdown]
        cat_data = [item["count"] for item in category_breakdown]

        context["cat_labels"] = json.dumps(cat_labels)
        context["cat_data"] = json.dumps(cat_data)

        return context


class AdminMenuListView(AdminStaffRequiredMixin, ListView):
    model = MenuItem
    template_name = "dashboard/menu_list.html"
    context_object_name = "menu_items"
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q")
        category_id = self.request.GET.get("category")

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        return context


class AdminMenuCreateView(AdminStaffRequiredMixin, CreateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = "dashboard/menu_form.html"
    success_url = reverse_lazy("dashboard:menu_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Menu Item"
        return context


class AdminMenuUpdateView(AdminStaffRequiredMixin, UpdateView):
    model = MenuItem
    form_class = MenuItemForm
    template_name = "dashboard/menu_form.html"
    success_url = reverse_lazy("dashboard:menu_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Menu Item"
        return context


class AdminMenuDeleteView(AdminStaffRequiredMixin, DeleteView):
    model = MenuItem
    template_name = "dashboard/menu_confirm_delete.html"
    success_url = reverse_lazy("dashboard:menu_list")


class OrderCSVExportView(AdminStaffRequiredMixin, View):
    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="Orders-Export-{timezone.now().strftime("%Y-%m-%d")}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(
            [
                "Order Number",
                "Customer Name",
                "Phone",
                "Dining Option",
                "Status",
                "Subtotal",
                "Tax",
                "Discount",
                "Total Amount",
                "Payment Method",
                "Payment Status",
                "Created At",
            ]
        )

        orders = Order.objects.all().order_by("-created_at")
        for order in orders:
            writer.writerow(
                [
                    order.order_number,
                    order.customer_name,
                    order.customer_phone,
                    order.get_dining_option_display(),
                    order.get_status_display(),
                    order.subtotal,
                    order.tax,
                    order.discount,
                    order.total_amount,
                    order.get_payment_method_display(),
                    order.get_payment_status_display(),
                    order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )

        return response


class AdminOrderListView(AdminStaffRequiredMixin, ListView):
    model = Order
    template_name = "dashboard/order_list.html"
    context_object_name = "orders"
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q")
        status = self.request.GET.get("status")

        if query:
            queryset = queryset.filter(
                Q(order_number__icontains=query)
                | Q(customer_name__icontains=query)
                | Q(customer_phone__icontains=query)
            )
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Order.STATUS_CHOICES
        return context


class AdminOrderUpdateView(AdminStaffRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        status = request.POST.get("status")
        payment_status = request.POST.get("payment_status")

        if status:
            order.status = status
        if payment_status:
            order.payment_status = payment_status
        order.save()

        # Sync Payment model
        try:
            payment = order.payment_details
            if payment_status:
                payment.status = payment_status
                payment.save()
        except Exception:
            pass

        return redirect("dashboard:order_list")


class AdminCategoryListView(AdminStaffRequiredMixin, ListView):
    model = Category
    template_name = "dashboard/category_list.html"
    context_object_name = "categories"


class AdminCategoryCreateView(AdminStaffRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = "dashboard/category_form.html"
    success_url = reverse_lazy("dashboard:category_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Category"
        return context


class AdminCategoryUpdateView(AdminStaffRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = "dashboard/category_form.html"
    success_url = reverse_lazy("dashboard:category_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Category"
        return context


class AdminCategoryDeleteView(AdminStaffRequiredMixin, DeleteView):
    model = Category
    template_name = "dashboard/category_confirm_delete.html"
    success_url = reverse_lazy("dashboard:category_list")


class AdminCouponListView(AdminStaffRequiredMixin, ListView):
    model = Coupon
    template_name = "dashboard/coupon_list.html"
    context_object_name = "coupons"


class AdminCouponCreateView(AdminStaffRequiredMixin, CreateView):
    model = Coupon
    form_class = CouponForm
    template_name = "dashboard/coupon_form.html"
    success_url = reverse_lazy("dashboard:coupon_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Create Coupon"
        return context


class AdminCouponUpdateView(AdminStaffRequiredMixin, UpdateView):
    model = Coupon
    form_class = CouponForm
    template_name = "dashboard/coupon_form.html"
    success_url = reverse_lazy("dashboard:coupon_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Coupon"
        return context


class AdminCouponDeleteView(AdminStaffRequiredMixin, DeleteView):
    model = Coupon
    template_name = "dashboard/coupon_confirm_delete.html"
    success_url = reverse_lazy("dashboard:coupon_list")


class AdminCustomerListView(AdminStaffRequiredMixin, ListView):
    model = Customer
    template_name = "dashboard/customer_list.html"
    context_object_name = "customers"
    paginate_by = 15


class AdminPaymentListView(AdminStaffRequiredMixin, ListView):
    model = Payment
    template_name = "dashboard/payment_list.html"
    context_object_name = "payments"
    paginate_by = 15


class AdminReviewListView(AdminStaffRequiredMixin, ListView):
    model = Review
    template_name = "dashboard/review_list.html"
    context_object_name = "reviews"
    paginate_by = 15


class AdminReviewDeleteView(AdminStaffRequiredMixin, DeleteView):
    model = Review
    template_name = "dashboard/review_confirm_delete.html"
    success_url = reverse_lazy("dashboard:review_list")


class AdminSettingsUpdateView(AdminStaffRequiredMixin, UpdateView):
    model = RestaurantSettings
    form_class = RestaurantSettingsForm
    template_name = "dashboard/settings_form.html"
    success_url = reverse_lazy("dashboard:home")

    def get_object(self, queryset=None):
        return (
            RestaurantSettings.objects.first()
            or RestaurantSettings.objects.create()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Restaurant Settings"
        return context


class AdminReservationListView(AdminStaffRequiredMixin, ListView):
    model = TableReservation
    template_name = "dashboard/reservation_list.html"
    context_object_name = "reservations"
    paginate_by = 15
    ordering = ["-reservation_date", "-reservation_time"]


class AdminReservationUpdateView(AdminStaffRequiredMixin, UpdateView):
    model = TableReservation
    form_class = TableReservationForm
    template_name = "dashboard/reservation_form.html"
    success_url = reverse_lazy("dashboard:reservation_list")


class AdminBlogListView(AdminStaffRequiredMixin, ListView):
    model = BlogPost
    template_name = "dashboard/blog_list.html"
    context_object_name = "blogs"
    paginate_by = 10
    ordering = ["-created_at"]


class AdminBlogCreateView(AdminStaffRequiredMixin, CreateView):
    model = BlogPost
    form_class = BlogPostForm
    template_name = "dashboard/blog_form.html"
    success_url = reverse_lazy("dashboard:blog_list")


class AdminBlogUpdateView(AdminStaffRequiredMixin, UpdateView):
    model = BlogPost
    form_class = BlogPostForm
    template_name = "dashboard/blog_form.html"
    success_url = reverse_lazy("dashboard:blog_list")


class AdminBlogDeleteView(AdminStaffRequiredMixin, DeleteView):
    model = BlogPost
    template_name = "dashboard/blog_confirm_delete.html"
    success_url = reverse_lazy("dashboard:blog_list")
