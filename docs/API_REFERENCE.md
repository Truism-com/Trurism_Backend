# API Reference Documentation

> **Version:** 1.0.0  
> **Base URL:** `https://api.yourdomain.com` or `http://localhost:8000`  
> **Last Updated:** February 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Response Formats](#common-response-formats)
4. [API Endpoints](#api-endpoints)
   - [Health & System](#health--system)
   - [Authentication](#authentication-endpoints)
   - [Search](#search-endpoints)
   - [Bookings](#booking-endpoints)
   - [Payments](#payment-endpoints)
   - [Wallet](#wallet-endpoints)
   - [Holidays](#holiday-endpoints)
   - [Visa](#visa-endpoints)
   - [Activities](#activity-endpoints)
   - [Transfers](#transfer-endpoints)
   - [CMS](#cms-endpoints)
   - [Dashboard](#dashboard-endpoints)
   - [API Keys](#api-key-endpoints)
   - [Admin](#admin-endpoints)
   - [Tenant/White-Label](#tenant-endpoints)
   - [Markup](#markup-endpoints)
   - [Pricing](#pricing-endpoints)
   - [Settings](#settings-endpoints)
   - [Company](#company-endpoints)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Pagination](#pagination)

---

## Overview

The Travel Booking Platform API is a RESTful API built with FastAPI. All endpoints return JSON responses and accept JSON request bodies where applicable.

### API Documentation

| Format | URL | Description |
|--------|-----|-------------|
| Swagger UI | `/docs` | Interactive API documentation |
| ReDoc | `/redoc` | Alternative API documentation |
| OpenAPI JSON | `/openapi.json` | OpenAPI 3.0 specification |

---

## Authentication

### Bearer Token Authentication

Most endpoints require authentication via JWT Bearer tokens.

**Header Format:**
```http
Authorization: Bearer <access_token>
```

### API Key Authentication

Alternative authentication for server-to-server communication.

**Header Format:**
```http
X-API-Key: <your_api_key>
```

### Tenant Identification (Optional)

For white-label/multi-tenant setups:

```http
X-Tenant-ID: <tenant_id>
X-Tenant-Code: <tenant_code>
```

---

## Common Response Formats

### Success Response

```json
{
  "data": { ... },
  "message": "Success"
}
```

### Error Response

```json
{
  "detail": "Error message",
  "path": "/endpoint/path"
}
```

### Validation Error Response

```json
{
  "detail": "Validation error",
  "errors": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "path": "/endpoint/path"
}
```

### Paginated Response

```json
{
  "items": [ ... ],
  "total": 100,
  "page": 1,
  "size": 20,
  "total_pages": 5,
  "has_next": true,
  "has_prev": false
}
```

---

## API Endpoints

---

## Health & System

### GET `/`

Root endpoint with API information.

**Authentication:** None

**Response:**
```json
{
  "message": "Welcome to Travel Booking Platform API",
  "version": "1.0.0",
  "environment": "development",
  "docs_url": "/docs",
  "redoc_url": "/redoc",
  "health_url": "/health"
}
```

---

### GET `/health`

Health check endpoint for monitoring and load balancers.

**Authentication:** None

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1738764800.123,
  "version": "1.0.0",
  "environment": "production",
  "issues": []
}
```

**Status Values:**
- `healthy` - All systems operational
- `degraded` - Some non-critical issues

---

## Authentication Endpoints

Base path: `/auth`

### POST `/auth/register`

Register a new user account.

**Authentication:** None

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "name": "John Doe",
  "phone": "+919876543210",
  "address": "123 Main Street, Mumbai",
  "role": "customer",
  "company_name": "Travel Corp",
  "pan_number": "ABCDE1234F"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `email` | string | Yes | Valid email format |
| `password` | string | Yes | Min 8 chars, 1 uppercase, 1 lowercase, 1 digit |
| `name` | string | Yes | - |
| `phone` | string | No | Valid phone format |
| `address` | string | No | - |
| `role` | enum | No | `customer`, `agent`, `admin` (default: `customer`) |
| `company_name` | string | Conditional | Required if role is `agent` |
| `pan_number` | string | Conditional | Required if role is `agent`, exactly 10 characters |

**Response:** `201 Created`
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "+919876543210",
  "address": "123 Main Street, Mumbai",
  "role": "customer",
  "is_active": true,
  "is_verified": false,
  "company_name": null,
  "pan_number": null,
  "approval_status": null,
  "created_at": "2026-02-05T10:30:00Z",
  "last_login": null
}
```

---

### POST `/auth/login`

Authenticate user and obtain JWT tokens.

**Authentication:** None

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### POST `/auth/refresh`

Refresh access token using refresh token.

**Authentication:** None

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

---

### POST `/auth/logout`

Logout and invalidate current token.

**Authentication:** Bearer Token

**Response:** `200 OK`
```json
{
  "message": "Successfully logged out"
}
```

---

### GET `/auth/me`

Get current user's profile.

**Authentication:** Bearer Token

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "+919876543210",
  "address": "123 Main Street, Mumbai",
  "role": "customer",
  "is_active": true,
  "is_verified": true,
  "company_name": null,
  "pan_number": null,
  "approval_status": null,
  "created_at": "2026-02-05T10:30:00Z",
  "last_login": "2026-02-05T14:20:00Z"
}
```

---

### PUT `/auth/me`

Update current user's profile.

**Authentication:** Bearer Token

**Request Body:**
```json
{
  "name": "John Smith",
  "phone": "+919876543211",
  "address": "456 New Street, Delhi"
}
```

**Response:** `200 OK` (Same as GET `/auth/me`)

---

### PUT `/auth/me/password`

Change current user's password.

**Authentication:** Bearer Token

**Request Body:**
```json
{
  "current_password": "OldPass123",
  "new_password": "NewSecure456"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

---

## Search Endpoints

Base path: `/search`

### GET `/search/flights`

Search for available flights.

**Authentication:** None

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `origin` | string | Yes | Origin airport IATA code (e.g., "DEL") |
| `destination` | string | Yes | Destination airport IATA code (e.g., "BOM") |
| `depart_date` | string | Yes | Departure date (YYYY-MM-DD) |
| `return_date` | string | No | Return date for round trip (YYYY-MM-DD) |
| `adults` | integer | Yes | Number of adults (1-9) |
| `children` | integer | No | Number of children (0-9, default: 0) |
| `infants` | integer | No | Number of infants (0-9, ≤ adults, default: 0) |
| `travel_class` | string | No | `economy`, `premium_economy`, `business`, `first` |
| `max_results` | integer | No | Maximum results (1-100, default: 50) |

**Example Request:**
```
GET /search/flights?origin=DEL&destination=BOM&depart_date=2026-03-15&adults=2&travel_class=economy
```

**Response:** `200 OK`
```json
{
  "search_id": "abc123",
  "results": [
    {
      "offer_id": "flight_offer_123",
      "airline": "Air India",
      "flight_number": "AI302",
      "origin": "DEL",
      "destination": "BOM",
      "departure_time": "2026-03-15T06:00:00",
      "arrival_time": "2026-03-15T08:15:00",
      "duration": "2h 15m",
      "stops": 0,
      "aircraft": "A320",
      "price": 7500.00,
      "currency": "INR",
      "travel_class": "economy",
      "baggage_allowance": "15kg",
      "refundable": false
    }
  ],
  "total_results": 25,
  "search_time": 1.234
}
```

---

### POST `/search/flights`

Search for flights using request body (alternative to GET).

**Authentication:** None

**Request Body:**
```json
{
  "origin": "DEL",
  "destination": "BOM",
  "depart_date": "2026-03-15",
  "return_date": null,
  "adults": 2,
  "children": 0,
  "infants": 0,
  "travel_class": "economy",
  "max_results": 50
}
```

**Response:** Same as GET `/search/flights`

---

### GET `/search/hotels`

Search for available hotels.

**Authentication:** None

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `location` | string | Yes | City or location name |
| `checkin` | string | Yes | Check-in date (YYYY-MM-DD) |
| `checkout` | string | Yes | Check-out date (YYYY-MM-DD) |
| `rooms` | integer | Yes | Number of rooms (1-9) |
| `adults` | integer | Yes | Number of adults (1-18) |
| `children` | integer | No | Number of children (0-18, default: 0) |
| `min_price` | float | No | Minimum price per night |
| `max_price` | float | No | Maximum price per night |
| `rating` | float | No | Minimum hotel rating (1-5) |
| `amenities` | string | No | Comma-separated amenities |
| `max_results` | integer | No | Maximum results (1-100, default: 50) |

**Response:** `200 OK`
```json
{
  "search_id": "hotel_123",
  "results": [
    {
      "hotel_id": "hotel_456",
      "name": "Grand Plaza Hotel",
      "address": "123 Main Street, Mumbai",
      "city": "Mumbai",
      "rating": 4.5,
      "price_per_night": 5500.00,
      "currency": "INR",
      "amenities": ["WiFi", "Pool", "Gym", "Restaurant"],
      "room_types": ["Deluxe", "Suite"],
      "distance_from_center": 2.5,
      "cancellation_policy": "Free cancellation until 24 hours before check-in",
      "images": ["https://..."],
      "description": "Luxury hotel in the heart of Mumbai"
    }
  ],
  "total_results": 15
}
```

---

### GET `/search/buses`

Search for available buses.

**Authentication:** None

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `origin` | string | Yes | Origin city |
| `destination` | string | Yes | Destination city |
| `travel_date` | string | Yes | Travel date (YYYY-MM-DD) |
| `passengers` | integer | Yes | Number of passengers (1-9) |
| `return_date` | string | No | Return date for round trip |
| `max_results` | integer | No | Maximum results (1-100) |

**Response:** `200 OK`
```json
{
  "search_id": "bus_123",
  "results": [
    {
      "bus_id": "bus_456",
      "operator": "VRL Travels",
      "bus_type": "AC Sleeper",
      "origin": "Mumbai",
      "destination": "Bangalore",
      "departure_time": "2026-03-15T20:00:00",
      "arrival_time": "2026-03-16T08:00:00",
      "duration": "12h 0m",
      "price": 1800.00,
      "currency": "INR",
      "available_seats": 25,
      "amenities": ["AC", "Blanket", "Water Bottle"]
    }
  ],
  "total_results": 10
}
```

---

## Booking Endpoints

Base path: `/bookings`

### POST `/bookings/flights`

Create a new flight booking.

**Authentication:** Bearer Token

**Request Body:**
```json
{
  "offer_id": "flight_offer_123",
  "passengers": [
    {
      "name": "John Doe",
      "age": 30,
      "type": "ADT",
      "passport_number": "A12345678",
      "nationality": "IN",
      "phone": "+919876543210",
      "email": "john@example.com"
    }
  ],
  "payment_details": {
    "method": "card",
    "card_number": "4111111111111111",
    "card_expiry": "12/28",
    "card_cvv": "123"
  },
  "special_requests": "Window seat preferred",
  "contact_email": "john@example.com",
  "contact_phone": "+919876543210"
}
```

**Passenger Types:**
- `ADT` - Adult
- `CHD` - Child
- `INF` - Infant

**Payment Methods:**
- `card` - Credit/Debit Card
- `upi` - UPI Payment
- `net_banking` - Net Banking
- `wallet` - Digital Wallet
- `pay_later` - Pay Later

**Response:** `201 Created`
```json
{
  "booking_id": 1,
  "booking_reference": "TBK20260205001",
  "status": "confirmed",
  "confirmation_number": "ABC123",
  "total_amount": 7500.00,
  "currency": "INR",
  "payment_status": "completed",
  "expires_at": null,
  "created_at": "2026-02-05T10:30:00Z",
  "airline": "Air India",
  "flight_number": "AI302",
  "origin": "DEL",
  "destination": "BOM",
  "departure_time": "2026-03-15T06:00:00",
  "arrival_time": "2026-03-15T08:15:00",
  "travel_class": "economy",
  "passenger_count": 1
}
```

---

### POST `/bookings/hotels`

Create a new hotel booking.

**Authentication:** Bearer Token

**Request Body:**
```json
{
  "hotel_id": "hotel_456",
  "checkin_date": "2026-03-15",
  "checkout_date": "2026-03-18",
  "rooms": 1,
  "adults": 2,
  "children": 0,
  "guest_details": [
    {
      "name": "John Doe",
      "email": "john@example.com"
    }
  ],
  "payment_details": {
    "method": "upi",
    "upi_id": "john@upi"
  },
  "special_requests": "Late checkout requested",
  "contact_email": "john@example.com",
  "contact_phone": "+919876543210"
}
```

**Response:** `201 Created` (Similar structure to flight booking)

---

### POST `/bookings/buses`

Create a new bus booking.

**Authentication:** Bearer Token

**Request Body:**
```json
{
  "bus_id": "bus_456",
  "travel_date": "2026-03-15",
  "passengers": 2,
  "passenger_details": [
    {
      "name": "John Doe",
      "age": 30,
      "type": "ADT"
    },
    {
      "name": "Jane Doe",
      "age": 28,
      "type": "ADT"
    }
  ],
  "payment_details": {
    "method": "card",
    "card_number": "4111111111111111",
    "card_expiry": "12/28",
    "card_cvv": "123"
  },
  "boarding_point": "Mumbai Central",
  "dropping_point": "Bangalore Majestic",
  "contact_email": "john@example.com",
  "contact_phone": "+919876543210"
}
```

---

### GET `/bookings/`

Get user's bookings with pagination.

**Authentication:** Bearer Token

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `size` | integer | No | Items per page (1-50, default: 10) |
| `status` | string | No | Filter by status |

**Response:** `200 OK`
```json
{
  "total": 25,
  "page": 1,
  "size": 10,
  "bookings": [
    {
      "booking_id": 1,
      "type": "flight",
      "booking_reference": "TBK20260205001",
      "status": "confirmed",
      "total_amount": 7500.00,
      "currency": "INR",
      "created_at": "2026-02-05T10:30:00Z",
      "airline": "Air India",
      "origin": "DEL",
      "destination": "BOM",
      "departure_time": "2026-03-15T06:00:00"
    }
  ]
}
```

---

### GET `/bookings/{booking_id}`

Get detailed booking information.

**Authentication:** Bearer Token

**Response:** `200 OK`
```json
{
  "booking_id": 1,
  "booking_reference": "TBK20260205001",
  "type": "flight",
  "status": "confirmed",
  "total_amount": 7500.00,
  "currency": "INR",
  "payment_status": "completed",
  "details": {
    "airline": "Air India",
    "flight_number": "AI302",
    "origin": "DEL",
    "destination": "BOM",
    "departure_time": "2026-03-15T06:00:00",
    "arrival_time": "2026-03-15T08:15:00",
    "travel_class": "economy",
    "passenger_count": 1,
    "base_fare": 6500.00,
    "taxes": 1000.00,
    "confirmation_number": "ABC123"
  },
  "passenger_details": [...],
  "created_at": "2026-02-05T10:30:00Z",
  "updated_at": "2026-02-05T10:35:00Z"
}
```

---

### PUT `/bookings/{booking_id}/cancel`

Cancel a booking.

**Authentication:** Bearer Token

**Request Body:**
```json
{
  "reason": "Change of plans"
}
```

**Response:** `200 OK`
```json
{
  "booking_id": 1,
  "status": "cancelled",
  "refund_amount": 6000.00,
  "currency": "INR",
  "refund_processing_time": "5-7 business days",
  "cancellation_fee": 1500.00,
  "message": "Your flight booking has been cancelled successfully."
}
```

---

## Payment Endpoints

Base path: `/payments`

### POST `/payments/create-order`

Create a Razorpay order for payment.

**Authentication:** Bearer Token

**Request Body:**
```json
{
  "booking_id": 1,
  "booking_type": "flight",
  "base_amount": 7500.00,
  "payment_method": "card"
}
```

**Response:** `200 OK`
```json
{
  "order_id": "order_ABC123",
  "amount": 788100,
  "currency": "INR",
  "key_id": "rzp_test_xxxxx",
  "receipt": "rcpt_001",
  "convenience_fee": 150.00,
  "gst_amount": 27.00,
  "total_amount": 7677.00
}
```

> **Note:** Amount is in paise (smallest currency unit)

---

### POST `/payments/verify`

Verify payment after Razorpay checkout.

**Authentication:** Bearer Token

**Request Body:**
```json
{
  "razorpay_order_id": "order_ABC123",
  "razorpay_payment_id": "pay_XYZ789",
  "razorpay_signature": "signature_string"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "transaction_id": 1,
  "booking_id": 1,
  "booking_type": "flight",
  "message": "Payment verified successfully"
}
```

---

### POST `/payments/webhook`

Razorpay webhook handler.

**Authentication:** Razorpay Signature (X-Razorpay-Signature header)

**Events Handled:**
- `payment.captured`
- `payment.failed`
- `order.paid`
- `refund.processed`

---

## Wallet Endpoints

Base path: `/wallet`

### GET `/wallet/balance`

Get wallet balance.

**Authentication:** Bearer Token

**Response:** `200 OK`
```json
{
  "balance": 10000.00,
  "hold_amount": 500.00,
  "available_balance": 9500.00,
  "credit_limit": 50000.00,
  "credit_used": 0.00,
  "currency": "INR"
}
```

---

### GET `/wallet/transactions`

Get transaction history.

**Authentication:** Bearer Token

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `page_size` | integer | Items per page (1-100) |
| `type` | string | `credit`, `debit`, `refund` |
| `status` | string | `completed`, `pending`, `failed` |
| `start_date` | datetime | Filter start date |
| `end_date` | datetime | Filter end date |
| `min_amount` | float | Minimum amount |
| `max_amount` | float | Maximum amount |

---

## Holiday Endpoints

Base path: `/holidays`

### GET `/holidays/themes`

Get all holiday themes.

**Authentication:** None

---

### GET `/holidays/destinations`

Get all destinations.

**Authentication:** None

---

### GET `/holidays/packages`

Search holiday packages.

**Authentication:** None

**Query Parameters:**
- `query` - Search text
- `theme_id` - Filter by theme
- `destination_id` - Filter by destination
- `min_nights` / `max_nights` - Duration filter
- `min_price` / `max_price` - Price filter
- `package_type` - Package type filter
- `is_featured` - Featured only
- `sort_by` - `display_order`, `price_asc`, `price_desc`, `rating`, `newest`
- `page` / `page_size` - Pagination

---

## Visa Endpoints

Base path: `/visa`

### GET `/visa/countries`

Get all visa countries.

**Authentication:** None

### GET `/visa/types`

Get visa types (optionally filtered by country).

**Authentication:** None

### POST `/visa/applications`

Submit visa application.

**Authentication:** Bearer Token

---

## Activity Endpoints

Base path: `/activities`

### GET `/activities/categories`

Get activity categories.

**Authentication:** None

### GET `/activities`

Search activities.

**Authentication:** None

### GET `/activities/featured`

Get featured activities.

**Authentication:** None

---

## Transfer Endpoints

Base path: `/transfers`

### GET `/transfers/car-types`

Get available car types.

**Authentication:** None

### GET `/transfers/routes`

Get transfer routes.

**Authentication:** None

### POST `/transfers/estimate-price`

Get price estimate.

**Authentication:** None

**Request Body:**
```json
{
  "car_type_id": 1,
  "trip_type": "one_way",
  "route_id": 1,
  "pickup_date": "2026-03-15",
  "pickup_time": "10:00"
}
```

---

## CMS Endpoints

Base path: `/cms`

### GET `/cms/sliders`

Get active sliders for a placement.

**Authentication:** None

**Query Parameters:**
- `placement` - `homepage`, `flights`, etc.

### GET `/cms/offers`

Get active offers.

**Authentication:** None

### POST `/cms/offers/validate`

Validate a coupon code.

**Authentication:** Bearer Token (optional)

**Request Body:**
```json
{
  "code": "SUMMER20",
  "service_type": "flight",
  "amount": 10000.00
}
```

---

## Dashboard Endpoints

Base path: `/dashboard`

### GET `/dashboard/profile`

Get user profile for dashboard.

**Authentication:** Bearer Token

### PUT `/dashboard/profile`

Update user profile.

**Authentication:** Bearer Token

### GET `/dashboard/bookings`

Get user's booking history.

**Authentication:** Bearer Token

### GET `/dashboard/social-accounts`

Get linked social accounts.

**Authentication:** Bearer Token

---

## API Key Endpoints

Base path: `/api-keys`

### POST `/api-keys/`

Create a new API key.

**Authentication:** Bearer Token

**Request Body:**
```json
{
  "name": "My API Key",
  "scopes": ["search:read", "booking:write"],
  "rate_limit": 100,
  "expires_at": "2027-02-05T00:00:00Z"
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "name": "My API Key",
  "key": "tbk_live_xxxxxxxxxxxxxxxxx",
  "scopes": ["search:read", "booking:write"],
  "rate_limit": 100,
  "is_active": true,
  "created_at": "2026-02-05T10:30:00Z",
  "expires_at": "2027-02-05T00:00:00Z"
}
```

> **Important:** The `key` is only shown once upon creation. Store it securely.

### GET `/api-keys/`

List all API keys.

**Authentication:** Bearer Token

### DELETE `/api-keys/{key_id}`

Revoke an API key.

**Authentication:** Bearer Token

---

## Admin Endpoints

Base path: `/admin`

> **Note:** All admin endpoints require admin role authentication.

### GET `/admin/dashboard/stats`

Get dashboard statistics.

**Response:**
```json
{
  "total_users": 1500,
  "total_bookings": 5000,
  "total_revenue": 25000000.00,
  "pending_agents": 15,
  "today_bookings": 50,
  "monthly_revenue": 5000000.00
}
```

---

### GET `/admin/users`

List all users with filters.

**Query Parameters:**
- `page`, `size` - Pagination
- `role` - `customer`, `agent`, `admin`
- `is_active` - Boolean
- `approval_status` - For agents

---

### PUT `/admin/agents/{agent_id}/approve`

Approve or reject agent application.

**Request Body:**
```json
{
  "approval_status": "approved",
  "rejection_reason": null
}
```

---

### GET `/admin/bookings`

List all bookings with filters.

**Query Parameters:**
- `booking_type` - `flight`, `hotel`, `bus`
- `status` - Booking status
- `payment_status` - Payment status
- `date_from`, `date_to` - Date range

---

## Tenant Endpoints

Base path: `/v1`

### GET `/v1/config/public`

Get public tenant configuration.

**Authentication:** None (Tenant identified by headers)

**Response:**
```json
{
  "tenant_id": 1,
  "code": "travel-corp",
  "brand_name": "Travel Corp",
  "logo_url": "https://...",
  "theme_colors": {
    "primary": "#1E40AF",
    "secondary": "#F59E0B"
  },
  "enabled_modules": {
    "flights": true,
    "hotels": true,
    "buses": true
  },
  "currency": "INR"
}
```

---

## Markup Endpoints

Base path: `/v1/admin/markups`

### POST `/v1/admin/markups`

Create markup rule.

**Authentication:** Admin

**Request Body:**
```json
{
  "name": "International Flight Markup",
  "service_type": "flight",
  "markup_type": "fixed",
  "value": 500,
  "priority": 10,
  "agent_commission_percentage": 20,
  "conditions": {
    "route_type": "international"
  }
}
```

---

## Pricing Endpoints

Base path: `/pricing`

### POST `/pricing/calculate`

Calculate final price with all fees.

**Authentication:** Optional

**Request Body:**
```json
{
  "service_type": "flight",
  "base_fare": 5000.00,
  "taxes": 500.00,
  "user_type": "B2C",
  "payment_mode": "card",
  "discount_code": "SUMMER20"
}
```

**Response:**
```json
{
  "base_fare": 5000.00,
  "taxes": 500.00,
  "total_markup": 250.00,
  "fare_after_markup": 5750.00,
  "total_discount": 500.00,
  "fare_after_discount": 5250.00,
  "convenience_fee": 100.00,
  "convenience_fee_gst": 18.00,
  "total_convenience_fee": 118.00,
  "grand_total": 5368.00,
  "you_save": 500.00
}
```

---

## Settings Endpoints

Base path: `/settings`

### GET `/settings/fees`

Get convenience fee configurations.

**Authentication:** Admin

### POST `/settings/fees/calculate`

Calculate convenience fee.

**Authentication:** None

---

## Company Endpoints

Base path: `/admin/company`

### GET `/admin/company/profile`

Get company profile.

**Authentication:** Admin

### PUT `/admin/company/profile`

Update company profile.

**Authentication:** Admin

### GET `/admin/company/bank-accounts`

List bank accounts.

**Authentication:** Admin

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `204` | No Content |
| `400` | Bad Request - Invalid input |
| `401` | Unauthorized - Invalid/missing token |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found |
| `422` | Validation Error |
| `429` | Too Many Requests - Rate limit exceeded |
| `500` | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Error message describing the issue",
  "path": "/api/endpoint"
}
```

### Validation Error Format

```json
{
  "detail": "Validation error",
  "errors": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ],
  "path": "/auth/register"
}
```

---

## Rate Limiting

Default rate limits:
- **Per User:** 60 requests/minute
- **Per IP:** 1000 requests/hour

Rate limit headers in response:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 55
X-RateLimit-Reset: 1738764860
```

When rate limit exceeded:
```json
{
  "detail": "Rate limit exceeded. Limit: 60 requests/minute"
}
```

---

## Pagination

### Request Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `size` | integer | 20 | Items per page |

### Response Format

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "total_pages": 5,
  "has_next": true,
  "has_prev": false
}
```

---

## SDK Examples

### JavaScript/TypeScript

```javascript
// Login
const response = await fetch('https://api.example.com/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com', password: 'password' })
});
const { access_token } = await response.json();

// Authenticated request
const bookings = await fetch('https://api.example.com/bookings/', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
```

### Python

```python
import requests

# Login
response = requests.post('https://api.example.com/auth/login', json={
    'email': 'user@example.com',
    'password': 'password'
})
access_token = response.json()['access_token']

# Authenticated request
headers = {'Authorization': f'Bearer {access_token}'}
bookings = requests.get('https://api.example.com/bookings/', headers=headers)
```

### cURL

```bash
# Login
curl -X POST https://api.example.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Authenticated request
curl https://api.example.com/bookings/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Changelog

### v1.0.0 (February 2026)
- Initial API release
- Authentication endpoints
- Search endpoints (flights, hotels, buses)
- Booking management
- Payment integration
- Admin panel
- White-label support

---

## Support

For API support or questions:
- Email: api-support@example.com
- Documentation: https://docs.example.com
