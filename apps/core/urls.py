from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("menu/", views.MenuView.as_view(), name="menu"),
    path(
        "menu/search/", views.MenuSearchAPIView.as_view(), name="menu_search"
    ),
    path(
        "menu/item/<int:pk>/detail/",
        views.MenuItemDetailView.as_view(),
        name="menu_item_detail",
    ),
    path(
        "menu/item/<int:pk>/review/",
        views.SubmitReviewView.as_view(),
        name="submit_review",
    ),
    path("cart/sync/", views.CartSyncView.as_view(), name="cart_sync"),
    path(
        "coupon/apply/", views.CouponApplyView.as_view(), name="coupon_apply"
    ),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path(
        "payment/<str:order_number>/",
        views.PaymentView.as_view(),
        name="payment_portal",
    ),
    path(
        "payment/<str:order_number>/confirm/",
        views.PaymentConfirmAPIView.as_view(),
        name="payment_confirm",
    ),
    path(
        "checkout/success/<str:order_number>/",
        views.CheckoutSuccessView.as_view(),
        name="checkout_success",
    ),
    path(
        "order/track/<str:order_number>/",
        views.OrderTrackingView.as_view(),
        name="order_track",
    ),
    path(
        "order/invoice/<str:order_number>/",
        views.InvoicePDFView.as_view(),
        name="order_invoice",
    ),
    path(
        "order/<str:order_number>/reorder/",
        views.ReorderView.as_view(),
        name="reorder",
    ),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path(
        "newsletter/",
        views.NewsletterSubscribeView.as_view(),
        name="newsletter",
    ),
    # Customer Authentication & Dashboard
    path("login/", views.UnifiedLoginView.as_view(), name="login"),
    path("logout/", views.CustomerLogoutView.as_view(), name="logout"),
    path("register/", views.CustomerRegisterView.as_view(), name="register"),
    path(
        "forgot-password/",
        views.ForgotPasswordView.as_view(),
        name="forgot_password",
    ),
    path(
        "reset-password/<str:uidb64>/<str:token>/",
        views.ResetPasswordView.as_view(),
        name="reset_password",
    ),
    path(
        "customer/dashboard/",
        views.CustomerDashboardView.as_view(),
        name="customer_dashboard",
    ),
    path(
        "favorites/toggle/<int:item_id>/",
        views.ToggleFavoriteView.as_view(),
        name="toggle_favorite",
    ),
    # B.Tech Additions
    path("reserve/", views.ReserveTableView.as_view(), name="reserve"),
    path("blog/", views.BlogListView.as_view(), name="blog_list"),
    path(
        "blog/<slug:slug>/", views.BlogDetailView.as_view(), name="blog_detail"
    ),
    path(
        "notifications/read/<int:pk>/",
        views.MarkNotificationReadView.as_view(),
        name="mark_notification_read",
    ),
    path("robots.txt", views.RobotsTxtView.as_view(), name="robots_txt"),
    path("sitemap.xml", views.SitemapXmlView.as_view(), name="sitemap_xml"),
]
