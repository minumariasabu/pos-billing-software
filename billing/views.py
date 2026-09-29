from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, F
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from accounts.permissions import admin_required, is_admin
from catalog.models import Product, Supplier
from .models import *

@login_required
def home(request): return redirect("dashboard" if is_admin(request.user) else "billing")

@login_required
def billing(request):
    return render(request, "billing.html", {"can_discount": request.user.profile.can_discount or is_admin(request.user)})

@login_required
def invoice(request, pk):
    sale = get_object_or_404(Sale.objects.select_related("staff", "payment", "customer").prefetch_related("items"), pk=pk)
    if not is_admin(request.user) and sale.staff != request.user: raise PermissionDenied
    return render(request, "invoice.html", {"sale": sale, "biz": settings.BUSINESS})

def _ctx():
    t = Sale.objects.filter(created_at__date=timezone.localdate())
    return {"products": Product.objects.count(), "staff": User.objects.filter(profile__role="staff").count(),
            "suppliers": Supplier.objects.count(), "today_sales": t.aggregate(v=Sum("total"))["v"] or 0,
            "today_tx": t.count(), "revenue": Sale.objects.aggregate(v=Sum("total"))["v"] or 0,
            "low_stock": Product.objects.filter(is_active=True, stock__lte=F("reorder_level")),
            "recent_sales": Sale.objects.select_related("staff", "payment")[:8],
            "returns_total": SaleReturn.objects.count()}

@admin_required
def dashboard(request): return render(request, "dashboard.html", _ctx())
@admin_required
def mobile_dashboard(request): return render(request, "mobile.html", _ctx())

@admin_required
def ledger(request):
    qs = LedgerEntry.objects.all(); g = request.GET
    if g.get("from"): qs = qs.filter(date__date__gte=g["from"])
    if g.get("to"): qs = qs.filter(date__date__lte=g["to"])
    bal, rows = 0, []
    for e in qs: bal += e.credit - e.debit; rows.append((e, bal))
    return render(request, "ledger.html", {"rows": rows})
