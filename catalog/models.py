from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    class Meta: verbose_name_plural = "categories"
    def __str__(self): return self.name

class Supplier(models.Model):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    gst_number = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Customer(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    def __str__(self): return f"{self.name} ({self.phone})"

class Product(models.Model):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    brand = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    size = models.CharField(max_length=30, blank=True)
    color = models.CharField(max_length=30, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=5)
    stock = models.IntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=5)
    image = models.ImageField(upload_to="products/", blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        indexes = [models.Index(fields=["name"]), models.Index(fields=["is_active", "stock"])]
        constraints = [models.CheckConstraint(check=models.Q(stock__gte=0), name="stock_non_negative")]
    @property
    def low_stock(self): return self.stock <= self.reorder_level
    def __str__(self): return f"{self.name} [{self.sku}]"

class StockMovement(models.Model):
    KINDS = [("purchase","Purchase"),("sale","Sale"),("return","Return"),("adjust","Adjustment")]
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="movements")
    kind = models.CharField(max_length=10, choices=KINDS)
    quantity = models.IntegerField(help_text="+in / -out")
    reference = models.CharField(max_length=50, blank=True)
    created_by = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]
