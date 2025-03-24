from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Transaction, EmailVerificationToken, Account

# ✅ CustomUser Admin Panel Configuration
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'name', 'phone', 'wallet_id', 'balance', 'is_verified', 'is_staff')
    fieldsets = (
        (None, {'fields': ('email', 'password', 'plain_password')}),
        (_('Personal info'), {'fields': ('name', 'phone',  'transfer_pin')}),
        (_('Permissions'), {'fields': ('is_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'phone', 'transfer_pin', 'password1', 'password2'),
        }),
    )
    search_fields = ('email', 'name')
    ordering = ('email',)

# ✅ Register CustomUser Model
admin.site.register(CustomUser, CustomUserAdmin)

# ✅ Register Email Verification Token Model
admin.site.register(EmailVerificationToken)

# ✅ Register Account Model
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'balance')

# ✅ Register Transaction Model
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    # Updated list_display to use fields that exist in Transaction model.
    list_display = ('id', 'sender', 'receiver', 'amount', 'timestamp')
