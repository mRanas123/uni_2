from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from .models import User, City, Address, Order, Offer, Complaint, Rating
from .serializers import (
    UserSerializer, CitySerializer, AddressSerializer,
    OrderSerializer, OfferSerializer, ComplaintSerializer,
    RatingSerializer
)
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.utils import timezone
from rest_framework.decorators import action
from .filters import UserFilter, OrderFilter, OfferFilter
from rest_framework import filters as drf_filters
from django_filters.rest_framework import DjangoFilterBackend


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter()
    serializer_class = UserSerializer
    pagination_class = None
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter
    ]
    filterset_class = UserFilter
    search_fields = [
        'email',
        'first_name',
        'last_name',
        'phone',
        '=user_type'  # Exact match for user_type
    ]
    ordering_fields = [
        'email',
        'first_name',
        'last_name',
        'user_type',
        'date_joined',
        'updated_at'
    ]
    ordering = ['-date_joined']
    def get_queryset(self):
        queryset = User.objects.all().order_by('id')
        if not self.request.query_params.get('is_deleted', False):
            queryset = queryset.filter(is_deleted=False)
        return queryset
    def get_permissions(self):
        if self.action in ['create', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        elif self.action == 'list':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_destroy(self, instance):
        """Soft delete user"""
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()

    def create(self, request, *args, **kwargs):
        # Prevent creating admin users
        if request.data.get('user_type') == 3:  # Admin
            return Response(
                {"detail": "Cannot create admin users"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Only admin can create Technical Support
        if request.data.get('user_type') == 4:  # Technical Support
            if not request.user.is_authenticated or request.user.user_type != 3:
                return Response(
                    {"detail": "Only admins can create Technical Support users"},
                    status=status.HTTP_403_FORBIDDEN
                )

        return super().create(request, *args, **kwargs)

class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all().order_by('id')  # Add ordering
    serializer_class = CitySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None  # Add this
    
class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Add this to prevent pagination in tests

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user).order_by('id')  # Add ordering

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    pagination_class = None
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter
    ]
    filterset_class = OrderFilter
    search_fields = [
        'notes',
        'address__address',
        'address__city__name',
        'customer__email',
        'customer__first_name',
        'customer__last_name'
    ]
    ordering_fields = [
        'created_date',
        'updated_date',
        'budget',
        'status'
    ]
    ordering = ['-created_date']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        status_filter = self.request.query_params.get('status', None)

        queryset = Order.objects.all().order_by('id')

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if not user.is_authenticated:
            return queryset.none()

        if user.user_type == 1:  # Customer
            return queryset.filter(customer=user)
        elif user.user_type == 2:  # Worker
            return queryset.filter(offer__worker=user).distinct()
        return queryset
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if request.user.user_type != 1:
            return Response(
                {"detail": "Only customers can create orders"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        user = request.user

        # Only customer who owns the order or admin can update
        if user.user_type not in [1, 3] or (user.user_type == 1 and order.customer != user):
            return Response(
                {"detail": "You don't have permission to update this order"},
                status=status.HTTP_403_FORBIDDEN
            )

        # For customers, only allow updating certain fields
        if user.user_type == 1:
            allowed_fields = {'status', 'notes',
                              'photo', 'short_video', 'budget'}
            provided_fields = set(request.data.keys())
            invalid_fields = provided_fields - allowed_fields
            if invalid_fields:
                return Response(
                    {"detail": f"Customers can only update {', '.join(allowed_fields)}. Invalid fields: {', '.join(invalid_fields)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Status transition validation
        current_status = order.status
        new_status = request.data.get('status')
        if new_status is not None and isinstance(new_status, int):
            if current_status == 1 and new_status == 3:  # Pending -> Completed
                return Response(
                    {"detail": "Cannot transition directly from Pending to Completed"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')

        if not new_status:
            return Response(
                {'detail': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate status transition
        if order.status == 1 and new_status == 3:
            return Response(
                {"detail": "Cannot transition directly from Pending to Completed"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check permissions
        user = request.user
        if user.user_type not in [1, 3] or (user.user_type == 1 and order.customer != user):
            return Response(
                {"detail": "You don't have permission to update this order"},
                status=status.HTTP_403_FORBIDDEN
            )

        order.status = new_status
        order.save()

        return Response({'detail': 'Order status updated successfully'})

    def perform_destroy(self, instance):
        user = self.request.user
        if user.user_type not in [1, 3] or (user.user_type == 1 and instance.customer != user):
            raise PermissionDenied(
                "You don't have permission to delete this order")
        instance.delete()

class OfferViewSet(viewsets.ModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None 
    filter_backends = [
        DjangoFilterBackend,
        drf_filters.SearchFilter,
        drf_filters.OrderingFilter
    ]
    filterset_class = OfferFilter
    search_fields = [
        'notes',
        'order__notes',
        'worker__email',
        'worker__first_name',
        'worker__last_name'
    ]
    ordering_fields = [
        'price',
        'expected_date',
        'last_time_date',
        'created_at',
        'updated_at'
    ]
    ordering = ['-last_time_date']

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 2:  # Worker
            return Offer.objects.filter(worker=user).order_by('id')
        # Customers can see offers for their orders
        return Offer.objects.filter(order__customer=user).order_by('id')

    def create(self, request, *args, **kwargs):
        if request.user.user_type != 2:
            return Response(
                {"detail": "Only workers can create offers"},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

class ComplaintViewSet(viewsets.ModelViewSet):
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Add this

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 3:  # Admin can see all complaints
            return Complaint.objects.all().order_by('id')
        return Complaint.objects.filter(user=user).order_by('id')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

from drf_spectacular.utils import extend_schema_view, extend_schema

@extend_schema_view(
    list=extend_schema(description="List all ratings"),
    create=extend_schema(description="Create a new rating"),
    retrieve=extend_schema(description="Get a specific rating"),
    update=extend_schema(description="Update a rating"),
    partial_update=extend_schema(description="Partially update a rating"),
    destroy=extend_schema(description="Delete a rating"),
)
 
class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None  # Add this

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Rating.objects.none()
        user = self.request.user
        return (Rating.objects.filter(order__customer=user) | 
                Rating.objects.filter(user=user)).order_by('id').distinct()
    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        if order.status != 3:  # Only completed orders can be rated
            raise serializers.ValidationError(
                "Only completed orders can be rated")
        serializer.save(user=self.request.user)
