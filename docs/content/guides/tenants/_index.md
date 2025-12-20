---
title: "Setting Up Tenants"
weight: 11
---

# Setting Up Tenants

This guide explains how to create and manage tenants in ChatAPI. Tenants provide multi-tenant isolation, allowing you to serve multiple organizations or applications from a single ChatAPI instance.

## Prerequisites

Before creating tenants, ensure you have:

1. **ChatAPI running** with `MASTER_API_KEY` configured
2. **Admin access** to the master API key
3. **Understanding** of tenant isolation concepts

## What is a Tenant?

A tenant represents an isolated organization or application instance:

- **API Key**: Unique authentication key for the tenant
- **Isolation**: Complete data separation from other tenants
- **Rate Limiting**: Per-tenant request limits
- **Configuration**: Tenant-specific settings

## Creating Your First Tenant

### 1. Generate a Master API Key

First, set up your master API key in the environment:

```bash
# Generate a secure random key (64 characters recommended)
export MASTER_API_KEY="s08XLS75G2SHN3owC2WkYtcdddHpUPBJXCG/3cKc66M="

# Or use openssl to generate one
export MASTER_API_KEY=$(openssl rand -hex 32)
```

### 2. Start ChatAPI

```bash
# With master key configured
export MASTER_API_KEY="your-master-key-here"
./bin/chatapi
```

### 3. Create a Tenant

Use the admin API to create your first tenant:

```bash
curl -X POST http://localhost:8080/admin/tenants \
  -H "X-Master-Key: your-master-key-here" \
  -H "Content-Type: application/json" \
  -d '{"name": "MyCompany"}'
```

**Response:**
```json
{
  "tenant_id": "tenant_abc123",
  "api_key": "sk_abc123def456ghi789jkl012mno345pqr678stu901vwx",
  "name": "MyCompany",
  "created_at": "2025-12-13T12:00:00Z"
}
```

### 4. Store the API Key Securely

**Important:** Save the `api_key` immediately - it cannot be retrieved later!

```bash
# Store securely (environment variable, secret manager, etc.)
export CHATAPI_KEY="sk_abc123def456ghi789jkl012mno345pqr678stu901vwx"
```

## Testing Your Tenant

### Create a Test Room

```bash
curl -X POST http://localhost:8080/rooms \
  -H "X-API-Key: $CHATAPI_KEY" \
  -H "X-User-Id: testuser" \
  -H "Content-Type: application/json" \
  -d '{"type": "dm", "members": ["alice", "bob"]}'
```

### Send a Test Message

```bash
curl -X POST http://localhost:8080/rooms/room_abc123/messages \
  -H "X-API-Key: $CHATAPI_KEY" \
  -H "X-User-Id: alice" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello from my tenant!"}'
```

## Managing Multiple Tenants

### Creating Additional Tenants

```bash
# Tenant for different organization
curl -X POST http://localhost:8080/admin/tenants \
  -H "X-Master-Key: your-master-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "AnotherCompany"}'

# Tenant for staging environment
curl -X POST http://localhost:8080/admin/tenants \
  -H "X-Master-Key: your-master-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "StagingEnvironment"}'
```

### Tenant Isolation

Each tenant is completely isolated:

- **Data Separation**: Tenants cannot access each other's data
- **Rate Limiting**: Limits apply per tenant
- **API Keys**: Each tenant has its own authentication
- **Resource Usage**: Usage is tracked per tenant

## Production Considerations

### Security

- **Master Key Protection**: Store master key securely (vault, KMS, etc.)
- **API Key Rotation**: Implement key rotation policies
- **Access Control**: Limit who can create tenants

### Scaling

- **Rate Limits**: Configure appropriate limits per tenant
- **Monitoring**: Track usage per tenant
- **Backup**: Include tenant data in backups

### Environment Variables

For production deployment:

```bash
# Required
export MASTER_API_KEY="your-secure-master-key"

# Optional per-tenant settings
export DEFAULT_RATE_LIMIT="1000"  # Higher for production
```

## Troubleshooting

### Common Issues

**"Unauthorized" when creating tenant:**
- Verify `MASTER_API_KEY` is set correctly
- Check `X-Master-Key` header matches

**"Invalid API key" in tenant operations:**
- Ensure you're using the tenant's `api_key`, not the master key
- Check for typos in the API key

**Rate limiting:**
- Increase `DEFAULT_RATE_LIMIT` if needed
- Implement exponential backoff in your client

### Debugging

Enable debug logging to troubleshoot tenant issues:

```bash
export LOG_LEVEL="debug"
./bin/chatapi
```

Look for tenant-related log entries:
```json
{"level":"info","msg":"Tenant validated","tenant_id":"tenant_abc123"}
{"level":"error","msg":"Invalid API key","error":"tenant not found"}
```

## Next Steps

Now that you have tenants set up:

1. **[Create Rooms](/guides/rooms/)** - Start building chat functionality
2. **[Integrate WebSockets](/api/websocket/)** - Add real-time messaging
3. **[Monitor Health](/api/rest/#health-check)** - Set up monitoring
4. **[Configure Production](/guides/deployment/)** - Deploy to production

## API Reference

- [Create Tenant API](/api/rest/#create-tenant-admin)
- [Authentication Guide](/api/)
- [Configuration Options](/getting-started/)</content>
