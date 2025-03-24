from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
import random



class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # Store raw password in plain_password field for super admin view (insecure!)
        user.plain_password = password
        user.set_password(password)
        # Generate unique 8-digit wallet ID if not provided
        if not extra_fields.get('wallet_id'):
            user.wallet_id = self.generate_unique_wallet_id()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        return self.create_user(email, password, **extra_fields)

    def generate_unique_wallet_id(self):
        while True:
            wallet_id = f"{random.randint(0, 99999999):08d}"
            if not CustomUser.objects.filter(wallet_id=wallet_id).exists():
                return wallet_id

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(
        max_length=100,
        validators=[RegexValidator(regex=r'^[A-Za-z0-9 ]+$', message="Name must contain only alphabets and numbers")]
    )
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\d+$', message="Phone number must contain only digits")]
    )
    wallet_id = models.CharField(max_length=8, unique=True, blank=True,editable=False)
    transfer_pin = models.CharField(
        max_length=4,
        validators=[RegexValidator(regex=r'^\d{4}$', message="Transfer pin must be 4 digits")]
    )
    is_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    plain_password = models.CharField(max_length=128, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone', 'transfer_pin']

    def __str__(self):
        return self.email

    @property
    def balance(self):
        """Fetch balance from related Account model."""
        account = getattr(self, "account", None)
        return account.balance if account else 0  # Return 0 if account does not exist


class Transaction(models.Model):
    sender = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='sent_transactions',
        null=True, blank=True
    )
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='success')  # e.g., 'success' or 'failed'

    def __str__(self):
        return f"Transaction from {self.sender} to {self.receiver} amount {self.amount}"

class EmailVerificationToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # You could add an expiration time if desired

    def __str__(self):
        return f"Token for {self.user.email}"

class Account(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE,related_name="account")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Account {self.user.wallet_id} - Balance: ₹{self.balance}"
