# API Documentation

This section provides comprehensive documentation for all API endpoints in the Travel Booking Platform, including request/response formats, authentication requirements, and usage examples.

## 📚 API Overview

The Travel Booking Platform provides a RESTful API with the following characteristics:

- **RESTful Design**: Standard HTTP methods and status codes
- **JSON Format**: All requests and responses use JSON
- **JWT Authentication**: Token-based authentication system
- **Comprehensive Documentation**: Interactive API documentation
- **Versioning**: API versioning strategy
- **Rate Limiting**: Protection against abuse

## 🔗 Base URL

```
Development: http://localhost:8000
Production:  https://api.travelbooking.com
```

## 🔐 Authentication

### JWT Token System

The API uses JWT (JSON Web Tokens) for authentication:

#### Token Types
- **Access Token**: Short-lived token for API access (15 minutes)
- **Refresh Token**: Long-lived token for token renewal (7 days)

#### Authentication Header
```http
Authorization: Bearer <access_token>
```

#### Token Flow
```
1. Login → Get access_token + refresh_token
2. Use access_token for API calls
3. When access_token expires → Use refresh_token to get new access_token
4. Logout → Blacklist tokens
```

## 📋 API Endpoints Overview

### Authentication Endpoints (`/auth`)
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user profile
- `PUT /auth/me` - Update user profile
- `PUT /auth/me/password` - Change password

### Search Endpoints (`/search`)
- `GET /search/flights` - Search flights
- `POST /search/flights` - Search flights (POST)
- `GET /search/hotels` - Search hotels
- `POST /search/hotels` - Search hotels (POST)
- `GET /search/buses` - Search buses
- `POST /search/buses` - Search buses (POST)
- `DELETE /search/cache` - Clear search cache

### Booking Endpoints (`/bookings`)
- `POST /bookings/flights` - Create flight booking
- `POST /bookings/hotels` - Create hotel booking
- `POST /bookings/buses` - Create bus booking
- `GET /bookings` - List user bookings
- `GET /bookings/{id}` - Get booking details
- `PUT /bookings/{id}/cancel` - Cancel booking

### Admin Endpoints (`/admin`)
- `GET /admin/dashboard/stats` - Dashboard statistics
- `GET /admin/users` - List all users
- `GET /admin/users/{id}` - Get user details
- `PUT /admin/agents/{id}/approve` - Approve/reject agent
- `PUT /admin/users/{id}/status` - Update user status
- `GET /admin/bookings` - List all bookings
- `PUT /admin/bookings/{id}/status` - Update booking status
- `GET /admin/analytics/bookings` - Booking analytics
- `GET /admin/health` - System health check

### System Endpoints
- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation

## 📊 Response Format

### Success Response
```json
{
  "data": { ... },
  "message": "Success message",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-01-15T10:30:00Z",
  "path": "/api/endpoint"
}
```

### Paginated Response
```json
{
  "total": 100,
  "page": 1,
  "size": 10,
  "total_pages": 10,
  "has_next": true,
  "has_prev": false,
  "items": [ ... ]
}
```

## 🔒 Authentication API

### Register User

```http
POST /auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "StrongP@ssw0rd",
  "name": "John Doe",
  "phone": "+1234567890",
  "role": "customer",
  "company_name": "TravelCo",
  "pan_number": "ABCDE1234F"
}
```

**Response (201 Created):**
```json
{
  "id": 123,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "customer",
  "is_active": true,
  "created_at": "2025-01-15T10:00:00Z"
}
```

### Login User

```http
POST /auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "StrongP@ssw0rd"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Refresh Token

```http
POST /auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Get Current User

```http
GET /auth/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 123,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "customer",
  "is_active": true,
  "created_at": "2025-01-15T10:00:00Z",
  "last_login": "2025-01-15T10:30:00Z"
}
```

## 🔍 Search API

### Search Flights

```http
GET /search/flights?origin=DEL&destination=BOM&depart_date=2025-01-20&adults=2&travel_class=economy
```

**Query Parameters:**
- `origin` (required): Origin airport IATA code
- `destination` (required): Destination airport IATA code
- `depart_date` (required): Departure date (YYYY-MM-DD)
- `return_date` (optional): Return date for round trip
- `adults` (required): Number of adult passengers (1-9)
- `children` (optional): Number of child passengers (0-9)
- `infants` (optional): Number of infant passengers (0-9)
- `travel_class` (optional): Travel class (economy, business, first)
- `max_results` (optional): Maximum results (1-100)

**Response (200 OK):**
```json
{
  "search_id": "search_123456",
  "total_results": 25,
  "search_time": 1.234,
  "cached": false,
  "results": [
    {
      "offer_id": "FL12345",
      "airline": "AirFast",
      "flight_number": "AF123",
      "origin": "DEL",
      "destination": "BOM",
      "departure_time": "2025-01-20T06:00:00Z",
      "arrival_time": "2025-01-20T09:00:00Z",
      "duration": "3h 0m",
      "stops": 0,
      "price": 7500.00,
      "currency": "INR",
      "travel_class": "economy"
    }
  ]
}
```

### Search Hotels

```http
GET /search/hotels?location=Mumbai&checkin=2025-01-20&checkout=2025-01-22&rooms=1&adults=2
```

**Query Parameters:**
- `location` (required): Hotel location or city
- `checkin` (required): Check-in date (YYYY-MM-DD)
- `checkout` (required): Check-out date (YYYY-MM-DD)
- `rooms` (required): Number of rooms (1-9)
- `adults` (required): Number of adult guests (1-18)
- `children` (optional): Number of child guests (0-18)
- `min_price` (optional): Minimum price per night
- `max_price` (optional): Maximum price per night
- `rating` (optional): Minimum hotel rating (1-5)
- `amenities` (optional): Comma-separated amenities
- `max_results` (optional): Maximum results (1-100)

**Response (200 OK):**
```json
{
  "search_id": "search_789012",
  "total_results": 15,
  "search_time": 0.876,
  "cached": false,
  "results": [
    {
      "hotel_id": "HTL789",
      "name": "Grand Plaza Mumbai",
      "address": "123 Main Street, Mumbai",
      "city": "Mumbai",
      "rating": 4.5,
      "price_per_night": 3500.00,
      "currency": "INR",
      "amenities": ["WiFi", "Pool", "Gym", "Restaurant"],
      "room_types": ["Standard", "Deluxe"],
      "distance_from_center": 2.5,
      "cancellation_policy": "Free cancellation until 24 hours before check-in"
    }
  ]
}
```

### Search Buses

```http
GET /search/buses?origin=Delhi&destination=Mumbai&travel_date=2025-01-20&passengers=2
```

**Query Parameters:**
- `origin` (required): Origin city or location
- `destination` (required): Destination city or location
- `travel_date` (required): Travel date (YYYY-MM-DD)
- `passengers` (required): Number of passengers (1-9)
- `return_date` (optional): Return date for round trip
- `max_results` (optional): Maximum results (1-100)

**Response (200 OK):**
```json
{
  "search_id": "search_345678",
  "total_results": 8,
  "search_time": 0.543,
  "cached": false,
  "results": [
    {
      "bus_id": "BUS1001",
      "operator": "GoBus",
      "bus_type": "AC Sleeper",
      "origin": "Delhi",
      "destination": "Mumbai",
      "departure_time": "2025-01-20T20:00:00Z",
      "arrival_time": "2025-01-21T04:00:00Z",
      "duration": "8h 0m",
      "seats_available": 15,
      "price": 1200.00,
      "currency": "INR",
      "amenities": ["WiFi", "Charging Points", "Blanket"],
      "boarding_points": ["Bus Stand 1", "Bus Stand 2"],
      "dropping_points": ["Bus Stop A", "Bus Stop B"]
    }
  ]
}
```

## 📝 Booking API

### Create Flight Booking

```http
POST /bookings/flights
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "offer_id": "FL12345",
  "passengers": [
    {
      "name": "John Doe",
      "age": 30,
      "type": "ADT",
      "passport_number": "A1234567",
      "nationality": "IN",
      "phone": "+1234567890"
    }
  ],
  "payment_details": {
    "method": "card",
    "card_number": "4111111111111111",
    "card_expiry": "12/25",
    "card_cvv": "123"
  },
  "special_requests": "Window seat preferred",
  "contact_email": "john@example.com",
  "contact_phone": "+1234567890"
}
```

**Response (201 Created):**
```json
{
  "booking_id": 456,
  "booking_reference": "BK20250115001",
  "status": "confirmed",
  "confirmation_number": "FL000456",
  "total_amount": 8250.00,
  "currency": "INR",
  "payment_status": "success",
  "expires_at": null,
  "created_at": "2025-01-15T10:30:00Z",
  "airline": "AirFast",
  "flight_number": "AF123",
  "origin": "DEL",
  "destination": "BOM",
  "departure_time": "2025-01-20T06:00:00Z",
  "arrival_time": "2025-01-20T09:00:00Z",
  "travel_class": "economy",
  "passenger_count": 1
}
```

### List User Bookings

```http
GET /bookings?page=1&size=10&status=confirmed
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `size` (optional): Number of bookings per page (default: 10)
- `status` (optional): Filter by booking status

**Response (200 OK):**
```json
{
  "total": 5,
  "page": 1,
  "size": 10,
  "bookings": [
    {
      "booking_id": 456,
      "type": "flight",
      "booking_reference": "BK20250115001",
      "status": "confirmed",
      "total_amount": 8250.00,
      "currency": "INR",
      "created_at": "2025-01-15T10:30:00Z",
      "airline": "AirFast",
      "origin": "DEL",
      "destination": "BOM",
      "departure_time": "2025-01-20T06:00:00Z"
    }
  ]
}
```

### Get Booking Details

```http
GET /bookings/456
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "booking_id": 456,
  "booking_reference": "BK20250115001",
  "type": "flight",
  "status": "confirmed",
  "total_amount": 8250.00,
  "currency": "INR",
  "payment_status": "success",
  "details": {
    "airline": "AirFast",
    "flight_number": "AF123",
    "origin": "DEL",
    "destination": "BOM",
    "departure_time": "2025-01-20T06:00:00Z",
    "arrival_time": "2025-01-20T09:00:00Z",
    "travel_class": "economy",
    "passenger_count": 1,
    "base_fare": 7500.00,
    "taxes": 750.00,
    "confirmation_number": "FL000456"
  },
  "passenger_details": [
    {
      "name": "John Doe",
      "age": 30,
      "type": "ADT",
      "passport_number": "A1234567",
      "nationality": "IN"
    }
  ],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

### Cancel Booking

```http
PUT /bookings/456/cancel
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "reason": "Change of plans",
  "refund_preference": "original_payment_method",
  "contact_for_refund": true
}
```

**Response (200 OK):**
```json
{
  "booking_id": 456,
  "status": "cancelled",
  "refund_amount": 6600.00,
  "currency": "INR",
  "refund_processing_time": "5-7 business days",
  "cancellation_fee": 1650.00,
  "message": "Your flight booking has been cancelled successfully."
}
```

## 👨‍💼 Admin API

### Get Dashboard Statistics

```http
GET /admin/dashboard/stats
Authorization: Bearer <admin_access_token>
```

**Response (200 OK):**
```json
{
  "total_users": 1250,
  "active_users": 1100,
  "pending_agents": 15,
  "approved_agents": 85,
  "total_bookings": 5432,
  "confirmed_bookings": 4890,
  "cancelled_bookings": 342,
  "pending_bookings": 200,
  "total_revenue": 2500000.00,
  "revenue_today": 12500.00,
  "revenue_this_month": 150000.00,
  "average_booking_value": 460.25,
  "bookings_today": 25,
  "cancellations_today": 3,
  "new_users_today": 12,
  "agent_applications_today": 2,
  "booking_success_rate": 95.0,
  "cancellation_rate": 5.0,
  "payment_success_rate": 98.5
}
```

### List All Users

```http
GET /admin/users?page=1&size=50&role=customer&is_active=true
Authorization: Bearer <admin_access_token>
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `size` (optional): Number of users per page (default: 50)
- `role` (optional): Filter by user role
- `is_active` (optional): Filter by active status
- `approval_status` (optional): Filter by approval status

**Response (200 OK):**
```json
{
  "total": 1250,
  "page": 1,
  "size": 50,
  "total_pages": 25,
  "has_next": true,
  "has_prev": false,
  "items": [
    {
      "id": 123,
      "email": "user@example.com",
      "name": "John Doe",
      "role": "customer",
      "is_active": true,
      "is_verified": true,
      "created_at": "2025-01-15T10:00:00Z",
      "last_login": "2025-01-15T10:30:00Z",
      "total_bookings": 5
    }
  ]
}
```

### Approve Agent

```http
PUT /admin/agents/124/approve
Authorization: Bearer <admin_access_token>
```

**Request Body:**
```json
{
  "approval_status": "approved",
  "rejection_reason": null,
  "admin_notes": "All documents verified successfully"
}
```

**Response (200 OK):**
```json
{
  "message": "Agent application approved successfully",
  "agent_id": 124,
  "approval_status": "approved",
  "agent_email": "agent@example.com"
}
```

## 🔧 System API

### Health Check

```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "version": "1.0.0",
  "environment": "production"
}
```

### API Information

```http
GET /
```

**Response (200 OK):**
```json
{
  "message": "Welcome to Travel Booking Platform API",
  "version": "1.0.0",
  "environment": "production",
  "docs_url": "/docs",
  "redoc_url": "/redoc",
  "health_url": "/health"
}
```

## 📊 Error Codes

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid request data |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

### Error Response Format

```json
{
  "detail": "Error message",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2025-01-15T10:30:00Z",
  "path": "/api/endpoint",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    }
  ]
}
```

## 🚀 Rate Limiting

### Rate Limits

- **Authenticated Users**: 1000 requests per hour
- **Unauthenticated Users**: 100 requests per hour
- **Admin Users**: 5000 requests per hour

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```

## 📱 SDK and Examples

### Python SDK Example

```python
import requests

# Authentication
response = requests.post('http://localhost:8000/auth/login', json={
    'email': 'user@example.com',
    'password': 'password'
})
tokens = response.json()

# Search flights
headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
search_response = requests.get(
    'http://localhost:8000/search/flights',
    params={
        'origin': 'DEL',
        'destination': 'BOM',
        'depart_date': '2025-01-20',
        'adults': 2
    },
    headers=headers
)
flights = search_response.json()

# Create booking
booking_response = requests.post(
    'http://localhost:8000/bookings/flights',
    json={
        'offer_id': flights['results'][0]['offer_id'],
        'passengers': [{'name': 'John Doe', 'age': 30, 'type': 'ADT'}],
        'payment_details': {'method': 'card', 'card_number': '4111111111111111'},
        'contact_email': 'john@example.com'
    },
    headers=headers
)
booking = booking_response.json()
```

### JavaScript SDK Example

```javascript
// Authentication
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password'
  })
});
const tokens = await loginResponse.json();

// Search flights
const searchResponse = await fetch(
  'http://localhost:8000/search/flights?origin=DEL&destination=BOM&depart_date=2025-01-20&adults=2',
  {
    headers: {'Authorization': `Bearer ${tokens.access_token}`}
  }
);
const flights = await searchResponse.json();

// Create booking
const bookingResponse = await fetch('http://localhost:8000/bookings/flights', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${tokens.access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    offer_id: flights.results[0].offer_id,
    passengers: [{name: 'John Doe', age: 30, type: 'ADT'}],
    payment_details: {method: 'card', card_number: '4111111111111111'},
    contact_email: 'john@example.com'
  })
});
const booking = await bookingResponse.json();
```

## 🔗 Interactive Documentation

### Swagger UI
Access the interactive API documentation at:
- **Development**: http://localhost:8000/docs
- **Production**: https://api.travelbooking.com/docs

### ReDoc
Alternative documentation format at:
- **Development**: http://localhost:8000/redoc
- **Production**: https://api.travelbooking.com/redoc

---

This API documentation provides comprehensive coverage of all endpoints, request/response formats, and usage examples for the Travel Booking Platform.
