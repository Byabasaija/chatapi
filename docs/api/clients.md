# Client Management

Client management is the foundation of ChatAPI. Each client represents an application or service that uses ChatAPI for messaging and notifications.

## Overview

Clients in ChatAPI are:

- **Applications** that use the messaging service
- **Authenticated** with unique API keys
- **Isolated** from each other's data
- **Configurable** with custom email providers

## Client Model

A client has the following properties:

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "api_key": "string",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "email_config": {
    "provider": "smtp|mailgun|sendgrid|postmark|ses",
    "config": {...}
  }
}
```

## API Endpoints

### Create Client

Creates a new client application.

```http
POST /api/v1/clients/
```

**Request Body:**

```json
{
	"name": "My Application",
	"description": "Mobile app for customer support"
}
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440000",
		"name": "My Application",
		"description": "Mobile app for customer support",
		"api_key": "sk_test_1234567890abcdef",
		"is_active": true,
		"created_at": "2024-01-01T00:00:00Z",
		"updated_at": "2024-01-01T00:00:00Z",
		"email_config": null
	},
	"status": "success"
}
```

### Get Client Details

Retrieves current client information.

```http
GET /api/v1/clients/me
```

**Headers:**

```
X-API-Key: sk_test_1234567890abcdef
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440000",
		"name": "My Application",
		"description": "Mobile app for customer support",
		"is_active": true,
		"created_at": "2024-01-01T00:00:00Z",
		"updated_at": "2024-01-01T00:00:00Z",
		"email_config": {
			"provider": "smtp",
			"config": {
				"host": "smtp.example.com",
				"port": 587,
				"username": "noreply@example.com",
				"use_tls": true
			}
		}
	},
	"status": "success"
}
```

### Update Client

Updates client information.

```http
PUT /api/v1/clients/me
```

**Request Body:**

```json
{
	"name": "Updated Application Name",
	"description": "Updated description"
}
```

**Response:**

```json
{
	"data": {
		"id": "550e8400-e29b-41d4-a716-446655440000",
		"name": "Updated Application Name",
		"description": "Updated description",
		"is_active": true,
		"created_at": "2024-01-01T00:00:00Z",
		"updated_at": "2024-01-01T12:00:00Z",
		"email_config": null
	},
	"status": "success"
}
```

### Delete Client

Permanently deletes a client and all associated data.

```http
DELETE /api/v1/clients/me
```

**Response:**

```json
{
	"message": "Client deleted successfully",
	"status": "success"
}
```

!!! warning "Data Loss Warning"
Deleting a client will permanently remove all associated rooms, messages, notifications, and configurations. This action cannot be undone.

## Email Provider Configuration

Clients can configure their own email providers for sending notifications.

### Set Email Provider

```http
POST /api/v1/clients/email-config
```

**SMTP Configuration:**

```json
{
	"provider": "smtp",
	"config": {
		"host": "smtp.example.com",
		"port": 587,
		"username": "noreply@example.com",
		"password": "your-password",
		"use_tls": true,
		"from_email": "noreply@example.com",
		"from_name": "My Application"
	}
}
```

**Mailgun Configuration:**

```json
{
	"provider": "mailgun",
	"config": {
		"api_key": "key-1234567890abcdef",
		"domain": "mg.example.com",
		"from_email": "noreply@example.com",
		"from_name": "My Application"
	}
}
```

**SendGrid Configuration:**

```json
{
	"provider": "sendgrid",
	"config": {
		"api_key": "SG.1234567890abcdef",
		"from_email": "noreply@example.com",
		"from_name": "My Application"
	}
}
```

### Get Email Configuration

```http
GET /api/v1/clients/email-config
```

**Response:**

```json
{
	"data": {
		"provider": "smtp",
		"config": {
			"host": "smtp.example.com",
			"port": 587,
			"username": "noreply@example.com",
			"use_tls": true,
			"from_email": "noreply@example.com",
			"from_name": "My Application"
		}
	},
	"status": "success"
}
```

### Update Email Configuration

```http
PUT /api/v1/clients/email-config
```

Use the same request format as setting the configuration.

### Remove Email Configuration

```http
DELETE /api/v1/clients/email-config
```

**Response:**

```json
{
	"message": "Email configuration removed successfully",
	"status": "success"
}
```

## API Key Management

### Regenerate API Key

For security, you can regenerate your API key:

```http
POST /api/v1/clients/regenerate-key
```

**Response:**

```json
{
	"data": {
		"api_key": "sk_test_new1234567890abcdef"
	},
	"message": "API key regenerated successfully",
	"status": "success"
}
```

!!! warning "API Key Security" - Store API keys securely - Regenerate keys if compromised - Use different keys for development and production - Never commit API keys to version control

## Best Practices

### Client Setup

1. **Use descriptive names** - Make it easy to identify clients
2. **Set up email providers** - Configure before sending notifications
3. **Test configurations** - Validate email settings before production
4. **Monitor usage** - Keep track of API usage and limits

### Security

1. **Rotate API keys regularly** - Especially after team changes
2. **Use environment variables** - Never hardcode API keys
3. **Restrict access** - Only share keys with authorized team members
4. **Monitor logs** - Watch for unusual API activity

### Development vs Production

1. **Separate clients** - Use different clients for different environments
2. **Test email providers** - Use test modes when available
3. **Monitor rate limits** - Be aware of provider-specific limits

## Error Handling

Common errors when managing clients:

### Invalid Email Configuration

```json
{
	"error": {
		"code": "INVALID_EMAIL_CONFIG",
		"message": "Invalid SMTP configuration",
		"details": {
			"field": "host",
			"error": "Invalid hostname"
		}
	},
	"status": "error"
}
```

### Client Not Found

```json
{
	"error": {
		"code": "CLIENT_NOT_FOUND",
		"message": "Client not found"
	},
	"status": "error"
}
```

### Duplicate Client Name

```json
{
	"error": {
		"code": "DUPLICATE_CLIENT_NAME",
		"message": "Client name already exists"
	},
	"status": "error"
}
```

## Examples

### Complete Client Setup

```bash
# 1. Create client
curl -X POST "http://localhost:8000/api/v1/clients/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Mobile App",
    "description": "iOS and Android customer support app"
  }'

# 2. Configure email provider
curl -X POST "http://localhost:8000/api/v1/clients/email-config" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_test_1234567890abcdef" \
  -d '{
    "provider": "smtp",
    "config": {
      "host": "smtp.gmail.com",
      "port": 587,
      "username": "noreply@myapp.com",
      "password": "app-password",
      "use_tls": true,
      "from_email": "noreply@myapp.com",
      "from_name": "My Mobile App"
    }
  }'

# 3. Test configuration
curl -X GET "http://localhost:8000/api/v1/clients/me" \
  -H "X-API-Key: sk_test_1234567890abcdef"
```

## Next Steps

- [Room Management](rooms.md) - Create rooms for organizing conversations
- [Messages](messages.md) - Send and receive messages
- [Notifications](notifications.md) - Set up email notifications
- [Email Providers](../notifications/email-providers.md) - Learn about supported providers
