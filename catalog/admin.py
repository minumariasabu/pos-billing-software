from django.contrib import admin
from .models import *
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name","sku","category","selling_price","stock","is_active")
    list_filter = ("category","supplier","is_active"); search_fields = ("name","sku")
for m in (Category, Supplier, Customer, StockMovement): admin.site.register(m)
