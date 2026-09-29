from django.contrib.auth.models import User
from django.db.models import Sum, Count, F
from django.utils import timezone
from rest_framework import serializers, viewsets, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from accounts.permissions import IsAdminRole, AdminWriteStaffRead, is_admin
from catalog.models import *
from .models import *
from . import services

class ProductS(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    low_stock = serializers.BooleanField(read_only=True)
    class Meta: model = Product; fields = "__all__"
class CategoryS(serializers.ModelSerializer):
    class Meta: model = Category; fields = "__all__"
class SupplierS(serializers.ModelSerializer):
    class Meta: model = Supplier; fields = "__all__"
class CustomerS(serializers.ModelSerializer):
    class Meta: model = Customer; fields = "__all__"
class ItemS(serializers.ModelSerializer):
    class Meta: model = SaleItem; exclude = ["sale"]
class SaleS(serializers.ModelSerializer):
    items = ItemS(many=True, read_only=True)
    staff_name = serializers.CharField(source="staff.username", read_only=True)
    method = serializers.CharField(source="payment.method", read_only=True)
    class Meta: model = Sale; fields = "__all__"
class StaffS(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    role = serializers.ChoiceField(choices=["admin", "staff"], source="profile.role", required=False)
    class Meta: model = User; fields = ["id","username","first_name","email","is_active","password","role"]
    def create(self, v):
        role = v.pop("profile", {}).get("role", "staff"); pw = v.pop("password")
        u = User(**v); u.set_password(pw); u.save(); u.profile.role = role; u.profile.save(); return u
    def update(self, inst, v):
        role = v.pop("profile", {}).get("role"); pw = v.pop("password", None)
        for k, x in v.items(): setattr(inst, k, x)
        if pw: inst.set_password(pw)
        inst.save()
        if role: inst.profile.role = role; inst.profile.save()
        return inst

class ProductV(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all(); serializer_class = ProductS
    permission_classes = [AdminWriteStaffRead]
    filter_backends = [filters.SearchFilter]; search_fields = ["name", "sku", "category__name"]
    def get_queryset(self):
        qs = super().get_queryset()
        if not is_admin(self.request.user): qs = qs.filter(is_active=True)
        if self.request.query_params.get("low_stock"): qs = qs.filter(stock__lte=F("reorder_level"))
        return qs
    def perform_destroy(self, obj): obj.is_active = False; obj.save()          # soft delete
class CategoryV(viewsets.ModelViewSet):
    queryset = Category.objects.all(); serializer_class = CategoryS; permission_classes = [AdminWriteStaffRead]
class SupplierV(viewsets.ModelViewSet):
    queryset = Supplier.objects.all(); serializer_class = SupplierS; permission_classes = [IsAdminRole]
class CustomerV(viewsets.ModelViewSet):
    queryset = Customer.objects.all(); serializer_class = CustomerS
    filter_backends = [filters.SearchFilter]; search_fields = ["name", "phone"]
class StaffV(viewsets.ModelViewSet):
    queryset = User.objects.select_related("profile"); serializer_class = StaffS; permission_classes = [IsAdminRole]
class SaleV(viewsets.ReadOnlyModelViewSet):
    serializer_class = SaleS
    filter_backends = [filters.SearchFilter]; search_fields = ["invoice_no", "customer__name"]
    def get_queryset(self):
        qs = Sale.objects.select_related("staff", "payment").prefetch_related("items"); p = self.request.query_params
        if not is_admin(self.request.user): qs = qs.filter(staff=self.request.user)   # staff: own only
        if p.get("staff"): qs = qs.filter(staff_id=p["staff"])
        if p.get("method"): qs = qs.filter(payment__method=p["method"])
        if p.get("from"): qs = qs.filter(created_at__date__gte=p["from"])
        if p.get("to"): qs = qs.filter(created_at__date__lte=p["to"])
        return qs

@api_view(["POST"])
def checkout(request):
    d = request.data
    try:
        s = services.checkout(request.user, d.get("items", []), d.get("method"), d.get("discount", 0),
                              d.get("received"), d.get("customer_id"))
    except (services.BillingError, ValueError, KeyError, TypeError) as e:
        return Response({"error": str(e)}, status=400)
    return Response({"invoice_no": s.invoice_no, "sale_id": s.id, "total": s.total,
                     "change": s.payment.change, "invoice_url": f"/invoice/{s.id}/"}, status=201)

@api_view(["POST"])
def return_sale(request, sale_id):
    try:
        r = services.process_return(request.user, sale_id, request.data.get("items", []), request.data.get("reason", ""))
    except (services.BillingError, ValueError, KeyError, Sale.DoesNotExist, SaleItem.DoesNotExist) as e:
        return Response({"error": str(e)}, status=400)
    return Response({"return_id": r.id, "refund": r.refund_amount}, status=201)

@api_view(["GET"])
@permission_classes([IsAdminRole])
def report_summary(request):
    today = timezone.localdate(); s = Sale.objects.all(); t = s.filter(created_at__date=today)
    return Response({
        "today_sales": t.aggregate(v=Sum("total"))["v"] or 0, "today_transactions": t.count(),
        "revenue": s.aggregate(v=Sum("total"))["v"] or 0,
        "refunds": SaleReturn.objects.aggregate(v=Sum("refund_amount"))["v"] or 0,
        "by_payment": list(Payment.objects.values("method").annotate(total=Sum("amount"), n=Count("id"))),
        "by_staff": list(s.values("staff__username").annotate(total=Sum("total"), n=Count("id"))),
        "best_sellers": list(SaleItem.objects.values("name").annotate(qty=Sum("quantity")).order_by("-qty")[:10]),
        "low_stock": Product.objects.filter(is_active=True, stock__lte=F("reorder_level")).count(),
        "inventory_value": sum(p.stock * p.purchase_price for p in Product.objects.filter(is_active=True)),
    })
