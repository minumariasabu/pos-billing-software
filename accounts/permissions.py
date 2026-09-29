from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import BasePermission, SAFE_METHODS

def is_admin(u):
    return bool(u.is_authenticated and u.is_active and (u.is_superuser or (hasattr(u, "profile") and u.profile.role == "admin")))

def admin_required(view):
    @wraps(view)
    @login_required
    def w(request, *a, **k):
        if not is_admin(request.user): raise PermissionDenied
        return view(request, *a, **k)
    return w

class IsAdminRole(BasePermission):
    def has_permission(self, request, view): return is_admin(request.user)

class AdminWriteStaffRead(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated: return False
        return request.method in SAFE_METHODS or is_admin(request.user)
