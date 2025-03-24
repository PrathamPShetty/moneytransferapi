from rest_framework import serializers
from .models import CustomUser, Transaction
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'phone', 'password']

    def validate_name(self, value):
        # Allow alphabets, numbers and spaces
        if not all(char.isalnum() or char.isspace() for char in value):
            raise serializers.ValidationError("Name must contain only alphabets and numbers")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        
        user = CustomUser.objects.create_user(password=password, **validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(email=data.get('email'), password=data.get('password'))
        if user and user.is_verified:
            data['user'] = user
        elif user and not user.is_verified:
            raise serializers.ValidationError("Email not verified")
        else:
            raise serializers.ValidationError("Unable to login with provided credentials")
        return data

class TransferSerializer(serializers.Serializer):
    target_wallet_id = serializers.CharField(max_length=8)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    transfer_pin = serializers.CharField(max_length=4, write_only=True)

    def validate_target_wallet_id(self, value):
        if not value.isdigit() or len(value) != 8:
            raise serializers.ValidationError("Invalid wallet id format")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["email", "name", "phone", "wallet_id", "balance", "transfer_pin"]
        read_only_fields = ["email", "name", "phone", "wallet_id", "balance"]  # These fields cannot be edited

    def validate_transfer_pin(self, value):
        """Ensure transfer_pin is exactly 4 digits."""
        if not value.isdigit() or len(value) != 4:
            raise serializers.ValidationError("Transfer pin must be exactly 4 digits.")
        return value
    
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'sender', 'receiver', 'amount', 'timestamp', 'status']

# Super Admin serializers

class SuperAdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'name', 'phone', 'wallet_id', 'balance', 'plain_password']

class SuperAdminAddUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    transfer_pin = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'phone', 'password', 'transfer_pin']

    def create(self, validated_data):
        password = validated_data.pop('password')
        transfer_pin = validated_data.pop('transfer_pin')
        user = CustomUser.objects.create_user(password=password, transfer_pin=transfer_pin, **validated_data)
        return user

class SuperAdminEditBalanceSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2)

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    @classmethod
    def get_token(cls, user):
        if not user.is_verified:
            raise serializers.ValidationError("Your account is not verified. Please verify your email.")
        
        token = super().get_token(user)
        token['email'] = user.email
        token['is_verified'] = user.is_verified
        return token

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        if not user.is_verified:
            raise serializers.ValidationError("Your account is not verified. Please verify your email.")

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }