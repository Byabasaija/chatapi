-- Create rooms table
CREATE TABLE rooms (
  room_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  type TEXT NOT NULL,           -- 'dm'|'group'|'channel'
  unique_key TEXT NULL,          -- deterministic key for DMs (dm:userA:userB)
  name TEXT NULL,
  last_seq INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rooms_tenant ON rooms(tenant_id, room_id);
CREATE UNIQUE INDEX idx_rooms_unique_key ON rooms(tenant_id, unique_key) WHERE unique_key IS NOT NULL;