# API Key System - Quick Reference Guide

## Overview

The API Key system provides secure, scope-based access control for partner integrations. Keys are JWT-based with SHA256 hashing, Redis caching, and configurable rate limiting.

---

## Features

- ✅ **Scope-based Access**: Control which resources each key can access
- ✅ **Rate Limiting**: Configurable per-key request limits
- ✅ **Security**: SHA256 hashing, prefix-based key generation
- ✅ **Caching**: Redis caching for fast validation (1hr TTL)
- ✅ **Usage Tracking**: Monitor last used time and total requests
- ✅ **Expiration**: Optional expiration dates
- ✅ **Revocation**: Soft delete capability

---

## API Key Scopes

```python
class APIKeyScope(str, Enum):
    ALL = "all"           # Access to all resources
    FLIGHT = "flight"     # Flight search and booking
    HOTEL = "hotel"       # Hotel search and booking
    BUS = "bus"           # Bus search and booking
    PACKAGE = "package"   # Holiday packages
    VISA = "visa"         # Visa services
    ACTIVITY = "activity" # Activity booking
```

---

## Key Format

API keys follow a standardized format:

```
tk_<environment>_<random_string>

Examples:
- tk_live_3a8f9b2c4d5e6f7g8h9i0j  (Production)
- tk_test_1a2b3c4d5e6f7g8h9i0j    (Testing)
- tk_dev_9x8y7z6w5v4u3t2s1r      (Development)
```

**Environment Prefixes:**
- `tk_live_` - Production environment
- `tk_test_` - Testing environment
- `tk_dev_` - Development environment

---

## Creating API Keys

### Endpoint
```http
POST /api-keys
Authorization: Bearer <user_jwt_token>
Content-Type: application/json
```

### Request Body
```json
{
  "name": "Partner Integration XYZ",
  "scopes": ["FLIGHT", "HOTEL"],
  "rate_limit": 5000,
  "expires_at": "2025-12-31T23:59:59"
}
```

### Response
```json
{
  "id": 1,
  "key": "tk_live_3a8f9b2c4d5e6f7g8h9i0j",
  "name": "Partner Integration XYZ",
  "scopes": ["FLIGHT", "HOTEL"],
  "rate_limit": 5000,
  "usage_count": 0,
  "last_used_at": null,
  "expires_at": "2025-12-31T23:59:59",
  "is_active": true,
  "created_at": "2025-01-15T10:00:00",
  "updated_at": "2025-01-15T10:00:00"
}
```

**⚠️ Important:** The plain `key` is only shown once during creation. Store it securely!

---

## Using API Keys

### Authentication Header
```http
X-API-Key: tk_live_3a8f9b2c4d5e6f7g8h9i0j
```

### Example Request
```bash
curl -X POST https://api.example.com/bookings/flights \
  -H "X-API-Key: tk_live_3a8f9b2c4d5e6f7g8h9i0j" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "DEL",
    "destination": "BOM",
    "departure_date": "2025-02-15",
    "passengers": 2
  }'
```

---

## Managing API Keys

### List All Keys
```http
GET /api-keys
Authorization: Bearer <user_jwt_token>
```

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Partner Integration XYZ",
      "scopes": ["FLIGHT", "HOTEL"],
      "rate_limit": 5000,
      "usage_count": 1250,
      "last_used_at": "2025-01-15T12:30:00",
      "is_active": true
    }
  ],
  "total": 1
}
```

### Get Specific Key
```http
GET /api-keys/{id}
Authorization: Bearer <user_jwt_token>
```

### Update Key
```http
PUT /api-keys/{id}
Authorization: Bearer <user_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Updated Partner Name",
  "scopes": ["FLIGHT", "HOTEL", "BUS"],
  "rate_limit": 10000
}
```

### Revoke Key
```http
DELETE /api-keys/{id}
Authorization: Bearer <user_jwt_token>
```

**Response:** `204 No Content`

---

## Rate Limiting

### Default Limits
- **Default Rate Limit:** 1000 requests/hour per key
- **Configurable:** Can be set per key during creation/update

### Rate Limit Headers
```http
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4750
X-RateLimit-Reset: 1705324800
```

### Rate Limit Exceeded Response
```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "reset_at": "2025-01-15T14:00:00"
}
```

**Status Code:** `429 Too Many Requests`

---

## Scope Validation

### Endpoint Protection

Use the `require_api_key_scope` dependency to protect endpoints:

```python
from app.api_keys.api import require_api_key_scope

@router.post("/bookings/flights")
async def create_flight_booking(
    api_key: APIKey = Depends(require_api_key_scope([APIKeyScope.FLIGHT, APIKeyScope.ALL]))
):
    # Only API keys with FLIGHT or ALL scope can access
    pass
```

### Scope Validation Error
```json
{
  "detail": "API key does not have required scope: FLIGHT"
}
```

**Status Code:** `403 Forbidden`

---

## Error Responses

### Invalid API Key
```json
{
  "detail": "Invalid API key"
}
```
**Status Code:** `401 Unauthorized`

### Expired API Key
```json
{
  "detail": "API key has expired"
}
```
**Status Code:** `401 Unauthorized`

### Revoked API Key
```json
{
  "detail": "API key has been revoked"
}
```
**Status Code:** `401 Unauthorized`

### Missing API Key
```json
{
  "detail": "API key required"
}
```
**Status Code:** `401 Unauthorized`

---

## Security Best Practices

### For API Key Creators:
1. ✅ **Store Securely:** Save keys in environment variables or secret managers
2. ✅ **Use Minimal Scopes:** Only grant necessary permissions
3. ✅ **Set Expiration:** Use expiration dates for temporary access
4. ✅ **Rotate Regularly:** Create new keys periodically and revoke old ones
5. ✅ **Monitor Usage:** Track usage_count and last_used_at
6. ✅ **Revoke Compromised Keys:** Immediately revoke if suspected compromise

### For API Key Users:
1. ✅ **Never Log Keys:** Don't log API keys in application logs
2. ✅ **Use HTTPS Only:** Always use HTTPS for API requests
3. ✅ **Handle Errors:** Implement proper error handling for rate limits
4. ✅ **Respect Rate Limits:** Implement backoff strategies
5. ✅ **Monitor Headers:** Check rate limit headers in responses

---

## Usage Tracking

### Metrics Available:
- `usage_count` - Total number of requests made
- `last_used_at` - Timestamp of most recent use
- `created_at` - When the key was created
- `expires_at` - When the key expires (if set)

### Monitoring Example:
```python
# Get API key stats
response = requests.get(
    "https://api.example.com/api-keys/1",
    headers={"Authorization": f"Bearer {jwt_token}"}
)

stats = response.json()
print(f"Usage: {stats['usage_count']} requests")
print(f"Last used: {stats['last_used_at']}")
```

---

## Redis Caching

### Cache Strategy:
- **Cache Key:** `api_key:cache:{key_hash}`
- **TTL:** 1 hour (3600 seconds)
- **Invalidation:** On update/revoke operations

### Benefits:
- ⚡ **Fast Validation:** Sub-millisecond key validation
- 📉 **Reduced DB Load:** 99%+ cache hit rate expected
- 🔄 **Auto Refresh:** Automatic cache invalidation on updates

---

## Integration Examples

### Python (requests)
```python
import requests

API_KEY = "tk_live_3a8f9b2c4d5e6f7g8h9i0j"
BASE_URL = "https://api.example.com"

def search_flights(origin, destination, date):
    response = requests.post(
        f"{BASE_URL}/search/flights",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "origin": origin,
            "destination": destination,
            "departure_date": date
        }
    )
    
    if response.status_code == 429:
        print("Rate limit exceeded!")
        return None
    
    response.raise_for_status()
    return response.json()
```

### Node.js (axios)
```javascript
const axios = require('axios');

const API_KEY = 'tk_live_3a8f9b2c4d5e6f7g8h9i0j';
const BASE_URL = 'https://api.example.com';

async function searchFlights(origin, destination, date) {
  try {
    const response = await axios.post(
      `${BASE_URL}/search/flights`,
      {
        origin,
        destination,
        departure_date: date
      },
      {
        headers: {
          'X-API-Key': API_KEY,
          'Content-Type': 'application/json'
        }
      }
    );
    
    return response.data;
  } catch (error) {
    if (error.response?.status === 429) {
      console.error('Rate limit exceeded!');
    }
    throw error;
  }
}
```

### cURL
```bash
#!/bin/bash

API_KEY="tk_live_3a8f9b2c4d5e6f7g8h9i0j"
BASE_URL="https://api.example.com"

curl -X POST "$BASE_URL/search/flights" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "DEL",
    "destination": "BOM",
    "departure_date": "2025-02-15"
  }'
```

---

## Testing

### Test API Key Creation
```bash
# Create test key
curl -X POST http://localhost:8000/api-keys \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Integration",
    "scopes": ["FLIGHT"],
    "rate_limit": 100
  }'
```

### Test Authentication
```bash
# Use API key
curl -X GET http://localhost:8000/search/flights \
  -H "X-API-Key: tk_test_abc123..."
```

### Test Rate Limiting
```bash
# Make 101 requests to exceed limit
for i in {1..101}; do
  curl -X GET http://localhost:8000/search/flights \
    -H "X-API-Key: tk_test_abc123..."
  echo "Request $i"
done
```

---

## FAQ

### Q: Can I have multiple API keys?
**A:** Yes, each user can create multiple API keys with different scopes and rate limits.

### Q: What happens if I lose my API key?
**A:** You cannot retrieve the plain key. Revoke the lost key and create a new one.

### Q: Can I change the key string?
**A:** No, key strings are immutable. Create a new key and revoke the old one.

### Q: How is rate limiting calculated?
**A:** Per hour, rolling window. Resets at the top of each hour.

### Q: Can I use API keys and JWT together?
**A:** No, use either API key (X-API-Key header) OR JWT (Authorization header), not both.

### Q: Are API keys environment-specific?
**A:** The prefix indicates the intended environment, but technically they work in any environment where the database has the record.

---

## Support

For issues or questions:
- 📧 Email: support@example.com
- 📚 Documentation: https://docs.example.com/api-keys
- 🐛 Bug Reports: https://github.com/example/issues

---

**Last Updated:** 2025-01-15  
**Version:** 1.0.0
