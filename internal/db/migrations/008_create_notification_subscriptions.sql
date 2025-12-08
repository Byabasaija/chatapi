-- Create notification_subscriptions table (optional)
-- Parent apps can register subscribers; alternatively parent apps send target user lists
CREATE TABLE notification_subscriptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id TEXT NOT NULL,
  subscriber_id TEXT NOT NULL,  -- user_id or device_id
  topic TEXT NOT NULL,
  endpoint TEXT NULL,            -- webhook URL or push token
  metadata JSON NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notif_subs_tenant_topic ON notification_subscriptions(tenant_id, topic);