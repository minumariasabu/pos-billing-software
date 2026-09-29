from decimal import Decimal as D, ROUND_HALF_UP
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from accounts.permissions import is_admin
from catalog.models import Product, StockMovement, Customer
from .models import *

class BillingError(Exception): pass
def q2(x): return D(x).quantize(D("0.01"), ROUND_HALF_UP)

@transaction.atomic
def checkout(user, lines, method, discount=0, received=None, customer_id=None):
    """All-or-nothing sale. lines = [{'product_id':1,'qty':2}, ...]"""
    if not lines: raise BillingError("Cart is empty")
    if method not in ("cash", "card", "upi"): raise BillingError("Invalid payment method")
    discount = q2(discount or 0); prof = user.profile
    qtys = {}
    for l in lines:
        pid, qty = int(l["product_id"]), int(l["qty"])
        if qty < 1: raise BillingError("Quantity must be at least 1")
        qtys[pid] = qtys.get(pid, 0) + qty
    products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=sorted(qtys), is_active=True).order_by("id")}
    for pid, qty in qtys.items():
        if pid not in products: raise BillingError(f"Product {pid} unavailable")
        if qty > products[pid].stock: raise BillingError(f"Only {products[pid].stock} of {products[pid].name} in stock")
    subtotal = sum(products[p].selling_price * n for p, n in qtys.items())
    if discount:
        if not (is_admin(user) or prof.can_discount): raise BillingError("You may not apply discounts")
        pct = D("100") if is_admin(user) else prof.max_discount_pct
        if discount > subtotal * pct / 100: raise BillingError("Discount exceeds your limit")
    sale = Sale.objects.create(staff=user, customer=Customer.objects.filter(id=customer_id).first() if customer_id else None,
                               subtotal=q2(subtotal), discount=discount, tax=0, total=0)
    total_tax = D(0); total = D(0)
    for pid, qty in qtys.items():
        p = products[pid]; gross = p.selling_price * qty
        line_disc = q2(discount * gross / subtotal)                      # proportional share
        tax = q2((gross - line_disc) * p.tax_percent / 100)
        net = q2(gross - line_disc + tax)
        SaleItem.objects.create(sale=sale, product=p, name=p.name, unit_price=p.selling_price, quantity=qty,
                                discount=line_disc, tax=tax, line_total=net)
        p.stock -= qty; p.save(update_fields=["stock", "updated_at"])
        StockMovement.objects.create(product=p, kind="sale", quantity=-qty, reference=str(sale.pk), created_by=user)
        total_tax += tax; total += net
    received = q2(received) if received not in (None, "") else total
    if method == "cash" and received < total: raise BillingError("Cash received is less than total")
    if method != "cash": received = total
    sale.tax, sale.total = total_tax, total
    sale.invoice_no = f"INV-{timezone.localdate():%Y%m%d}-{sale.pk:05d}"
    sale.save()
    Payment.objects.create(sale=sale, method=method, amount=total, received=received, change=received - total)
    LedgerEntry.objects.create(reference=sale.invoice_no, description=f"Sale ({method})", credit=total)
    return sale

@transaction.atomic
def process_return(user, sale_id, items, reason):
    """items = [{'sale_item_id':1,'qty':1}]. The original sale is never deleted or edited (only its status flag)."""
    if not (is_admin(user) or user.profile.can_return): raise BillingError("No permission to process returns")
    if not reason.strip(): raise BillingError("Reason is required")
    sale = Sale.objects.select_for_update().get(pk=sale_id)
    sr = SaleReturn.objects.create(sale=sale, reason=reason, refund_amount=0, handled_by=user)
    refund = D(0)
    for it in items:
        si = SaleItem.objects.select_for_update().get(pk=it["sale_item_id"], sale=sale)
        qty = int(it["qty"])
        if qty < 1 or qty > si.quantity - si.returned_qty: raise BillingError(f"Invalid return qty for {si.name}")
        refund += q2(si.line_total * qty / si.quantity)
        si.returned_qty += qty; si.save(update_fields=["returned_qty"])
        p = Product.objects.select_for_update().get(pk=si.product_id)
        p.stock += qty; p.save(update_fields=["stock", "updated_at"])
        StockMovement.objects.create(product=p, kind="return", quantity=qty, reference=sale.invoice_no, created_by=user)
        ReturnItem.objects.create(sale_return=sr, sale_item=si, quantity=qty)
    if refund == 0: raise BillingError("Nothing to return")
    sr.refund_amount = refund; sr.save()
    fully = not sale.items.filter(returned_qty__lt=F("quantity")).exists()
    sale.status = "returned" if fully else "partial_return"; sale.save(update_fields=["status"])
    LedgerEntry.objects.create(reference=sale.invoice_no, description=f"Return #{sr.pk}", debit=refund)
    return sr
