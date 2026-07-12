from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.AdminHomeView.as_view(), name="home"),
    path("login/", views.AdminLoginView.as_view(), name="login"),
    path("logout/", views.AdminLogoutView.as_view(), name="logout"),
    # Menu Items
    path("menu/", views.AdminMenuListView.as_view(), name="menu_list"),
    path("menu/add/", views.AdminMenuCreateView.as_view(), name="menu_create"),
    path(
        "menu/<int:pk>/edit/",
        views.AdminMenuUpdateView.as_view(),
        name="menu_edit",
    ),
    path(
        "menu/<int:pk>/delete/",
        views.AdminMenuDeleteView.as_view(),
        name="menu_delete",
    ),
    # Categories
    path(
        "categories/",
        views.AdminCategoryListView.as_view(),
        name="category_list",
    ),
    path(
        "categories/add/",
        views.AdminCategoryCreateView.as_view(),
        name="category_create",
    ),
    path(
        "categories/<int:pk>/edit/",
        views.AdminCategoryUpdateView.as_view(),
        name="category_edit",
    ),
    path(
        "categories/<int:pk>/delete/",
        views.AdminCategoryDeleteView.as_view(),
        name="category_delete",
    ),
    # Orders
    path("orders/", views.AdminOrderListView.as_view(), name="order_list"),
    path(
        "orders/<int:pk>/update/",
        views.AdminOrderUpdateView.as_view(),
        name="order_update",
    ),
    path(
        "export/orders/",
        views.OrderCSVExportView.as_view(),
        name="export_orders",
    ),
    # Coupons
    path("coupons/", views.AdminCouponListView.as_view(), name="coupon_list"),
    path(
        "coupons/add/",
        views.AdminCouponCreateView.as_view(),
        name="coupon_create",
    ),
    path(
        "coupons/<int:pk>/edit/",
        views.AdminCouponUpdateView.as_view(),
        name="coupon_edit",
    ),
    path(
        "coupons/<int:pk>/delete/",
        views.AdminCouponDeleteView.as_view(),
        name="coupon_delete",
    ),
    # Customers, Payments, Reviews & Settings
    path(
        "customers/",
        views.AdminCustomerListView.as_view(),
        name="customer_list",
    ),
    path(
        "payments/", views.AdminPaymentListView.as_view(), name="payment_list"
    ),
    path("reviews/", views.AdminReviewListView.as_view(), name="review_list"),
    path(
        "reviews/<int:pk>/delete/",
        views.AdminReviewDeleteView.as_view(),
        name="review_delete",
    ),
    path(
        "settings/",
        views.AdminSettingsUpdateView.as_view(),
        name="settings_edit",
    ),
    # Reservations & Blogs
    path(
        "reservations/",
        views.AdminReservationListView.as_view(),
        name="reservation_list",
    ),
    path(
        "reservations/<int:pk>/edit/",
        views.AdminReservationUpdateView.as_view(),
        name="reservation_edit",
    ),
    path("blogs/", views.AdminBlogListView.as_view(), name="blog_list"),
    path(
        "blogs/add/", views.AdminBlogCreateView.as_view(), name="blog_create"
    ),
    path(
        "blogs/<int:pk>/edit/",
        views.AdminBlogUpdateView.as_view(),
        name="blog_edit",
    ),
    path(
        "blogs/<int:pk>/delete/",
        views.AdminBlogDeleteView.as_view(),
        name="blog_delete",
    ),
]
