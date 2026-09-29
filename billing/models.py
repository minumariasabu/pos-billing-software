from django.contrib.auth.models import User
from django.db import models
from catalog.models import Product, Customer

class Sale(models.Model):
    STATUS = [("completed","Completed"),("partial_return","Partially returned"),("returned","Returned")]
    invoice_no = models.CharField(max_length=30, unique=True, blank=True)
    staff = models.ForeignKey(User, on_delete=models.PROTECT, related_name="sales")
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name="sales")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=15, choices=STATUS, default="completed")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    class Meta: ordering = ["-created_at"]
    def __str__(self): return self.invoice_no

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)          # snapshot at time of sale
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)   # net of discount, incl. tax
    returned_qty = models.PositiveIntegerField(default=0)

class Payment(models.Model):
    METHODS = [("cash","Cash"),("card","Card"),("upi","UPI")]
    sale = models.OneToOneField(Sale, on_delete=models.PROTECT, related_name="payment")
    method = models.CharField(max_length=5, choices=METHODS)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    received = models.DecimalField(max_digits=12, decimal_places=2)
    change = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, default="paid")

class SaleReturn(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="returns")
    reason = models.TextField()
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, default="processed")
    handled_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

class ReturnItem(models.Model):
    sale_return = models.ForeignKey(SaleReturn, on_delete=models.CASCADE, related_name="items")
    sale_item = models.ForeignKey(SaleItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()

class LedgerEntry(models.Model):
    date = models.DateTimeField(auto_now_add=True, db_index=True)
    reference = models.CharField(max_length=40)
    description = models.CharField(max_length=200)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0)   # money out (refunds)
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # money in (sales)
    class Meta: ordering = ["date", "id"]
