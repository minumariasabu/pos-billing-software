from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from billing import api, views

r = DefaultRouter()
for name, vs in [("products", api.ProductV), ("categories", api.CategoryV), ("suppliers", api.SupplierV),
                 ("customers", api.CustomerV), ("staff", api.StaffV), ("transactions", api.SaleV)]:
    r.register(name, vs, basename=name)

urlpatterns = [
    path("django-admin/", admin.site.urls),          # full CRUD screens for admins
    path("login/", auth.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth.LogoutView.as_view(), name="logout"),
    path("", views.home, name="home"),
    path("billing/", views.billing, name="billing"),
    path("invoice/<int:pk>/", views.invoice, name="invoice"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("mobile-admin/", views.mobile_dashboard, name="mobile_admin"),
    path("ledger/", views.ledger, name="ledger"),
    path("api/", include(r.urls)),
    path("api/auth/token/", obtain_auth_token),
    path("api/checkout/", api.checkout),
    path("api/transactions/<int:sale_id>/return/", api.return_sale),
    path("api/reports/summary/", api.report_summary),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
