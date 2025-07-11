# Email Providers

ChatAPI supports multiple email providers for sending notifications. Configure your preferred provider to send branded, reliable emails to your users.

## Overview

Email providers in ChatAPI:

- **Client-specific configuration** - Each client can configure their own providers
- **Multiple provider support** - SMTP, Mailgun, SendGrid, Postmark, Amazon SES
- **Automatic provider selection** - SMTP for transactional, bulk providers for multiple recipients
- **No environment dependencies** - All configuration is client-supplied and stored securely
- **Provider validation** - Test and validate configurations before use

## Supported Providers

### SMTP

Direct SMTP connection for maximum control and customization.

**Best for:** Custom email servers, enterprise environments, full control over delivery

**Configuration:**

```json
{
	"provider": "smtp",
	"config": {
		"host": "smtp.gmail.com",
		"port": 587,
		"username": "noreply@yourcompany.com",
		"password": "your-app-password",
		"use_tls": true,
		"from_email": "noreply@yourcompany.com",
		"from_name": "Your Company"
	}
}
```

### Mailgun

Popular email service with excellent deliverability and analytics.

**Best for:** High-volume sending, detailed analytics, European customers

**Configuration:**

```json
{
	"provider": "mailgun",
	"config": {
		"api_key": "key-1234567890abcdef1234567890abcdef",
		"domain": "mg.yourcompany.com",
		"from_email": "noreply@yourcompany.com",
		"from_name": "Your Company"
	}
}
```

### SendGrid

Comprehensive email platform with templates and marketing features.

**Best for:** Marketing emails, template management, A/B testing

**Configuration:**

```json
{
	"provider": "sendgrid",
	"config": {
		"api_key": "SG.1234567890abcdef1234567890abcdef.1234567890abcdef1234567890abcdef1234567890ab",
		"from_email": "noreply@yourcompany.com",
		"from_name": "Your Company"
	}
}
```

### Postmark

Focused on transactional emails with fast delivery and excellent support.

**Best for:** Transactional emails, fast delivery, detailed bounce tracking

**Configuration:**

```json
{
	"provider": "postmark",
	"config": {
		"server_token": "12345678-1234-1234-1234-123456789012",
		"from_email": "noreply@yourcompany.com",
		"from_name": "Your Company"
	}
}
```

### Amazon SES

Amazon's email service integrated with AWS ecosystem.

**Best for:** AWS environments, cost-effective high volume, programmatic sending

**Configuration:**

```json
{
	"provider": "ses",
	"config": {
		"aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
		"aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
		"region": "us-east-1",
		"from_email": "noreply@yourcompany.com",
		"from_name": "Your Company"
	}
}
```

## Provider Selection Logic

ChatAPI automatically selects the appropriate provider based on the number of recipients:

### Single Recipient (Transactional)

- **SMTP** is used for single recipient emails
- Provides direct control and immediate delivery
- Best for password resets, confirmations, alerts

### Multiple Recipients (Bulk)

- **Bulk providers** (Mailgun, SendGrid, Postmark, SES) are used for 2+ recipients
- Optimized for higher volume and better deliverability
- Best for newsletters, notifications to groups

### Fallback Strategy

If the preferred provider fails:

1. Attempt delivery with configured provider
2. Log the failure with details
3. Notify client about delivery failure
4. No automatic fallback to other providers (client responsibility)

## Configuration Management

### Set Email Provider

Configure your email provider for the authenticated client:

```http
POST /api/v1/clients/email-config
```

**Request Body (SMTP):**

```json
{
	"provider": "smtp",
	"config": {
		"host": "smtp.gmail.com",
		"port": 587,
		"username": "noreply@yourcompany.com",
		"password": "your-app-password",
		"use_tls": true,
		"from_email": "noreply@yourcompany.com",
		"from_name": "Your Company"
	}
}
```

**Response:**

```json
{
	"data": {
		"provider": "smtp",
		"config": {
			"host": "smtp.gmail.com",
			"port": 587,
			"username": "noreply@yourcompany.com",
			"use_tls": true,
			"from_email": "noreply@yourcompany.com",
			"from_name": "Your Company"
		}
	},
	"message": "Email configuration saved successfully",
	"status": "success"
}
```

### Get Current Configuration

```http
GET /api/v1/clients/email-config
```

**Response:**

```json
{
	"data": {
		"provider": "smtp",
		"config": {
			"host": "smtp.gmail.com",
			"port": 587,
			"username": "noreply@yourcompany.com",
			"use_tls": true,
			"from_email": "noreply@yourcompany.com",
			"from_name": "Your Company"
		},
		"created_at": "2024-01-01T12:00:00Z",
		"updated_at": "2024-01-01T12:00:00Z"
	},
	"status": "success"
}
```

### Update Configuration

```http
PUT /api/v1/clients/email-config
```

Use the same request format as setting the configuration.

### Remove Configuration

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

### Test Configuration

Validate your email configuration by sending a test email:

```http
POST /api/v1/clients/email-config/test
```

**Request Body:**

```json
{
	"to_email": "test@yourcompany.com",
	"subject": "ChatAPI Email Test",
	"content": "This is a test email to verify your email configuration."
}
```

**Response:**

```json
{
	"data": {
		"test_successful": true,
		"message_id": "test_12345",
		"delivery_time": 1.23,
		"provider_response": "250 2.0.0 OK"
	},
	"message": "Test email sent successfully",
	"status": "success"
}
```

## Provider-Specific Setup

### SMTP Setup

#### Gmail Configuration

```json
{
	"provider": "smtp",
	"config": {
		"host": "smtp.gmail.com",
		"port": 587,
		"username": "your-email@gmail.com",
		"password": "your-app-password",
		"use_tls": true,
		"from_email": "your-email@gmail.com",
		"from_name": "Your App Name"
	}
}
```

!!! note "Gmail App Passwords"
Use [App Passwords](https://support.google.com/accounts/answer/185833) instead of your regular Gmail password for better security.

#### Office 365 Configuration

```json
{
	"provider": "smtp",
	"config": {
		"host": "smtp.office365.com",
		"port": 587,
		"username": "noreply@yourcompany.com",
		"password": "your-password",
		"use_tls": true,
		"from_email": "noreply@yourcompany.com",
		"from_name": "Your Company"
	}
}
```

#### Custom SMTP Server

```json
{
	"provider": "smtp",
	"config": {
		"host": "mail.yourcompany.com",
		"port": 465,
		"username": "noreply@yourcompany.com",
		"password": "your-password",
		"use_tls": false,
		"use_ssl": true,
		"from_email": "noreply@yourcompany.com",
		"from_name": "Your Company"
	}
}
```

### Mailgun Setup

1. **Create Mailgun Account** at [mailgun.com](https://mailgun.com)
2. **Add and verify your domain**
3. **Get your API key** from the dashboard
4. **Configure DNS records** for better deliverability

```json
{
	"provider": "mailgun",
	"config": {
		"api_key": "key-1234567890abcdef1234567890abcdef",
		"domain": "mg.yourcompany.com",
		"from_email": "noreply@yourcompany.com",
		"from_name": "Your Company"
	}
}
```

### SendGrid Setup

1. **Create SendGrid Account** at [sendgrid.com](https://sendgrid.com)
2. **Create an API Key** with full access or mail send permissions
3. **Verify your sender identity** (domain or single sender)
4. **Configure authentication** (SPF, DKIM, DMARC)

```json
{
	"provider": "sendgrid",
	"config": {
		"api_key": "SG.1234567890abcdef1234567890abcdef.1234567890abcdef1234567890abcdef1234567890ab",
		"from_email": "noreply@yourcompany.com",
		"from_name": "Your Company"
	}
}
```

### Postmark Setup

1. **Create Postmark Account** at [postmarkapp.com](https://postmarkapp.com)
2. **Create a Server** for transactional emails
3. **Get your Server Token** from server settings
4. **Verify your sender signature** or domain

```json
{
	"provider": "postmark",
	"config": {
		"server_token": "12345678-1234-1234-1234-123456789012",
		"from_email": "noreply@yourcompany.com",
		"from_name": "Your Company"
	}
}
```

### Amazon SES Setup

1. **Create AWS Account** and enable SES
2. **Verify your domain** or email address
3. **Create IAM user** with SES sending permissions
4. **Request production access** (remove sandbox limits)

```json
{
	"provider": "ses",
	"config": {
		"aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
		"aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
		"region": "us-east-1",
		"from_email": "noreply@yourcompany.com",
		"from_name": "Your Company"
	}
}
```

#### Required IAM Permissions

```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": ["ses:SendEmail", "ses:SendRawEmail"],
			"Resource": "*"
		}
	]
}
```

## Advanced Configuration

### HTML Email Support

All providers support HTML emails with automatic fallback to plain text:

```json
{
	"type": "email",
	"recipients": ["user@example.com"],
	"subject": "Welcome to Our Platform",
	"content": "Plain text content for email clients that don't support HTML",
	"meta": {
		"html_content": "<h1>Welcome!</h1><p>Thank you for joining our platform!</p>",
		"attachments": [
			{
				"filename": "welcome.pdf",
				"url": "https://yourcompany.com/files/welcome.pdf",
				"content_type": "application/pdf"
			}
		]
	}
}
```

### Custom Headers

Add custom headers for tracking and identification:

```json
{
	"meta": {
		"custom_headers": {
			"X-Campaign-ID": "welcome-series-01",
			"X-User-ID": "user_123",
			"X-Message-Type": "transactional"
		}
	}
}
```

### Reply-To Configuration

Set different reply-to addresses:

```json
{
	"provider": "smtp",
	"config": {
		"host": "smtp.gmail.com",
		"port": 587,
		"username": "noreply@yourcompany.com",
		"password": "your-app-password",
		"use_tls": true,
		"from_email": "noreply@yourcompany.com",
		"from_name": "Your Company",
		"reply_to": "support@yourcompany.com"
	}
}
```

## Deliverability Best Practices

### Domain Authentication

Set up proper domain authentication for better deliverability:

#### SPF Record

```
v=spf1 include:_spf.google.com include:mailgun.org include:sendgrid.net ~all
```

#### DKIM Signing

Most providers handle DKIM automatically when you verify your domain.

#### DMARC Policy

```
v=DMARC1; p=none; rua=mailto:dmarc@yourcompany.com
```

### Content Guidelines

1. **Avoid spam triggers** - Don't use excessive caps, exclamation marks, or spam keywords
2. **Include text version** - Always provide plain text alternative to HTML
3. **Use meaningful subject lines** - Clear, descriptive subjects improve engagement
4. **Include unsubscribe links** - Required for compliance and better reputation

### Monitoring and Maintenance

1. **Monitor bounce rates** - High bounce rates can hurt your sender reputation
2. **Track engagement metrics** - Open rates, click rates, and unsubscribes
3. **Maintain clean lists** - Remove invalid and unengaged email addresses
4. **Rotate sending IPs** - Some providers offer IP rotation for better deliverability

## Troubleshooting

### Common Issues

#### SMTP Authentication Failed

```json
{
	"error": {
		"code": "SMTP_AUTH_FAILED",
		"message": "SMTP authentication failed",
		"details": {
			"smtp_response": "535 5.7.8 Username and Password not accepted"
		}
	}
}
```

**Solutions:**

- Verify username and password
- Check if 2FA is enabled (use app passwords)
- Ensure SMTP access is enabled for the account

#### API Key Invalid

```json
{
	"error": {
		"code": "INVALID_API_KEY",
		"message": "Provider API key is invalid or expired",
		"details": {
			"provider": "sendgrid",
			"response": "The provided authorization grant is invalid"
		}
	}
}
```

**Solutions:**

- Regenerate API key in provider dashboard
- Check API key permissions
- Verify the key is correctly copied

#### Domain Not Verified

```json
{
	"error": {
		"code": "DOMAIN_NOT_VERIFIED",
		"message": "Sender domain is not verified with the email provider",
		"details": {
			"domain": "yourcompany.com",
			"provider": "mailgun"
		}
	}
}
```

**Solutions:**

- Complete domain verification process
- Check DNS records are properly configured
- Wait for DNS propagation (up to 48 hours)

#### Rate Limit Exceeded

```json
{
	"error": {
		"code": "RATE_LIMIT_EXCEEDED",
		"message": "Email sending rate limit exceeded",
		"details": {
			"retry_after": 3600,
			"daily_limit": 100,
			"sent_today": 100
		}
	}
}
```

**Solutions:**

- Upgrade your provider plan
- Spread sending over longer time periods
- Implement queuing and retry logic

## Examples

### Complete Provider Setup

```bash
# 1. Configure SMTP provider
curl -X POST "http://localhost:8000/api/v1/clients/email-config" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "provider": "smtp",
    "config": {
      "host": "smtp.gmail.com",
      "port": 587,
      "username": "noreply@yourcompany.com",
      "password": "your-app-password",
      "use_tls": true,
      "from_email": "noreply@yourcompany.com",
      "from_name": "Your Company"
    }
  }'

# 2. Test the configuration
curl -X POST "http://localhost:8000/api/v1/clients/email-config/test" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "to_email": "test@yourcompany.com",
    "subject": "ChatAPI Configuration Test",
    "content": "Your email configuration is working correctly!"
  }'

# 3. Send your first notification
curl -X POST "http://localhost:8000/api/v1/notifications/" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "type": "email",
    "recipients": ["user@example.com"],
    "subject": "Welcome to Our Platform",
    "content": "Thank you for joining our platform!",
    "meta": {
      "html_content": "<h1>Welcome!</h1><p>Thank you for joining our platform!</p>"
    }
  }'
```

### Switch to SendGrid

```bash
# Update to use SendGrid instead
curl -X PUT "http://localhost:8000/api/v1/clients/email-config" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "provider": "sendgrid",
    "config": {
      "api_key": "SG.your-sendgrid-api-key",
      "from_email": "noreply@yourcompany.com",
      "from_name": "Your Company"
    }
  }'
```

## Next Steps

- [Provider Configuration](provider-configuration.md) - Advanced provider settings
- [Delivery Tracking](delivery-tracking.md) - Monitor email delivery success
- [Notifications API](../api/notifications.md) - Send email notifications
