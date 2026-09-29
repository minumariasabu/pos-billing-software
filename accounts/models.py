from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    ROLES = [("admin","Admin"),("staff","Staff")]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLES, default="staff")
    can_discount = models.BooleanField(default=False)
    max_discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    can_return = models.BooleanField(default=False)
    def __str__(self): return f"{self.user} ({self.role})"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def make_profile(sender, instance, created, **kw):
    if created:
        Profile.objects.create(user=instance, role="admin" if instance.is_superuser else "staff")
