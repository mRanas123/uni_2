# filters.py
from django_filters import rest_framework as filters
from .models import User, Order, Offer
from django.db import models as django_models
from django_filters import DateFromToRangeFilter, NumberFilter

class BaseFilterSet(filters.FilterSet):
    created_date = DateFromToRangeFilter(field_name='date_joined')
    updated_date = DateFromToRangeFilter(field_name='updated_date')

    class Meta:
        abstract = True
        fields = {
            'date_joined': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'updated_date': ['exact', 'lt', 'lte', 'gt', 'gte'],
        }
class BaseOrderFilterSet(filters.FilterSet):
    created_date = DateFromToRangeFilter(field_name='created_date')
    updated_date = DateFromToRangeFilter(field_name='updated_date')

    class Meta:
        abstract = True
        fields = {
            'created_date': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'updated_date': ['exact', 'lt', 'lte', 'gt', 'gte'],
        }
class UserFilter(BaseFilterSet):
    email = filters.CharFilter(lookup_expr='icontains')
    full_name = filters.CharFilter(method='filter_full_name')
    user_type = filters.NumberFilter()
    is_active = filters.BooleanFilter()

    class Meta(BaseFilterSet.Meta):
        model = User
        fields = {
            'email': ['exact', 'icontains'],
            'first_name': ['exact', 'icontains'],
            'last_name': ['exact', 'icontains'],
            'phone': ['exact', 'icontains'],
            'user_type': ['exact'],
            'is_deleted': ['exact'],
            'gender': ['exact'],
        }

    def filter_full_name(self, queryset, name, value):
        return queryset.filter(
            django_models.Q(first_name__icontains=value) | 
            django_models.Q(last_name__icontains=value)
        )
 
class OrderFilter(BaseOrderFilterSet):
    budget_min = NumberFilter(field_name='budget', lookup_expr='gte')
    budget_max = NumberFilter(field_name='budget', lookup_expr='lte')
    customer_email = filters.CharFilter(field_name='customer__email', lookup_expr='icontains')
    city = filters.NumberFilter(field_name='address__city__id')
    created_date_after = filters.DateFilter(field_name='created_date', lookup_expr='gte')
    created_date_before = filters.DateFilter(field_name='created_date', lookup_expr='lte')

    class Meta(BaseOrderFilterSet.Meta):
        model = Order
        fields = {
            'status': ['exact', 'in'],
            'customer': ['exact'],
            'address': ['exact'],
            'budget': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'created_date': ['exact', 'lt', 'lte', 'gt', 'gte'],
        }
class OfferFilter(BaseFilterSet):
    price_min = NumberFilter(field_name='price', lookup_expr='gte')
    price_max = NumberFilter(field_name='price', lookup_expr='lte')
    worker_email = filters.CharFilter(field_name='worker__email', lookup_expr='icontains')
    order_status = filters.NumberFilter(field_name='order__status')

    class Meta(BaseFilterSet.Meta):
        model = Offer
        fields = {
            'status': ['exact', 'in'],
            'is_accept': ['exact'],
            'order': ['exact'],
            'worker': ['exact'],
            'price': ['exact', 'lt', 'lte', 'gt', 'gte'],
        }