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


class AddressTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass',
            first_name='Test',
            last_name='User',
            user_type=1
        )
        self.city = City.objects.create(name='Test City')
        self.address_data = {
            'address': '123 Test St',
            'gps_position': '0,0',
            'city': self.city.id,
           
        }
        self.address = Address.objects.create(
            address='123 Test St',
            gps_position='0,0',
            city=self.city,
            user=self.user
        )
        self.client.force_authenticate(user=self.user)

    def test_create_address(self):
        url = reverse('address-list')
        data = {
            'address': '456 New St',
            'gps_position': '1,1',
            'city': self.city.id,
            
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Address.objects.count(), 2)

    def test_list_addresses(self):
        url = reverse('address-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_address(self):
        url = reverse('address-detail', args=[self.address.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['address'], self.address.address)

    def test_update_address(self):
        url = reverse('address-detail', args=[self.address.id])
        data = {'address': 'Updated Address'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.address.refresh_from_db()
        self.assertEqual(self.address.address, 'Updated Address')

    def test_delete_address(self):
        url = reverse('address-detail', args=[self.address.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Address.objects.count(), 0)

    def test_cannot_access_other_users_addresses(self):
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass',
            first_name='Other',
            last_name='User',
            user_type=1
        )
        other_address = Address.objects.create(
            address='789 Other St',
            gps_position='2,2',
            city=self.city,
            user=other_user
        )

        url = reverse('address-detail', args=[other_address.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass',
            first_name='Admin',
            last_name='User',
            user_type=3  # Admin
        )
        self.city = City.objects.create(name='Test City')
        self.client.force_authenticate(user=self.user)

    def test_create_city(self):
        url = reverse('city-list')
        data = {'name': 'New City'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(City.objects.count(), 2)

    def test_list_cities(self):
        url = reverse('city-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_city(self):
        url = reverse('city-detail', args=[self.city.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.city.name)

    def test_update_city(self):
        url = reverse('city-detail', args=[self.city.id])
        data = {'name': 'Updated City'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.city.refresh_from_db()
        self.assertEqual(self.city.name, 'Updated City')

    def test_delete_city(self):
        url = reverse('city-detail', args=[self.city.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(City.objects.count(), 0)


class ComplaintTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass',
            first_name='Test',
            last_name='User',
            user_type=1
        )
        self.complaint = Complaint.objects.create(
            type=1,
            message='Test complaint',
            user=self.user
        )
        self.client.force_authenticate(user=self.user)

    def test_create_complaint(self):
        url = reverse('complaint-list')
        data = {
            'type': 2,
            'message': 'New complaint',
           
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Complaint.objects.count(), 2)

    def test_list_complaints(self):
        url = reverse('complaint-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_complaint(self):
        url = reverse('complaint-detail', args=[self.complaint.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], self.complaint.message)

    def test_update_complaint(self):
        url = reverse('complaint-detail', args=[self.complaint.id])
        data = {'message': 'Updated complaint'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.message, 'Updated complaint')

    def test_delete_complaint(self):
        url = reverse('complaint-detail', args=[self.complaint.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Complaint.objects.count(), 0)


class OfferTests(APITestCase):
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
        self.city = City.objects.create(name='Test City')
        self.address = Address.objects.create(
            address='123 Test St',
            gps_position='0,0',
            city=self.city,
            user=self.customer
        )
        self.order = Order.objects.create(
            status=1,
            budget=100.00,
            address=self.address,
            customer=self.customer
        )
        self.offer = Offer.objects.create(
            status=1,
            price=120.00,
            order=self.order,
            worker=self.worker
        )

    def test_create_offer_as_worker(self):
        self.client.force_authenticate(user=self.worker)
        url = reverse('offer-list')
        data = {
            'status': 1,  # Add required status
            'price': 150.00,
            'order': self.order.id,
            'worker': self.worker.id  # Add worker field
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_create_offer_as_customer(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('offer-list')
        data = {
            'price': 150.00,
            'order': self.order.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_offers_as_worker(self):
        self.client.force_authenticate(user=self.worker)
        url = reverse('offer-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_offers_as_customer(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('offer-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_offer(self):
        self.client.force_authenticate(user=self.worker)
        url = reverse('offer-detail', args=[self.offer.id])
        data = {'price': 130.00}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.price, 130.00)

    def test_delete_offer(self):
        self.client.force_authenticate(user=self.worker)
        url = reverse('offer-detail', args=[self.offer.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Offer.objects.count(), 0)


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
        self.city = City.objects.create(name='Test City')
        self.address = Address.objects.create(
            address='123 Test St',
            gps_position='0,0',
            city=self.city,
            user=self.customer
        )
        self.order = Order.objects.create(
            status=1,
            budget=100.00,
            address=self.address,
            customer=self.customer
        )

    def test_create_order_as_customer(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('order-list')
        data = {
            'status': 1,
            'budget': 200.00,
            'address': self.address.id,
            'customer': self.customer.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)

    def test_cannot_create_order_as_worker(self):
        self.client.force_authenticate(user=self.worker)
        url = reverse('order-list')
        data = {
            'status': 1,
            'budget': 200.00,
            'address': self.address.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_orders_as_customer(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_order_status(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('order-update-status', args=[self.order.id])
        data = {'status': 2}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 2)

    def test_delete_order(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('order-detail', args=[self.order.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Order.objects.count(), 0)


class RatingTests(APITestCase):
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
        self.city = City.objects.create(name='Test City')
        self.address = Address.objects.create(
            address='123 Test St',
            gps_position='0,0',
            city=self.city,
            user=self.customer
        )
        self.order = Order.objects.create(
            status=3,  # Completed
            budget=100.00,
            address=self.address,
            customer=self.customer
        )
        self.rating = Rating.objects.create(
            rate=4,
            order=self.order,
            user=self.customer
        )

    def test_create_rating_for_completed_order(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('rating-list')
        data = {
            'rate': 5,
            'note': 'Great service',
            'order': self.order.id,
           
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_rate_incomplete_order(self):
        incomplete_order = Order.objects.create(
            status=1,  # Pending
            budget=100.00,
            address=self.address,
            customer=self.customer
        )
        self.client.force_authenticate(user=self.customer)
        url = reverse('rating-list')
        data = {
            'rate': 5,
            'order': incomplete_order.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_ratings(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('rating-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_rating(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('rating-detail', args=[self.rating.id])
        data = {'rate': 3}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.rating.refresh_from_db()
        self.assertEqual(self.rating.rate, 3)

    def test_delete_rating(self):
        self.client.force_authenticate(user=self.customer)
        url = reverse('rating-detail', args=[self.rating.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Rating.objects.count(), 0)


class UserTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='adminpass',
            first_name='Admin',
            last_name='User',
            user_type=3
        )
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass',
            first_name='Test',
            last_name='User',
            user_type=1
        )
        self.client.force_authenticate(user=self.admin)

    def test_create_user(self):
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
        self.assertEqual(User.objects.count(), 3)

    def test_list_users(self):
        url = reverse('user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_user(self):
        url = reverse('user-detail', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_update_user(self):
        url = reverse('user-detail', args=[self.user.id])
        data = {'first_name': 'Updated'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')

    def test_soft_delete_user(self):
        url = reverse('user-detail', args=[self.user.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_deleted)
