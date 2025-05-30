
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .auth_views import user_login, user_logout, forgot_password, reset_password
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'cities', views.CityViewSet, basename='city')
router.register(r'addresses', views.AddressViewSet, basename='address')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'offers', views.OfferViewSet, basename='offer')
router.register(r'complaints', views.ComplaintViewSet, basename='complaint')
router.register(r'ratings', views.RatingViewSet, basename='rating')

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('reset-password/<uidb64>/<token>/', reset_password, name='reset_password'),
]