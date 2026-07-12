from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from django.db.models import Sum

from apps.core.models import MenuItem, Order, OrderItem


class KitchenAdminRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        # Determine if it's an API route or page load
        is_api = request.path.startswith("/kitchen/api/") or "api" in request.resolver_match.view_name
        
        # 1. Check if user is authenticated
        if not request.user.is_authenticated:
            if is_api:
                return JsonResponse({"success": False, "error": "Access denied. Authentication required."}, status=403)
            login_url = reverse("dashboard:login")
            return redirect(f"{login_url}?next={request.path}")

        # 2. Check if user is staff, superuser, or has kitchen permission
        has_permission = (
            request.user.is_staff or 
            request.user.is_superuser or 
            request.user.has_perm("core.can_access_kitchen") or
            request.user.has_perm("kitchen.view_kitchen") or
            request.user.groups.filter(name="Kitchen").exists()
        )
        
        if not has_permission:
            if is_api:
                return JsonResponse({"success": False, "error": "Kitchen Live is restricted to administrators only."}, status=403)
            
            messages.error(request, "Kitchen Live is restricted to administrators only.")
            referer = request.META.get('HTTP_REFERER')
            if referer:
                return redirect(referer)
            return redirect('core:home')
            
        return super().dispatch(request, *args, **kwargs)


class KitchenDashboardView(KitchenAdminRequiredMixin, TemplateView):
    template_name = "kitchen/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Get active orders
        active_orders = Order.objects.exclude(status="DELIVERED").order_by(
            "priority", "created_at"
        )

        # Split orders for dashboard display columns
        context["orders_received"] = active_orders.filter(status="RECEIVED")
        context["orders_preparing"] = active_orders.filter(
            status__in=["PREPARING", "COOKING"]
        )
        context["orders_packing_ready"] = active_orders.filter(
            status__in=["PACKING", "READY"]
        )

        # Stats
        context["today_orders"] = Order.objects.filter(
            created_at__date=today
        ).count()
        context["pending_orders"] = active_orders.count()
        context["completed_orders"] = Order.objects.filter(
            created_at__date=today, status="DELIVERED"
        ).count()

        revenue = Order.objects.filter(
            created_at__date=today,
            status="DELIVERED",
            payment_status="COMPLETED",
        ).aggregate(total=Sum("total_amount"))["total"]
        context["today_revenue"] = float(revenue or 0.00)

        # Top selling items
        top_items = (
            OrderItem.objects.filter(order__created_at__date=today)
            .values("menu_item__name")
            .annotate(total_qty=Sum("quantity"))
            .order_by("-total_qty")[:5]
        )

        context["top_items"] = list(top_items)
        return context


import json


class KitchenOrdersAPIView(KitchenAdminRequiredMixin, View):
    def get(self, request):
        today = timezone.now().date()
        orders = Order.objects.exclude(status="DELIVERED").order_by(
            "priority", "created_at"
        )

        orders_list = []
        for order in orders:
            items_list = [
                {"name": item.menu_item.name, "qty": item.quantity}
                for item in order.items.all()
            ]

            elapsed = int(
                (timezone.now() - order.created_at).total_seconds() / 60
            )

            orders_list.append(
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "customer_name": order.customer_name,
                    "dining_option": order.get_dining_option_display(),
                    "table_number": order.table_number or "N/A",
                    "status": order.status,
                    "items": items_list,
                    "elapsed_minutes": elapsed,
                    "priority": order.priority,
                }
            )

        # Overall dashboard stats
        pending_count = Order.objects.exclude(status="DELIVERED").count()
        completed_count = Order.objects.filter(
            created_at__date=today, status="DELIVERED"
        ).count()
        revenue = (
            Order.objects.filter(
                created_at__date=today, status="DELIVERED"
            ).aggregate(total=Sum("total_amount"))["total"]
            or 0.0
        )

        return JsonResponse(
            {
                "success": True,
                "orders": orders_list,
                "stats": {
                    "pending": pending_count,
                    "completed": completed_count,
                    "revenue": float(revenue),
                },
            }
        )


class KitchenOrderStatusUpdateAPIView(KitchenAdminRequiredMixin, View):
    def post(self, request, order_id):
        try:
            data = json.loads(request.body)
            new_status = data.get("status")
            new_priority = data.get("priority")

            order = get_object_or_404(Order, id=order_id)

            if new_status:
                valid_statuses = [choice[0] for choice in Order.STATUS_CHOICES]
                if new_status in valid_statuses:
                    order.status = new_status
                    if new_status == "DELIVERED":
                        order.payment_status = "COMPLETED"
                    order.save()

            if new_priority is not None:
                order.priority = int(new_priority)
                order.save()

            return JsonResponse(
                {"success": True, "message": "Order updated successfully"}
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "error": str(e)}, status=400
            )
