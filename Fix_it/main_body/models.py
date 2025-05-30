from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)
    
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        (1, 'Customer'),
        (2, 'Worker'),
        (3, 'Admin'),
        (4, 'Technical Support'),
    )

    GENDER_CHOICES = (
        (1, 'Male'),
        (2, 'Female'),
    )

    username = None   
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    birth_date = models.DateTimeField(null=True, blank=True)
    gender = models.PositiveSmallIntegerField(
        choices=GENDER_CHOICES, null=True, blank=True)
    phone = models.CharField(max_length=45, null=True, blank=True, unique=True)
    photo = models.TextField(null=True, blank=True, unique=True)
    user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES)
    work_experience = models.IntegerField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)  # Add soft delete field
    deleted_at = models.DateTimeField(null=True, blank=True)  # Add deletion timestamp

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']

    objects = UserManager()
    
    def delete(self, *args, **kwargs):
        """Soft delete user"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']

    objects = UserManager()
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',  # Add this
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',  # Add this
        related_query_name='custom_user',
    )

class City(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Address(models.Model):
    address = models.CharField(max_length=45)
    gps_position = models.CharField(max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.address}, {self.city.name}"

class Order(models.Model):
    STATUS_CHOICES = (
        (1, 'Pending'),
        (2, 'In Progress'),
        (3, 'Completed'),
        (4, 'Cancelled'),
    )

    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=1)
    notes = models.CharField(max_length=200, null=True, blank=True)
    photo = models.TextField(null=True, blank=True)  # base64 or URL
    short_video = models.TextField(null=True, blank=True)  # base64 or URL
    budget = models.FloatField(validators=[MinValueValidator(0)])
    created_date = models.DateTimeField(auto_now_add=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    customer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='customer_orders')

    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"

class Offer(models.Model):
    STATUS_CHOICES = (
        (1, 'Pending'),
        (2, 'Accepted'),
        (3, 'Rejected'),
    )

    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES, default=1)
    is_accept = models.BooleanField(default=False)
    price = models.FloatField(validators=[MinValueValidator(0)])
    company_paid = models.BooleanField(default=False)
    notes = models.CharField(max_length=200, null=True, blank=True)
    last_time_date = models.DateTimeField(null=True, blank=True)
    expected_date = models.DateTimeField(null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    worker = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='worker_offers')

    def __str__(self):
        return f"Offer #{self.id} for Order #{self.order.id}"

class Complaint(models.Model):
    TYPE_CHOICES = (
        (1, 'Service Quality'),
        (2, 'Professionalism'),
        (3, 'Payment Issue'),
        (4, 'Other'),

    )

    type = models.PositiveSmallIntegerField(choices=TYPE_CHOICES)
    message = models.CharField(max_length=500)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Complaint #{self.id} - {self.get_type_display()}"

class Rating(models.Model):
    rate = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    note = models.CharField(max_length=200, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating {self.rate} stars for Order #{self.order.id}"
