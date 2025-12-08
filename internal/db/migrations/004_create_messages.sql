-- Create messages table
CREATE TABLE messages (
  message_id TEXT PRIMARY KEY,   -- UUID
  tenant_id TEXT NOT NULL,
  chatroom_id TEXT NOT NULL,
  sender_id TEXT NOT NULL,
  seq INTEGER NOT NULL,          -- per-chatroom seq
  content TEXT NOT NULL,
  meta JSON NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_messages_room_seq ON messages(tenant_id, chatroom_id, seq);