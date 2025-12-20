---
title: "API Reference"
weight: 20
---

# API Reference

ChatAPI provides both REST and WebS### SDKs and Libraries

**Coming Soon**: Official SDKs for popular languages APIs for building chat applications. All APIs require authentication via API keys and support multi-tenant operation.

## Authentication

All API requests require authentication headers:

```
X-API-Key: <your-tenant-api-key>
X-User-Id: <user-identifier>
```

- **X-API-Key**: Identifies your tenant (organization)
- **X-User-Id**: Identifies the user performing the action

**Admin Operations**: System administration endpoints require:

```
X-Master-Key: <your-master-api-key>
```

- **X-Master-Key**: Master key for tenant creation and admin operations

## API Overview

ChatAPI provides both REST and WebSocket APIs for building chat applications. All APIs require authentication and return JSON responses.

### REST API

Traditional HTTP endpoints for chat operations:

- **Rooms**: Create, list, and manage chat rooms
- **Messages**: Send and retrieve messages
- **Delivery**: Acknowledge message delivery
- **Notifications**: Send notifications to users
- **Admin**: Tenant management and system administration
- **Health**: Service health monitoring

### WebSocket API

Real-time bidirectional communication:

- **Connection**: Persistent WebSocket connections
- **Events**: Real-time message delivery
- **Presence**: User online/offline status
- **Typing**: Typing indicators
- **ACKs**: Message acknowledgments

## Base URL

```
https://your-chatapi-instance.com
```

## Response Format

All API responses use JSON format:

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

Error responses:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters"
  }
}
```

## Rate Limiting

ChatAPI implements per-tenant rate limiting:

- **Default**: 100 requests per second per tenant
- **Headers**: Rate limit status included in responses
- **429 Status**: Returned when limits exceeded

## Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Invalid request parameters |
| `AUTHENTICATION_ERROR` | Invalid or missing API key |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `RATE_LIMIT_EXCEEDED` | Rate limit exceeded |
| `INTERNAL_ERROR` | Server internal error |

## SDKs and Libraries

{{< hint info >}}
**Coming Soon**: Official SDKs for popular languages
{{< /hint >}}

### Community Libraries

- [chatapi-js](https://github.com/example/chatapi-js) - JavaScript/TypeScript SDK
- [chatapi-python](https://github.com/example/chatapi-python) - Python SDK
- [chatapi-go](https://github.com/example/chatapi-go) - Go SDK

## API Versions

ChatAPI uses semantic versioning for API changes:

- **v1** (current): Initial stable API
- Breaking changes will introduce new major versions

## Testing

Use the built-in API playground or tools like:

- **curl**: Command-line testing
- **Postman**: GUI API testing
- **Insomnia**: Alternative to Postman
- **Swagger UI**: Interactive API documentation

## Next Steps

- [REST API Reference](/api/rest/) - Complete REST endpoint documentation
- [WebSocket API Reference](/api/websocket/) - Real-time API documentation
- [API Examples](/api/examples/) - Code samples and use cases

