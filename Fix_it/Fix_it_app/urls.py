from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import AllowAny  
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('main_body.urls')),  # Your existing API endpoints
    
    # Swagger/OpenAPI documentation URLs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(
        url_name='schema',
        permission_classes=[AllowAny]  # Explicitly set permissions
    ), name='swagger-ui'),
]