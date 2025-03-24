from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404

from helpers.formatted_response import formatted_response
from .serializers import (
    ProfileSerializer, SignupSerializer, LoginSerializer, TransferSerializer, TransactionSerializer,
    SuperAdminUserSerializer, SuperAdminAddUserSerializer, SuperAdminEditBalanceSerializer
)
from .models import Account, CustomUser, Transaction, EmailVerificationToken
from django.conf import settings
from django.core.mail import send_mail
import uuid
from django.db import transaction as db_transaction
from django.db import models
from rest_framework.authtoken.models import Token
from django.db import transaction as db_transaction
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Create email verification token
            token_str = uuid.uuid4().hex
            EmailVerificationToken.objects.create(user=user, token=token_str)
            verification_link = request.build_absolute_uri(f"/api/verify-email/?token={token_str}")
            # Send email (will print to console using the console backend)
            send_mail(
                'Verify your email',
                f'Click on the link to verify your email: {verification_link}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            return formatted_response(
                status_code=status.HTTP_201_CREATED,
                data={"email": user.email},
                description="Signup successful. Please check your email to verify your account."
            )
        return formatted_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            data=serializer.errors,
            description="Signup failed.",
            status_flag=0
        )
class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        token_str = request.query_params.get('token')
        if not token_str:
            return Response({"error": "Token missing"}, status=status.HTTP_400_BAD_REQUEST)
        token_obj = EmailVerificationToken.objects.filter(token=token_str).first()
        if token_obj:
            user = token_obj.user
            user.is_verified = True
            user.save()
            token_obj.delete()
            return Response({"message": "Email verified successfully."})
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        data = {
            "email": user.email,
            "name": user.name,
            "phone": user.phone,
            "wallet_id": user.wallet_id,
            "balance": user.balance,
        }
        return formatted_response(
            status_code=status.HTTP_200_OK,
            data=data,
            description="User profile details fetched successfully"
        )
    def patch(self, request):
        """Allow users to update only their transfer_pin."""
        user = request.user
        serializer = ProfileSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return formatted_response(
                status_code=status.HTTP_200_OK,
                data={"message": "Transfer PIN updated successfully."},
                description="Profile updated"
            )
        return formatted_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            data=serializer.errors,
            description="Failed to update profile",
            status_flag=0
        )



class TransferView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TransferSerializer(data=request.data)
        if serializer.is_valid():
            receiver_wallet_id = serializer.validated_data['target_wallet_id']
            amount = serializer.validated_data['amount']
            transfer_pin = serializer.validated_data['transfer_pin']

            # Validate transfer PIN
            if request.user.transfer_pin != transfer_pin:
                return formatted_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data={},
                    description="Invalid transfer PIN",
                    status_flag=0
                )

            # Check if receiver exists
            receiver_user = CustomUser.objects.filter(wallet_id=receiver_wallet_id).first()
            if not receiver_user:
                 return formatted_response(
                    status_code=status.HTTP_404_NOT_FOUND,
                    data={},
                    description="Receiver wallet not found",
                    status_flag=0
                )

            # Fetch sender's account
            sender_account = Account.objects.filter(user=request.user).first()
            if not sender_account:
                return formatted_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data={},
                    description="Sender account does not exist",
                    status_flag=0
                )

            # Check balance
            if sender_account.balance < amount:
                return formatted_response(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    data={},
                    description="Insufficient balance",
                    status_flag=0
                )

            # Fetch receiver's account
            receiver_account, _ = Account.objects.get_or_create(user=receiver_user)

            with db_transaction.atomic():
                # Deduct from sender
                sender_account.balance -= amount
                sender_account.save()

                # Credit to receiver
                receiver_account.balance += amount
                receiver_account.save()

                # Create transaction record
                Transaction.objects.create(
                    sender=request.user, 
                    receiver=receiver_user, 
                    amount=amount
                )

            return formatted_response(
                status_code=status.HTTP_200_OK,
                data={},
                description="Transfer successful"
            )

        return formatted_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            data=serializer.errors,
            description="Transfer failed",
            status_flag=0
        )
    
class TransactionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        transactions = Transaction.objects.filter(sender=user) | Transaction.objects.filter(receiver=user)
        transactions = transactions.order_by('-timestamp')
        serializer = TransactionSerializer(transactions, many=True)
        return formatted_response(
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            description="Transactions retrieved successfully"
        )


# ----- Super Admin Endpoints -----

# Helper function to identify super admin by email
def is_super_admin(user):
    return user.email == "maddoxka20@gmail.com"

class SuperAdminRequired(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and is_super_admin(request.user)

class AdminAccountsView(APIView):
    permission_classes = [permissions.IsAuthenticated, SuperAdminRequired]
    def get(self, request):
        total_accounts = CustomUser.objects.count()
        return formatted_response(
            status_code=status.HTTP_200_OK,
            data={"total_accounts": total_accounts},
            description="Total accounts fetched successfully"
        )

class AdminTransactionsView(APIView):
    permission_classes = [permissions.IsAuthenticated, SuperAdminRequired]
    def get(self, request):
        transactions = Transaction.objects.all().order_by('-timestamp')
        serializer = TransactionSerializer(transactions, many=True)
        return formatted_response(
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            description="All transactions retrieved successfully"
        )

class AdminUsersView(APIView):
    permission_classes = [permissions.IsAuthenticated, SuperAdminRequired]
    def get(self, request):
        users = CustomUser.objects.all()
        serializer = SuperAdminUserSerializer(users, many=True)
        return formatted_response(
            status_code=status.HTTP_200_OK,
            data=serializer.data,
            description="User list retrieved successfully"
        )

class AdminAddUserView(APIView):
    permission_classes = [permissions.IsAuthenticated, SuperAdminRequired]
    def post(self, request):
        serializer = SuperAdminAddUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return formatted_response(
                status_code=status.HTTP_201_CREATED,
                data={"user_id": user.id},
                description="User added successfully"
            )
        return formatted_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            data=serializer.errors,
            description="Failed to add user",
            status_flag=0
        )


class AdminDeleteUserView(APIView):
    permission_classes = [permissions.IsAuthenticated, SuperAdminRequired]
    def delete(self, request, user_id):
        user = get_object_or_404(CustomUser, id=user_id)
        if is_super_admin(user):
            return formatted_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                data={},
                description="Cannot delete super admin",
                status_flag=0
            )
        user.delete()
        return formatted_response(
            status_code=status.HTTP_200_OK,
            data={},
            description="User deleted successfully"
        )


class AdminEditBalanceView(APIView):
    permission_classes = [permissions.IsAuthenticated, SuperAdminRequired]
    def post(self, request):
        serializer = SuperAdminEditBalanceSerializer(data=request.data)
        if serializer.is_valid():
            # Only allow editing the super admin's own balance
            request.user.balance = serializer.validated_data['balance']
            request.user.save()
            return formatted_response(
                status_code=status.HTTP_200_OK,
                data={"balance": request.user.balance},
                description="Balance updated successfully"
            )
        return formatted_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            data=serializer.errors,
            description="Failed to update balance",
            status_flag=0
        )
