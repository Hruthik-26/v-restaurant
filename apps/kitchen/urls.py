from django.urls import path

from . import views

app_name = "kitchen"

urlpatterns = [
    path("dashboard/", views.KitchenDashboardView.as_view(), name="dashboard"),
    path(
        "api/orders/", views.KitchenOrdersAPIView.as_view(), name="api_orders"
    ),
    path(
        "api/orders/<int:order_id>/status/",
        views.KitchenOrderStatusUpdateAPIView.as_view(),
        name="update_status",
    ),
]
