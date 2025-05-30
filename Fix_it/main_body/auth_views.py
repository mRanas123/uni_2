 
from django.contrib.auth import authenticate, login, logout
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .models import User

@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    user = authenticate(request, username=email, password=password)
    if user is not None:
        if user.is_deleted:
            return Response({'detail': 'This account has been deactivated'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        login(request, user)
        return Response({
            'detail': 'Login successful',
            'user_id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
        })
    return Response({'detail': 'Invalid credentials'}, 
                  status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    logout(request)
    return Response({'detail': 'Logout successful'})

@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get('email')
    try:
        user = User.objects.get(email=email, is_deleted=False)
    except User.DoesNotExist:
        return Response({'detail': 'User not found'}, 
                      status=status.HTTP_404_NOT_FOUND)
    
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
    
    send_mail(
        'Password Reset Request',
        f'Click the link to reset your password: {reset_url}',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    
    return Response({'detail': 'Password reset email sent'})

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid, is_deleted=False)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        new_password = request.data.get('new_password')
        if not new_password:
            return Response({'detail': 'New password is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password has been reset successfully'})
    
    return Response({'detail': 'Invalid reset link'}, 
                  status=status.HTTP_400_BAD_REQUEST)