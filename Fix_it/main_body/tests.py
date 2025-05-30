from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, City, Address, Order, Offer, Complaint, Rating
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


class AuthTests(APITestCase):
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'user_type': 1
        }
        self.user = User.objects.create_user(**self.user_data)

    def test_user_login_success(self):
        url = reverse('login')
        data = {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_data['email'])

    def test_user_login_invalid_credentials(self):
        url = reverse('login')
        data = {
            'email': self.user_data['email'],
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_logout(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_forgot_password(self):
        url = reverse('forgot_password')
        data = {'email': self.user_data['email']}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_password(self):
        token = default_token_generator.make_token(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        
        url = reverse('reset_password', args=[uid, token])
        data = {'new_password': 'newpassword123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertTrue(check_password('newpassword123', self.user.password))


class UserTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass',
            first_name='Admin',
            last_name='User',
            user_type=3
        )
        self.client.force_authenticate(user=self.admin_user)
        self.customer_data = {
            'email': 'customer@example.com',
            'password': 'customerpass',
            'first_name': 'Customer',
            'last_name': 'User',
            'user_type': 1
        }
        self.customer_user = User.objects.create_user(**self.customer_data)
        
        # Additional users for search/filter tests
        User.objects.create_user(
            email='worker1@example.com',
            password='workerpass1',
            first_name='John',
            last_name='Doe',
            user_type=2
        )
        User.objects.create_user(
            email='worker2@example.com',
            password='workerpass2',
            first_name='Jane',
            last_name='Smith',
            user_type=2,
            is_deleted=True
        )

    def test_create_user_success(self):
        url = reverse('user-list')
        data = {
            'email': 'new@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'user_type': 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 5)  # Including the new one

    def test_search_users_by_email(self):
        url = reverse('user-list')
        response = self.client.get(url, {'search': 'worker1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['email'], 'worker1@example.com')

    def test_search_users_by_name(self):
        url = reverse('user-list')
        response = self.client.get(url, {'search': 'John'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['first_name'], 'John')

    def test_filter_users_by_type(self):
        url = reverse('user-list')
        response = self.client.get(url, {'user_type': 2})  # Workers
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only return active workers (worker2 is deleted)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['email'], 'worker1@example.com')

    def test_filter_users_by_is_deleted(self):
        url = reverse('user-list')
        response = self.client.get(url, {'is_deleted': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['email'], 'worker2@example.com')


class OrderTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='testpass',
            first_name='Customer',
            last_name='User',
            user_type=1
        )
        self.worker = User.objects.create_user(
            email='worker@example.com',
            password='testpass',
            first_name='Worker',
            last_name='User',
            user_type=2
        )
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass',
            first_name='Admin',
            last_name='User',
            user_type=3
        )
        
        self.city = City.objects.create(name='Test City')
        self.address = Address.objects.create(
            address='123 Test St',
            gps_position='0,0',
            city=self.city,
            user=self.customer
        )
        
        # Create orders with different statuses and dates
        self.order1 = Order.objects.create(
            status=1,
            budget=100.00,
            notes='Initial order',
            address=self.address,
            customer=self.customer,
            created_date=timezone.now() - timezone.timedelta(days=2)
        )
        self.order2 = Order.objects.create(
            status=2,
            budget=200.00,
            notes='In progress order',
            address=self.address,
            customer=self.customer,
            created_date=timezone.now() - timezone.timedelta(days=1)
        )
        self.order3 = Order.objects.create(
            status=3,
            budget=300.00,
            notes='Completed order',
            address=self.address,
            customer=self.customer,
            created_date=timezone.now()
        )
        
        self.offer = Offer.objects.create(
            status=1,
            price=150.00,
            order=self.order1,
            worker=self.worker
        )

    def test_filter_orders_by_status(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('order-list')
        response = self.client.get(url, {'status': 1})  # Pending
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.order1.id)

    def test_filter_orders_by_budget_range(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('order-list')
        response = self.client.get(url, {'budget_min': 150, 'budget_max': 250})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.order2.id)

    def test_search_orders_by_notes(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('order-list')
        response = self.client.get(url, {'search': 'progress'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.order2.id)
 
    def test_filter_orders_by_date_range(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('order-list')
        
        # Use timezone-aware datetimes
        yesterday = timezone.now() - timezone.timedelta(days=1)
        today = timezone.now()
        
        response = self.client.get(url, {
            'created_date_after': yesterday.date().isoformat(),
            'created_date_before': today.date().isoformat()
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # order2 and order3
        self.assertEqual({o['id'] for o in response.data}, {self.order2.id, self.order3.id})
    def test_order_created_date_ordering(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('order-list')
        response = self.client.get(url, {'ordering': 'created_date'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        # Should be in chronological order
        self.assertEqual(response.data[0]['id'], self.order1.id)
        self.assertEqual(response.data[1]['id'], self.order2.id)
        self.assertEqual(response.data[2]['id'], self.order3.id)


class OfferTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='testpass',
            first_name='Customer',
            last_name='User',
            user_type=1
        )
        self.worker1 = User.objects.create_user(
            email='worker1@example.com',
            password='testpass',
            first_name='Worker1',
            last_name='User',
            user_type=2
        )
        self.worker2 = User.objects.create_user(
            email='worker2@example.com',
            password='testpass',
            first_name='Worker2',
            last_name='User',
            user_type=2
        )
        
        self.city = City.objects.create(name='Test City')
        self.address = Address.objects.create(
            address='123 Test St',
            gps_position='0,0',
            city=self.city,
            user=self.customer
        )
        
        self.order1 = Order.objects.create(
            status=1,
            budget=100.00,
            address=self.address,
            customer=self.customer
        )
        self.order2 = Order.objects.create(
            status=1,
            budget=200.00,
            address=self.address,
            customer=self.customer
        )
        
        # Create offers with different prices and statuses
        self.offer1 = Offer.objects.create(
            status=1,
            price=120.00,
            order=self.order1,
            worker=self.worker1,
            last_time_date=timezone.now() - timezone.timedelta(days=1)
        )
        self.offer2 = Offer.objects.create(
            status=2,
            price=180.00,
            order=self.order1,
            worker=self.worker2,
            last_time_date=timezone.now()
        )
        self.offer3 = Offer.objects.create(
            status=1,
            price=220.00,
            order=self.order2,
            worker=self.worker1,
            last_time_date=timezone.now() - timezone.timedelta(hours=12)
        )

    def test_filter_offers_by_price_range(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('offer-list')
        response = self.client.get(url, {'price_min': 150, 'price_max': 200})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.offer2.id)

    def test_filter_offers_by_status(self):
        self.client.force_authenticate(user=self.worker1)
        url = reverse('offer-list')
        response = self.client.get(url, {'status': 1})  # Pending
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # offer1 and offer3
        self.assertEqual({o['id'] for o in response.data}, {self.offer1.id, self.offer3.id})

    def test_search_offers_by_worker_email(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('offer-list')
        response = self.client.get(url, {'search': 'worker2'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.offer2.id)

    def test_offer_ordering_by_last_time_date(self):
        self.client.force_authenticate(user=self.worker1)
        url = reverse('offer-list')
        response = self.client.get(url, {'ordering': 'last_time_date'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only worker1's offers
        # Should be in chronological order
        self.assertEqual(response.data[0]['id'], self.offer1.id)
        self.assertEqual(response.data[1]['id'], self.offer3.id)


class ComplaintTests(APITestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            email='customer@example.com',
            password='testpass',
            first_name='Customer',
            last_name='User',
            user_type=1
        )
        self.complaint = Complaint.objects.create(
            type=1,
            message='Test complaint',
            user=self.customer
        )

    def test_create_complaint(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('complaint-list')
        data = {
            'type': 2,
            'message': 'New complaint',
            'user': self.customer.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_complaints_as_customer(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('complaint-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)