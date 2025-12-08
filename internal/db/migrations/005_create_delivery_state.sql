-- Create delivery_state table
-- Per-user per-chat tracking of last acknowledged sequence
CREATE TABLE delivery_state (
  tenant_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  chatroom_id TEXT NOT NULL,
  last_ack INTEGER DEFAULT 0,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (tenant_id, user_id, chatroom_id)
);

CREATE INDEX idx_delivery_user_room ON delivery_state(tenant_id, user_id, chatroom_id);