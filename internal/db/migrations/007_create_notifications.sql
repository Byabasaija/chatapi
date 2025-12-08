-- Create notifications table (durable)
CREATE TABLE notifications (
  notification_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  topic TEXT NOT NULL,
  payload JSON NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'pending',   -- pending | processing | delivered | failed | dead
  attempts INTEGER DEFAULT 0,
  last_attempt_at DATETIME NULL
);

CREATE INDEX idx_notifications_status ON notifications(tenant_id, status, created_at);