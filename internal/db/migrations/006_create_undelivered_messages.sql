-- Create undelivered_messages table
-- Persistent queue for per-user undelivered messages
CREATE TABLE undelivered_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  chatroom_id TEXT NOT NULL,
  message_id TEXT NOT NULL,
  seq INTEGER NOT NULL,
  attempts INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_attempt_at DATETIME NULL
);

CREATE INDEX idx_undelivered_user_room_seq ON undelivered_messages(tenant_id, user_id, chatroom_id, seq);
CREATE INDEX idx_undelivered_attempts ON undelivered_messages(tenant_id, attempts, created_at);