# Delivery Tracking

ChatAPI provides comprehensive delivery tracking for all notification types, allowing you to monitor the status and performance of your messages.

## Tracking Methods

### Real-time Status Updates

All notifications include tracking information that provides real-time status updates:

```json
{
	"id": "notification_123",
	"status": "delivered",
	"tracking": {
		"created_at": "2023-12-01T10:00:00Z",
		"sent_at": "2023-12-01T10:00:01Z",
		"delivered_at": "2023-12-01T10:00:03Z",
		"read_at": null,
		"attempts": 1,
		"provider": "smtp",
		"provider_message_id": "msg_456"
	}
}
```

### Status Types

| Status       | Description                       |
| ------------ | --------------------------------- |
| `pending`    | Notification queued for delivery  |
| `processing` | Being processed by provider       |
| `sent`       | Successfully sent to provider     |
| `delivered`  | Confirmed delivery to recipient   |
| `failed`     | Delivery failed                   |
| `bounced`    | Message bounced back              |
| `read`       | Recipient opened/read the message |

## Webhooks for Tracking

Configure webhooks to receive real-time delivery status updates:

### Setup Webhook Endpoint

```python
# In your webhook handler
@app.post("/webhooks/chatapi/delivery")
async def handle_delivery_webhook(data: dict):
    notification_id = data["notification_id"]
    status = data["status"]
    timestamp = data["timestamp"]

    # Update your application's notification status
    await update_notification_status(notification_id, status, timestamp)

    return {"status": "received"}
```

### Configure Webhook URL

```bash
curl -X POST "https://api.chatapi.dev/v1/webhooks" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://yourapp.com/webhooks/chatapi/delivery",
    "events": ["notification.delivered", "notification.failed", "notification.read"],
    "secret": "your_webhook_secret"
  }'
```

## Query Delivery Status

### Get Notification Status

```bash
curl -X GET "https://api.chatapi.dev/v1/notifications/{notification_id}" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Bulk Status Query

```bash
curl -X POST "https://api.chatapi.dev/v1/notifications/bulk-status" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_ids": ["notif_1", "notif_2", "notif_3"]
  }'
```

## Analytics and Reporting

### Delivery Metrics

Access detailed delivery metrics through the API:

```bash
curl -X GET "https://api.chatapi.dev/v1/analytics/delivery-metrics" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -G -d "start_date=2023-12-01" \
      -d "end_date=2023-12-31" \
      -d "group_by=day"
```

Response:

```json
{
	"metrics": [
		{
			"date": "2023-12-01",
			"sent": 1000,
			"delivered": 950,
			"failed": 30,
			"bounced": 20,
			"delivery_rate": 0.95,
			"avg_delivery_time": 2.3
		}
	]
}
```

### Performance Tracking

Monitor key performance indicators:

- **Delivery Rate**: Percentage of successfully delivered messages
- **Bounce Rate**: Percentage of messages that bounced
- **Average Delivery Time**: Time from sending to delivery
- **Provider Performance**: Comparison across different providers

## Error Handling and Retries

### Automatic Retries

Failed notifications are automatically retried with exponential backoff:

```python
retry_config = {
    "max_attempts": 5,
    "initial_delay": 1,  # seconds
    "max_delay": 300,    # seconds
    "backoff_factor": 2,
    "retry_conditions": [
        "temporary_failure",
        "rate_limit",
        "timeout"
    ]
}
```

### Manual Retry

Force retry of failed notifications:

```bash
curl -X POST "https://api.chatapi.dev/v1/notifications/{notification_id}/retry" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Provider-Specific Tracking

### Email Tracking

Email notifications support additional tracking features:

- **Open Tracking**: Detect when emails are opened
- **Click Tracking**: Track link clicks within emails
- **Unsubscribe Tracking**: Monitor unsubscribe events

### SMS Tracking

SMS notifications provide:

- **Delivery Reports**: Carrier-level delivery confirmation
- **Read Receipts**: When supported by carrier
- **Link Tracking**: For URLs in SMS messages

### Push Notification Tracking

Push notifications offer:

- **Device Registration**: Track device token validity
- **Delivery Status**: Platform-specific delivery confirmation
- **Interaction Tracking**: User engagement with notifications

## Best Practices

### Monitoring Setup

1. **Set up webhooks** for real-time status updates
2. **Monitor delivery rates** and set up alerts for low performance
3. **Track bounces** and maintain clean recipient lists
4. **Analyze provider performance** and optimize routing

### Troubleshooting

Common issues and solutions:

- **High bounce rate**: Verify recipient addresses and list quality
- **Low delivery rate**: Check provider configuration and limits
- **Delayed delivery**: Monitor provider performance and queues
- **Missing tracking**: Verify webhook configuration and endpoints

### Data Retention

Tracking data is retained according to your plan:

- **Free Plan**: 30 days
- **Pro Plan**: 90 days
- **Enterprise Plan**: Custom retention periods

Configure data export for longer-term storage:

```bash
curl -X POST "https://api.chatapi.dev/v1/exports/delivery-data" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "format": "csv",
    "webhook_url": "https://yourapp.com/webhooks/export-complete"
  }'
```
