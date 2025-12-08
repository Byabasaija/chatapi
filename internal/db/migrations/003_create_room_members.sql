-- Create room_members table
CREATE TABLE room_members (
  chatroom_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  role TEXT DEFAULT 'member',
  joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY(chatroom_id, user_id)
);

CREATE INDEX idx_members_tenant_user ON room_members(tenant_id, user_id);
CREATE INDEX idx_members_tenant_room ON room_members(tenant_id, chatroom_id);