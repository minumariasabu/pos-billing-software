from django.contrib import admin
from .models import *
class ReadOnly(admin.ModelAdmin):   # completed sales cannot be silently modified
    def has_change_permission(self, r, obj=None): return False
    def has_add_permission(self, r): return False
    def has_delete_permission(self, r, obj=None): return False
class ItemInline(admin.TabularInline):
    model = SaleItem; extra = 0; can_delete = False
    def has_change_permission(self, r, obj=None): return False
    def has_add_permission(self, r, obj=None): return False
@admin.register(Sale)
class SaleAdmin(ReadOnly):
    list_display = ("invoice_no","created_at","staff","total","status"); list_filter = ("status","staff")
    search_fields = ("invoice_no",); inlines = [ItemInline]
for m in (SaleReturn, LedgerEntry, Payment): admin.site.register(m, ReadOnly)
