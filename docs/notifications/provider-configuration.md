# Provider Configuration

This guide covers advanced configuration options for email providers in ChatAPI, including authentication, rate limiting, and provider-specific optimizations.

## Configuration Structure

All email provider configurations follow a consistent structure:

```json
{
	"provider": "provider_name",
	"config": {
		// Provider-specific configuration
	},
	"options": {
		// Optional settings
		"rate_limit": 100,
		"timeout": 30,
		"retry_attempts": 3
	}
}
```

## Provider-Specific Configuration

### SMTP Configuration

SMTP is the most flexible provider, supporting any SMTP-compatible email service.

#### Basic Configuration

```json
{
	"provider": "smtp",
	"config": {
		"host": "smtp.example.com",
		"port": 587,
		"username": "user@example.com",
		"password": "password",
		"use_tls": true,
		"from_email": "noreply@example.com",
		"from_name": "Example Service"
	}
}
```

#### Advanced SMTP Options

```json
{
	"provider": "smtp",
	"config": {
		"host": "smtp.example.com",
		"port": 465,
		"username": "user@example.com",
		"password": "password",
		"use_tls": false,
		"use_ssl": true,
		"timeout": 30,
		"local_hostname": "localhost",
		"debug_level": 0,
		"from_email": "noreply@example.com",
		"from_name": "Example Service",
		"reply_to": "support@example.com",
		"return_path": "bounces@example.com"
	},
	"options": {
		"rate_limit": 50,
		"connection_pool_size": 5,
		"retry_attempts": 3,
		"retry_delay": 5
	}
}
```

#### Common SMTP Providers

**Gmail:**

```json
{
	"host": "smtp.gmail.com",
	"port": 587,
	"use_tls": true,
	"username": "your-email@gmail.com",
	"password": "app-password"
}
```

**Outlook/Office 365:**

```json
{
	"host": "smtp.office365.com",
	"port": 587,
	"use_tls": true,
	"username": "your-email@outlook.com",
	"password": "your-password"
}
```

**Yahoo:**

```json
{
	"host": "smtp.mail.yahoo.com",
	"port": 587,
	"use_tls": true,
	"username": "your-email@yahoo.com",
	"password": "app-password"
}
```

### Mailgun Configuration

Mailgun offers excellent deliverability with detailed analytics.

#### Basic Configuration

```json
{
	"provider": "mailgun",
	"config": {
		"api_key": "key-your-api-key",
		"domain": "mg.yourdomain.com",
		"from_email": "noreply@yourdomain.com",
		"from_name": "Your Service"
	}
}
```

#### Advanced Mailgun Options

```json
{
	"provider": "mailgun",
	"config": {
		"api_key": "key-your-api-key",
		"domain": "mg.yourdomain.com",
		"region": "us",
		"from_email": "noreply@yourdomain.com",
		"from_name": "Your Service",
		"reply_to": "support@yourdomain.com",
		"tracking": {
			"opens": true,
			"clicks": true,
			"unsubscribes": true
		},
		"tags": ["chatapi", "notifications"],
		"custom_variables": {
			"environment": "production"
		}
	},
	"options": {
		"rate_limit": 1000,
		"timeout": 30,
		"retry_attempts": 3
	}
}
```

### SendGrid Configuration

SendGrid provides comprehensive email marketing and transactional features.

#### Basic Configuration

```json
{
	"provider": "sendgrid",
	"config": {
		"api_key": "SG.your-api-key",
		"from_email": "noreply@yourdomain.com",
		"from_name": "Your Service"
	}
}
```

#### Advanced SendGrid Options

```json
{
	"provider": "sendgrid",
	"config": {
		"api_key": "SG.your-api-key",
		"from_email": "noreply@yourdomain.com",
		"from_name": "Your Service",
		"reply_to": "support@yourdomain.com",
		"template_id": "d-1234567890abcdef",
		"categories": ["chatapi", "notifications"],
		"custom_args": {
			"environment": "production",
			"service": "chatapi"
		},
		"tracking_settings": {
			"click_tracking": {
				"enable": true,
				"enable_text": false
			},
			"open_tracking": {
				"enable": true,
				"substitution_tag": "%open_track%"
			},
			"subscription_tracking": {
				"enable": true,
				"text": "Unsubscribe",
				"html": "<a href=\"%unsubscribe%\">Unsubscribe</a>"
			}
		}
	}
}
```

### Postmark Configuration

Postmark specializes in transactional emails with fast delivery.

#### Basic Configuration

```json
{
	"provider": "postmark",
	"config": {
		"server_token": "your-server-token",
		"from_email": "noreply@yourdomain.com",
		"from_name": "Your Service"
	}
}
```

#### Advanced Postmark Options

```json
{
	"provider": "postmark",
	"config": {
		"server_token": "your-server-token",
		"from_email": "noreply@yourdomain.com",
		"from_name": "Your Service",
		"reply_to": "support@yourdomain.com",
		"track_opens": true,
		"track_links": "HtmlOnly",
		"message_stream": "outbound",
		"tag": "chatapi-notifications",
		"metadata": {
			"environment": "production",
			"service": "chatapi"
		}
	},
	"options": {
		"rate_limit": 300,
		"timeout": 30
	}
}
```

### Amazon SES Configuration

AWS Simple Email Service integrated with the Amazon ecosystem.

#### Basic Configuration

```json
{
	"provider": "ses",
	"config": {
		"aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
		"aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
		"region": "us-east-1",
		"from_email": "noreply@yourdomain.com",
		"from_name": "Your Service"
	}
}
```

#### Advanced SES Options

```json
{
	"provider": "ses",
	"config": {
		"aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
		"aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
		"region": "us-east-1",
		"from_email": "noreply@yourdomain.com",
		"from_name": "Your Service",
		"reply_to": "support@yourdomain.com",
		"return_path": "bounces@yourdomain.com",
		"configuration_set": "chatapi-config",
		"tags": [
			{
				"Name": "Service",
				"Value": "ChatAPI"
			},
			{
				"Name": "Environment",
				"Value": "Production"
			}
		]
	},
	"options": {
		"rate_limit": 200,
		"timeout": 60,
		"max_send_rate": 14
	}
}
```

## Rate Limiting

### Per-Provider Limits

Configure rate limits to stay within provider restrictions:

```json
{
	"options": {
		"rate_limit": 100,
		"rate_limit_window": 3600,
		"burst_limit": 10,
		"queue_on_limit": true
	}
}
```

### Adaptive Rate Limiting

Automatically adjust rates based on provider responses:

```json
{
	"options": {
		"adaptive_rate_limiting": true,
		"min_rate_limit": 10,
		"max_rate_limit": 1000,
		"rate_adjustment_factor": 0.1
	}
}
```

## Failover and Load Balancing

### Multiple Provider Configuration

Configure multiple providers for failover:

```json
{
	"primary_provider": {
		"provider": "sendgrid",
		"config": {
			/* SendGrid config */
		}
	},
	"fallback_providers": [
		{
			"provider": "mailgun",
			"config": {
				/* Mailgun config */
			}
		},
		{
			"provider": "smtp",
			"config": {
				/* SMTP config */
			}
		}
	],
	"failover_policy": {
		"max_retries": 3,
		"retry_delay": 5,
		"circuit_breaker": {
			"failure_threshold": 5,
			"recovery_timeout": 300
		}
	}
}
```

### Load Balancing Strategies

Distribute load across multiple providers:

```json
{
	"load_balancing": {
		"strategy": "round_robin",
		"providers": [
			{
				"provider": "sendgrid",
				"weight": 60,
				"config": {
					/* config */
				}
			},
			{
				"provider": "mailgun",
				"weight": 40,
				"config": {
					/* config */
				}
			}
		]
	}
}
```

Available strategies:

- `round_robin`: Distribute evenly
- `weighted`: Use provider weights
- `least_connections`: Use provider with fewest active connections
- `response_time`: Use fastest responding provider

## Security Configuration

### Encryption

Configure TLS/SSL settings:

```json
{
	"security": {
		"tls_version": "TLSv1.2",
		"verify_certificates": true,
		"certificate_path": "/path/to/cert.pem",
		"private_key_path": "/path/to/key.pem"
	}
}
```

### Authentication

Secure credential storage:

```json
{
	"authentication": {
		"type": "oauth2",
		"client_id": "your-client-id",
		"client_secret": "your-client-secret",
		"refresh_token": "your-refresh-token",
		"token_url": "https://oauth.provider.com/token"
	}
}
```

### IP Restrictions

Limit connections to specific IP ranges:

```json
{
	"security": {
		"allowed_ips": ["192.168.1.0/24", "10.0.0.0/8"],
		"blocked_ips": ["203.0.113.0/24"]
	}
}
```

## Performance Optimization

### Connection Pooling

Configure connection pools for better performance:

```json
{
	"performance": {
		"connection_pool": {
			"max_connections": 10,
			"max_idle_connections": 5,
			"connection_timeout": 30,
			"idle_timeout": 300
		}
	}
}
```

### Caching

Cache provider responses and configurations:

```json
{
	"caching": {
		"enable_response_caching": true,
		"cache_ttl": 3600,
		"cache_key_prefix": "chatapi:email:",
		"cache_provider": "redis"
	}
}
```

### Batch Processing

Configure batch sending for improved throughput:

```json
{
	"batch_processing": {
		"enabled": true,
		"batch_size": 100,
		"batch_timeout": 30,
		"max_batches_per_second": 10
	}
}
```

## Monitoring and Alerting

### Health Checks

Configure provider health monitoring:

```json
{
	"monitoring": {
		"health_check": {
			"enabled": true,
			"interval": 300,
			"timeout": 10,
			"failure_threshold": 3
		}
	}
}
```

### Metrics Collection

Track provider performance:

```json
{
	"metrics": {
		"enabled": true,
		"track_delivery_time": true,
		"track_error_rates": true,
		"track_throughput": true,
		"export_interval": 60
	}
}
```

### Alerting

Configure alerts for provider issues:

```json
{
	"alerting": {
		"error_rate_threshold": 0.05,
		"response_time_threshold": 5000,
		"queue_size_threshold": 1000,
		"notification_channels": [
			{
				"type": "email",
				"recipients": ["admin@yourdomain.com"]
			},
			{
				"type": "webhook",
				"url": "https://hooks.slack.com/your-webhook"
			}
		]
	}
}
```

## Testing Configuration

### Test Mode

Enable test mode for safe configuration testing:

```json
{
	"test_mode": {
		"enabled": true,
		"test_email": "test@yourdomain.com",
		"skip_delivery": false,
		"log_only": false
	}
}
```

### Validation

Validate configurations before applying:

```json
{
	"validation": {
		"validate_credentials": true,
		"test_connection": true,
		"send_test_email": true,
		"verify_domain": true
	}
}
```

## Environment-Specific Configuration

### Development

```json
{
	"environment": "development",
	"provider": "smtp",
	"config": {
		"host": "localhost",
		"port": 1025,
		"use_tls": false,
		"from_email": "dev@localhost"
	},
	"options": {
		"rate_limit": 10,
		"timeout": 5
	}
}
```

### Staging

```json
{
	"environment": "staging",
	"provider": "sendgrid",
	"config": {
		"api_key": "SG.staging-key",
		"from_email": "staging@yourdomain.com"
	},
	"test_mode": {
		"enabled": true,
		"test_email": "staging-test@yourdomain.com"
	}
}
```

### Production

```json
{
	"environment": "production",
	"provider": "sendgrid",
	"config": {
		"api_key": "SG.production-key",
		"from_email": "noreply@yourdomain.com"
	},
	"monitoring": {
		"health_check": {
			"enabled": true,
			"interval": 60
		}
	},
	"alerting": {
		"error_rate_threshold": 0.01
	}
}
```

## Best Practices

### Configuration Management

1. **Use environment variables** for sensitive data
2. **Version control configurations** (excluding secrets)
3. **Implement configuration validation**
4. **Use separate configs per environment**
5. **Regular configuration audits**

### Security

1. **Rotate credentials regularly**
2. **Use least privilege access**
3. **Monitor for unauthorized changes**
4. **Encrypt sensitive configuration data**
5. **Implement access logging**

### Performance

1. **Monitor provider response times**
2. **Implement proper timeouts**
3. **Use connection pooling**
4. **Configure appropriate rate limits**
5. **Regular performance testing**

### Reliability

1. **Configure multiple providers**
2. **Implement circuit breakers**
3. **Set up proper monitoring**
4. **Test failover scenarios**
5. **Regular backup of configurations**
