```markdown
# FixIt Service Platform API

A RESTful API for a service marketplace platform connecting customers with service workers.

## Table of Contents
- [API Documentation](#api-documentation)
  - [Authentication](#authentication)
    - [Login](#login)
    - [Logout](#logout)
    - [Forgot Password](#forgot-password)
    - [Reset Password](#reset-password)
- [Getting Started](#getting-started)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [API Endpoints](#api-endpoints)
- [License](#license)

## API Documentation

### Authentication

#### Login
- **Endpoint**: POST `/login/`
- **Request**:
  ```json
  {
    "email": "user@example.com",
    "password": "yourpassword"
  }
```

- **Success Response**:
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "detail": "Login successful",
      "user_id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "user_type": 1
    }
    ```
- **Error Responses**:
  - `400 Bad Request` - Invalid credentials
  - `400 Bad Request` - Account deactivated
- **Description**: Authenticates user and returns user details

#### Logout

- **Endpoint**: POST `/logout/`
- **Headers**:
  ```
  Authorization: Token <your_token>
  ```
- **Success Response**:
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "detail": "Logout successful"
    }
    ```
- **Description**: Logs out the current user

#### Forgot Password

- **Endpoint**: POST `/forgot-password/`
- **Request**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Success Response**:
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "detail": "Password reset email sent"
    }
    ```
- **Error Responses**:
  - `404 Not Found` - User not found
- **Description**: Sends password reset email to the user

#### Reset Password

- **Endpoint**: POST `/reset-password/<uidb64>/<token>/`
- **Request**:
  ```json
  {
    "new_password": "newsecurepassword123"
  }
  ```
- **Success Response**:
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "detail": "Password has been reset successfully"
    }
    ```
- **Error Responses**:
  - `400 Bad Request` - Invalid reset link
  - `400 Bad Request` - New password is required
- **Description**: Completes password reset process

Authorization: Token <your_token>

## Getting Started

### Installation

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies:

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file with the following variables:

```
SECRET_KEY=your_django_secret_key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/dbname
FRONTEND_URL=http://localhost:3000
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=user@example.com
EMAIL_HOST_PASSWORD=password
```

### Running Tests

To run the test suite:

```bash
python manage.py test
```

## API Documentation

### User Actions

1. **Create User**

   - **Endpoint**: POST `/users/`
   - **JSON**:
     ```json
     {
       "email": "user@example.com",
       "password": "securepassword",
       "first_name": "John",
       "last_name": "Doe",
       "user_type": 1,
       "birth_date": "1990-01-01",
       "gender": 1,
       "phone": "+123456789",
       "photo": "base64encodedimage",
       "work_experience": 5
     }
     ```
   - **Description**: Creates a new user account. All fields except optional ones (birth_date, gender, phone, photo, work_experience) are required.
2. **List Users**

   - **Endpoint**: GET `/users/`
   - **Description**: Returns list of all users (admin only)
3. **Retrieve User**

   - **Endpoint**: GET `/users/{id}/`
   - **Description**: Returns details of a specific user
4. **Update User**

   - **Endpoint**: PUT/PATCH `/users/{id}/`
   - **JSON** (partial updates allowed):
     ```json
     {
       "first_name": "UpdatedName",
       "last_name": "UpdatedLastName",
       "phone": "+987654321"
     }
     ```
   - **Description**: Updates user information
5. **Delete User**

   - **Endpoint**: DELETE `/users/{id}/`
   - **Description**: Deletes a user account (admin only)

### City Actions

1. **Create City**

   - **Endpoint**: POST `/cities/`
   - **JSON**:
     ```json
     {
       "name": "New York"
     }
     ```
   - **Description**: Creates a new city (authenticated users only)
2. **List Cities**

   - **Endpoint**: GET `/cities/`
   - **Description**: Returns list of all cities (public)

### Address Actions

1. **Create Address**

   - **Endpoint**: POST `/addresses/`
   - **JSON**:
     ```json
     {
       "address": "123 Main St",
       "gps_position": "40.7128,-74.0060",
       "city": 1
     }
     ```
   - **Description**: Creates a new address for the authenticated user
2. **List User Addresses**

   - **Endpoint**: GET `/addresses/`
   - **Description**: Returns addresses belonging to the authenticated user
3. **Update Address**

   - **Endpoint**: PUT/PATCH `/addresses/{id}/`
   - **JSON**:
     ```json
     {
       "address": "456 Updated St",
       "gps_position": "40.7130,-74.0062"
     }
     ```
   - **Description**: Updates an address (owner only)

### Order Actions

1. **Create Order**

   - **Endpoint**: POST `/orders/`
   - **JSON**:
     ```json
     {
       "status": 1,
       "budget": 500.00,
       "address": 1,
       "notes": "Please complete by Friday",
       "photo": "base64encodedimage",
       "short_video": "base64encodedvideo"
     }
     ```
   - **Description**: Creates a new service order (customers only)
2. **List Orders**

   - **Endpoint**: GET `/orders/`
   - **Optional Filter**: `?status=2` (filters by status)
   - **Description**: Returns orders based on user role:
     - Customers see their own orders
     - Workers see orders they've made offers on
     - Admins see all orders
3. **Update Order**

   - **Endpoint**: PUT/PATCH `/orders/{id}/`
   - **Allowed Fields for Customers**:
     ```json
     {
       "status": 2,
       "notes": "Updated notes",
       "photo": "newphoto",
       "short_video": "newvideo",
       "budget": 550.00
     }
     ```
   - **Description**: Updates order details with status transition validation

### Offer Actions

1. **Create Offer**

   - **Endpoint**: POST `/offers/`
   - **JSON**:
     ```json
     {
       "price": 450.00,
       "notes": "Can complete within 3 days",
       "expected_date": "2023-12-15",
       "order": 1
     }
     ```
   - **Description**: Creates a new offer for an order (workers only)
2. **List Offers**

   - **Endpoint**: GET `/offers/`
   - **Description**:
     - Workers see their own offers
     - Customers see offers on their orders

### Complaint Actions

1. **Create Complaint**

   - **Endpoint**: POST `/complaints/`
   - **JSON**:
     ```json
     {
       "type": 1,
       "message": "The worker arrived late"
     }
     ```
   - **Description**: Submits a new complaint
2. **List Complaints**

   - **Endpoint**: GET `/complaints/`
   - **Description**:
     - Users see their own complaints
     - Admins see all complaints

### Rating Actions

1. **Create Rating**

   - **Endpoint**: POST `/ratings/`
   - **JSON**:
     ```json
     {
       "rate": 5,
       "note": "Excellent service!",
       "order": 1
     }
     ```
   - **Description**: Rates a completed order (1-5 stars)
2. **List Ratings**

   - **Endpoint**: GET `/ratings/`
   - **Description**: Shows ratings on orders you've created or received

## License

This project is licensed under the MIT License 

Copyright (c) fix it developers at damascus universty.
All rights reserved.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
