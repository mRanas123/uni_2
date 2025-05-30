from rest_framework import serializers
from .models import User, City, Address, Order, Offer, Complaint, Rating
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from django_filters import rest_framework as filters


class LoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'birth_date', 'gender',
                  'phone', 'photo', 'work_experience', 'user_type', 'is_deleted', 'deleted_at']
        extra_kwargs = {
            'password': {'write_only': True},
            'is_deleted': {'read_only': True},
            'deleted_at': {'read_only': True},
        }

    def create(self, validated_data):
        # Prevent creating admin users
        if validated_data.get('user_type') == 3:  # Admin
            raise serializers.ValidationError("Cannot create admin users")

        # Only admin can create Technical Support
        request = self.context.get('request')
        if validated_data.get('user_type') == 4 and (not request or not request.user.is_authenticated or request.user.user_type != 3):
            raise serializers.ValidationError(
                "Only admins can create Technical Support users")

        validated_data['password'] = make_password(
            validated_data.get('password'))
        return super().create(validated_data)


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'address', 'gps_position', 'city', 'user']
        extra_kwargs = {
            'user': {'read_only': True}
        }

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status', 'notes', 'photo', 'short_video', 'budget',
                  'created_date', 'address', 'customer']
        extra_kwargs = {
            'customer': {'read_only': True}
        }


class OfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Offer
        fields = ['id', 'status', 'is_accept', 'price', 'company_paid', 'notes',
                  'last_time_date', 'expected_date', 'order', 'worker']
        extra_kwargs = {
            'worker': {'read_only': True}
        }

    def create(self, validated_data):
        validated_data['worker'] = self.context['request'].user
        return super().create(validated_data)


class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['id', 'type', 'message', 'user', 'created_at']
        extra_kwargs = {
            'user': {'read_only': True},
            'created_at': {'read_only': True}
        }

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'rate', 'note', 'order', 'user', 'created_at']
        extra_kwargs = {
            'user': {'read_only': True},
            'created_at': {'read_only': True}
        }

    def perform_create(self, serializer):
        order = serializer.validated_data['order']
        if order.status != 3:  # Only completed orders can be rated
            raise serializers.ValidationError(
                "Only completed orders can be rated")
        serializer.save(user=self.request.user)
