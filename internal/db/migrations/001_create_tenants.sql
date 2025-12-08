-- Create tenants table
CREATE TABLE tenants (
  tenant_id TEXT PRIMARY KEY,
  api_key TEXT UNIQUE NOT NULL,
  name TEXT,
  config JSON,  -- per-tenant feature flags: max_message_size, retry_limit, etc.
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);