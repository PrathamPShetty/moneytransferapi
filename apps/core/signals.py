from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Account, CustomUser

@receiver(post_save, sender=Account)
def update_user_balance(sender, instance, **kwargs):
    """Ensures that CustomUser's balance is always updated when Account balance changes."""
    user = instance.user
    user.save()  # Triggers balance property recalculation
