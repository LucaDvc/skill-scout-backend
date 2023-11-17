import os

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, smart_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from users.models import User
from rest_framework.permissions import AllowAny

from .serializers import RegisterSerializer, SetNewPasswordSerializer
from rest_framework import generics, status, serializers
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

from ..tasks import send_email


def get_email_confirmation_url(user_id):
    signer = TimestampSigner()
    token = signer.sign(user_id)
    # Frontend URL for email confirmation
    frontend_url = f'{os.environ.get("FRONTEND_URL")}/confirm-email'
    # Append the token as a query parameter
    confirmation_url = f'{frontend_url}?token={token}'
    return confirmation_url


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        confirmation_url = get_email_confirmation_url(user.id)
        message = f'Please click on the link to confirm your email: {confirmation_url}'
        subject = 'Confirm your email'
        send_email.delay(user.email, subject, message)


@api_view(['GET'])
def confirm_email(request, token):
    signer = TimestampSigner()

    try:
        user_id = signer.unsign(token, max_age=3600)  # 1 hour expiry
        user = User.objects.get(id=user_id)
        user.email_confirmed = True
        user.save()
        return Response({'message': 'Email confirmed successfully.'})
    except (BadSignature, User.DoesNotExist, SignatureExpired):
        return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def resend_confirm_email(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        # Check if the user's email is already confirmed
        if user.email_confirmed:
            return Response({'error': 'Email is already confirmed.'}, status=status.HTTP_400_BAD_REQUEST)

        confirmation_url = get_email_confirmation_url(user.id)
        message = f'Please click on the link to confirm your email: {confirmation_url}'
        subject = 'Confirm your email'
        send_email.delay(user.email, subject, message)
        return Response({'message': 'Confirmation email resent.'})

    except User.DoesNotExist:
        return Response({'error': 'User with the provided email does not exist.'}, status=status.HTTP_404_NOT_FOUND)


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        user = User.objects.get(email=request.data.get('email'))
        if user and not user.email_confirmed:
            return Response({'error': 'Email not confirmed'}, status=status.HTTP_401_UNAUTHORIZED)

        return super().post(request, *args, **kwargs)


@api_view(['POST'])
def request_password_reset_email(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
        token = PasswordResetTokenGenerator().make_token(user)
        frontend_url = f'{os.environ.get("FRONTEND_URL")}/reset-password'
        reset_url = f'{frontend_url}?uidb64={uidb64}&token={token}'
        send_email.delay(email, 'Password Reset Request', f'Please follow the link to reset your password: {reset_url}')
        return Response({'success': 'We have sent you a link to reset your password'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'User with the provided email does not exist.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PATCH'])
def set_new_password(request):
    serializer = SetNewPasswordSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        uidb64 = serializer.validated_data.get('uidb64')
        token = serializer.validated_data.get('token')
        password = serializer.validated_data.get('password')

        uid = smart_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=uid)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({'error': 'Token is invalid or expired'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()
        return Response({'success': True, 'message': 'Password has been reset successfully'})

    except (User.DoesNotExist, ValueError, TypeError):
        return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)

# TODO profile rud view (using UserSerializer)
# TODO forgot password send email
