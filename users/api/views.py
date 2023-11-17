import os

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from users.models import User
from rest_framework.permissions import AllowAny

from .serializers import RegisterSerializer
from rest_framework import generics, status, serializers
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

from ..tasks import send_email


def get_confirmation_url(user_id):
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
        confirmation_url = get_confirmation_url(user.id)
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

        confirmation_url = get_confirmation_url(user.id)
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

# TODO profile rud view (using UserSerializer)
# TODO forgot password send email
