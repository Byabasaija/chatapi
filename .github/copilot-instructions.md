# Go ChatAPI — Final Spec v2 (multitenant, service-based, SQLite, chatroom model)

Lightweight, single-binary Go service. Multitenant via API key (stateless). Durable notifications enabled. Email excluded. Parent app supplies user_id. Minimal dependencies. Production-ready with graceful shutdown, health checks, and structured logging.

## Key design decisions

**Tenancy**: API-Key approach. Each request must identify tenant via `X-API-Key`. Server maps API key → tenant_id.

**Identity**: Parent app supplies `X-User-Id` on each request (and for WS connections). ChatAPI does not manage user accounts.

**Model**: Everything is a chatroom (DMs are rooms with 2 members).

**DB**: Single SQLite DB (WAL mode). Shared DB across tenants; every relevant table includes tenant_id.

**Realtime**: WebSocket for live events; in-memory pub/sub for single-server fan-out.

**Delivery**: store-then-send with at-least-once guarantees, client ACKs, server retries, persistent undelivered queue for durable notifications/messages.

**Notifications**: Durable mode (store + fanout + retry + dead-letter). Parent app posts notifications to ChatAPI endpoint to relay to subscribers (and ChatAPI can emit webhook events back to parent if desired).

**Email**: Excluded — parent app handles email triggered by ChatAPI events (webhook/push).

## Minimal dependencies

Only:

- stdlib (`net/http`, `database/sql`, `context`, `sync`, `time`, `encoding/json`, `log/slog`)
- `modernc.org/sqlite` (or `github.com/mattn/go-sqlite3` if CGO OK)
- `github.com/gorilla/websocket`

No ORMs, no frameworks, no Redis; pure `net/http` + `gorilla/websocket`.

## Project layout (service-based)

```
/cmd/chatapi/main.go
/internal/
  config/         // config loader
  db/             // sqlite init, migrations, WAL management
  models/         // struct types
  services/
    tenant/       // tenant lookup, rate limiting
    chatroom/
    member/
    message/
    realtime/     // WS session registry, pub/sub
    notification/
    delivery/     // delivery workers
  handlers/
    rest/         // HTTP endpoints
    ws/           // WebSocket handlers
  transport/      // HTTP server bootstrapping, graceful shutdown
  worker/         // background workers (retries, DLQ processing, WAL checkpoints)
  ratelimit/      // in-memory token bucket rate limiter
```

## Database schema (SQLite)

All tables include `tenant_id TEXT NOT NULL`.

### tenants

```sql
CREATE TABLE tenants (
  tenant_id TEXT PRIMARY KEY,
  api_key TEXT UNIQUE NOT NULL,
  name TEXT,
  config JSON,  -- per-tenant feature flags: max_message_size, retry_limit, etc.
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### rooms

```sql
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
```

### room_members

```sql
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
```

### messages

```sql
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
```

### delivery_state

Per-user per-chat tracking of last acknowledged sequence.

```sql
CREATE TABLE delivery_state (
  tenant_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  chatroom_id TEXT NOT NULL,
  last_ack INTEGER DEFAULT 0,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (tenant_id, user_id, chatroom_id)
);

CREATE INDEX idx_delivery_user_room ON delivery_state(tenant_id, user_id, chatroom_id);
```

### undelivered_messages

Persistent queue for per-user undelivered messages.

```sql
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
```

### notifications (durable)

```sql
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
```

### notification_subscriptions (optional)

Parent apps can register subscribers; alternatively parent apps send target user lists.

```sql
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
```

## Core services

### TenantService

- Validate `X-API-Key` → tenant lookup
- Provide tenant config (e.g., `durable_notifications` boolean, `max_message_size`, `retry_limit`)
- **Rate limiting**: in-memory token bucket per `tenant_id` (e.g., 100 req/sec per tenant)

### ChatroomService

- Create room (deterministic DM logic via `unique_key`)
- Add/remove members
- Fetch members

### MessageService

- Store message (transactionally increment `last_seq` → INSERT messages)
- Enqueue undelivered targets for offline users
- Handle idempotency via `message_id`

### RealtimeService

- Manage WS sessions: in-memory map `map[tenant_id][user_id] -> []*websocket.Conn`
- Publish events to subscribers (fan-out to connections)
- Broadcast presence updates on connect/disconnect
- Handle graceful shutdown (drain connections with timeout)

### DeliveryService/Worker

- Read `undelivered_messages` and `notifications` tables where `attempts < threshold`
- Retry delivery (WS if online; optional webhook/push if configured)
- Mark delivered or move to dead-letter after max attempts
- Purge old entries older than `last_ack`

### NotificationService

- Store inbound notification
- Determine subscribers (by topic or explicit targets)
- Create queued deliveries and kick worker

## APIs — REST

All REST calls require `X-API-Key: <api_key>` header. All actions that are "performed by a user" require `X-User-Id: <user_id>` header.

### Auth headers (required)

```
X-API-Key: <tenant_api_key>
X-User-Id: <user_id>      // actor; required for message send, room create, ack
```

### Chatrooms

**POST /rooms**

Body:

```json
{
  "type": "dm"|"group"|"channel",
  "members": ["u1", "u2"],
  "name": "optional"
}
```

Behavior: if `type == "dm"`, compute deterministic `unique_key = dm:min:max` and return existing if present; else create.

**GET /rooms/{room_id}**

**GET /rooms/{room_id}/members**

### Messages

**POST /rooms/{room_id}/messages**

Body:

```json
{
  "content": "...",
  "meta": {}
}
```

Server: transactionally increment `room.last_seq`, insert message (seq assigned), respond with message object (`message_id` + `seq` + `created_at`). After write, publish to realtime layer. For any members offline, persist `undelivered_messages` rows.

**GET /rooms/{room_id}/messages?after_seq=N&limit=50**

### ACKs / Delivery

**POST /acks**

Body:

```json
{
  "room_id": "...",
  "seq": 123
}
```

Requires `X-User-Id`. Server updates `delivery_state.last_ack`. Handles out-of-order ACKs idempotently (only update if `seq > current last_ack`).

### Notifications (incoming from parent app)

**POST /notify**

Body:

```json
{
  "topic": "order.shipped",
  "payload": {},
  "targets": {
    "user_ids": [],
    "room_id": "...",
    "topic_subscribers": true
  }
}
```

Server stores into `notifications` (durable), schedules deliveries for subscribers, responds 202.

### Health & Admin

**GET /health**

Returns:

```json
{
  "status": "ok",
  "uptime": "12h34m",
  "db_writable": true
}
```

Checks: SQLite write test, uptime reporting. Use for monitoring/load balancers.

**GET /admin/dead-letters?tenant_id=X&limit=100** (optional)

Returns failed notifications/messages in dead-letter status for debugging.

## WebSocket protocol (realtime)

### Endpoint

`GET /ws` with headers:

```
X-API-Key: <api_key>
X-User-Id: <user_id>
```

Or query params (fallback for browser clients, but less secure):

```
/ws?api_key=<>&user_id=<>
```

**Security note**: Prefer header-based auth. Query params leak in logs/browser history. Consider short-lived tokens for production.

Server validates tenant & user at connect. Registers connection in `RealtimeService`.

### Messages from client → server (JSON)

```json
{"type": "send_message", "room_id": "r1", "content": "hi", "meta": {}}
{"type": "ack", "room_id": "r1", "seq": 51}
{"type": "typing.start", "room_id": "r1"}
{"type": "typing.stop", "room_id": "r1"}
{"type": "subscribe", "room_id": "r1"}  // optional explicit subscribe
```

### Events server → client (JSON)

```json
{"type": "message", "room_id": "r1", "seq": 51, "message_id": "...", "sender_id": "u1", "content": "hi", "created_at": "..."}
{"type": "ack.received", "room_id": "r1", "seq": 51, "user_id": "u2"}
{"type": "presence.update", "user_id": "u2", "status": "online"|"offline"}
{"type": "typing", "room_id": "r1", "user_id": "u2", "action": "start"|"stop"}
{"type": "notification", "notification_id": "...", "topic": "order.shipped", "payload": {}}
```

### WS behavior

**On connect**:

- Server registers connection: `onlineUsers[tenant][user] = append(conn)`
- Broadcast `presence.update` (online) to rooms where other members are connected
- **Reconnect sync**: Query `messages` where `seq > delivery_state.last_ack` for user's rooms and stream them in order

**On disconnect**:

- Remove connection
- If no more connections for that user, broadcast `presence.update` (offline) after brief delay (5s grace period for quick reconnects)

**On send_message**:

- Server requires `X-User-Id` (from connect param or header) as `sender_id` — cannot be spoofed by client
- Insert message → publish to connected members → queue `undelivered_messages` for offline members

**Graceful shutdown**:

- On SIGTERM/SIGINT: stop accepting new connections
- Send `{"type": "server.shutdown", "reconnect_after_ms": 5000}` to all connected clients
- Wait 5-10s for clients to drain/reconnect elsewhere
- Close remaining connections
- Shutdown server

## Delivery algorithm (detailed)

Goal: durable, at-least-once, ordered per chatroom.

### Store-then-send (atomic)

```
1. Begin transaction
2. UPDATE rooms SET last_seq = last_seq + 1 WHERE room_id = ? AND tenant_id = ?
3. seq = last_seq
4. INSERT INTO messages (message_id, tenant_id, chatroom_id, sender_id, seq, content, created_at)
5. Commit
```

### Publish

`RealtimeService.Publish(tenant, chatroom, message)` → iterate connections for members and write WS messages asynchronously (goroutines with buffered channels).

For each member that is not connected, create `undelivered_messages` entry (persistent). Also create/update records in `delivery_state` as needed.

### ACK handling

Clients send ACK with seq. Server updates `delivery_state.last_ack` for that user+chatroom **only if seq > current last_ack** (handles out-of-order ACKs).

Worker periodically purges `undelivered_messages` entries where `seq <= last_ack`.

### Retry / Worker

Worker runs every 10-30s:

1. Read `undelivered_messages`/`notifications` where `attempts < max_attempts` (e.g., 5)
2. Attempt delivery:
   - WS if user online
   - Optional webhook or push notification if configured
3. On success: remove `undelivered_messages` row; mark notification `delivered`
4. On failure: increment `attempts`, set `last_attempt_at`
5. If `attempts >= max_attempts`: set `status = 'dead'`, optionally move to separate dead-letter table

### Reconnect sync

When user reconnects:

1. Server queries: `SELECT * FROM messages WHERE tenant_id = ? AND chatroom_id IN (...user's rooms...) AND seq > ? ORDER BY seq` (where `?` = `delivery_state.last_ack`)
2. Stream messages in sequence over WS
3. Resume realtime updates

### Duplicate handling

Clients dedupe by `message_id` (UUID). Server may re-send same message during retries — client must check `message_id` to ignore duplicates.

## Notification relay (durable mode)

1. Parent app posts `POST /notify` with `X-API-Key` and optionally `X-User-Id`
2. Server writes notification row in `notifications` table with `status = 'pending'`
3. Worker picks `pending` notifications, resolves subscribers (explicit targets or via `notification_subscriptions`)
4. Enqueues per-subscriber deliveries (as `undelivered_messages` or similar)
5. Worker attempts immediate delivery over WS for online subscribers
6. For offline subscribers: keep queued entries; optionally emit webhook to parent app (if configured) to let parent do push/email
7. Notification delivery uses same retry & DLQ semantics as messages

## Presence & Typing

**Presence**: purely in-memory. On WS connect/disconnect broadcast `presence.update` to rooms or to subscribers. No DB writes. Include 5s grace period before marking offline to handle quick reconnects.

**Typing**: ephemeral WS events fanned out to room members. No DB writes. Auto-expire after 5s if no stop event received.

## API Key & security

- `tenants` table stores `api_key`
- Server authenticates each request by `X-API-Key`
- Validate that `X-User-Id` is present for actions that are user-scoped
- **Rate limiting**: in-memory token bucket per tenant (e.g., 100 req/sec). Returns `429 Too Many Requests` when exceeded
- For WS: prefer headers over query params for credentials

## Client reconnect behavior (expected)

Clients should implement:

1. **Exponential backoff**: 1s, 2s, 4s, 8s, max 30s between reconnect attempts
2. **Resume from last_ack**: On reconnect, expect server to stream missed messages
3. **Deduplication**: Track received `message_id` set to ignore duplicates during retries
4. **Handle `server.shutdown` event**: Immediately reconnect when server signals graceful shutdown

## Configuration / runtime

Config via env or file:

```
DATA_DIR=/var/chatapi
SQLITE_DSN=file:chatapi.db?_journal_mode=WAL&_busy_timeout=5000
LISTEN_ADDR=:8080
WAL_AUTOCHECKPOINT=1000
RETRY_MAX_ATTEMPTS=5
RETRY_INTERVAL=30s
WORKER_INTERVAL=30s
SHUTDOWN_DRAIN_TIMEOUT=10s
LOG_LEVEL=info
```

### Start-up

1. Open SQLite with WAL mode: `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;`
2. Set `PRAGMA wal_autocheckpoint=1000;` to prevent unbounded WAL growth
3. Run migrations from `internal/db/migrations/*.sql`
4. Load tenant API keys into memory
5. Start HTTP+WS server
6. Start background workers:
   - Delivery retry worker (every 30s)
   - WAL checkpoint worker (every 5 minutes: `PRAGMA wal_checkpoint(TRUNCATE);`)
7. Register signal handlers for graceful shutdown (SIGTERM, SIGINT)

### Graceful shutdown

On SIGTERM/SIGINT:

1. Stop accepting new HTTP/WS connections
2. Send shutdown notice to all WS clients (`{"type": "server.shutdown"}`)
3. Wait `SHUTDOWN_DRAIN_TIMEOUT` (10s) for clients to disconnect
4. Close remaining connections
5. Stop workers
6. Close DB connection
7. Exit

## Structured logging

Use `log/slog` (Go 1.21+). Log format:

```json
{
  "time": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "msg": "message sent",
  "tenant_id": "acme",
  "user_id": "alice",
  "room_id": "r123",
  "message_id": "m456",
  "seq": 42
}
```

Include `tenant_id`, `user_id`, `room_id` in all relevant log entries for debugging multi-tenant issues.

## WAL management

SQLite WAL mode requires periodic checkpointing to prevent WAL file from growing unbounded.

### Config

- `PRAGMA wal_autocheckpoint=1000;` — checkpoint every 1000 pages
- `PRAGMA busy_timeout=5000;` — wait up to 5s for locks

### Worker

Background worker runs every 5 minutes:

```sql
PRAGMA wal_checkpoint(TRUNCATE);
```

This merges WAL into main DB file. Monitor WAL file size; if it grows beyond ~100MB, increase checkpoint frequency.

## Testing & local dev

- Use `file::memory:?cache=shared` or temp files for SQLite in tests
- Unit tests for services
- Integration tests for end-to-end flow: message store → WS fanout → ack → reconnect sync
- Simulated WebSocket clients for concurrency tests
- Test graceful shutdown: send SIGTERM, verify drain behavior

## Operational notes

- **Single binary**: `chatapi` with embedded migrations
- **Data file**: `chatapi.db` + `chatapi.db-wal` + `chatapi.db-shm` must be backed up together (recommend nightly snapshot or litestream)
- **Monitoring**: `/health` endpoint for uptime checks; export SQLite stats (DB size, WAL size, connection count)
- **Logs**: structured JSON to stdout; ship to log aggregator (e.g., Loki, CloudWatch)
- **Backups**: SQLite backup via `.backup` command or file copy (with WAL); test restore procedure

### Horizontal scale (future)

For horizontal scale later: add NATS/Redis for cross-instance pub/sub and either a shared DB (Postgres) or litestream replication for SQLite. But not required for single-server MVP.

## Rate limiting (in-memory)

Per-tenant token bucket:

- Refill rate: 100 tokens/second (configurable per tenant via `tenants.config`)
- Bucket size: 200 tokens
- Cost: 1 token per request
- Return `429 Too Many Requests` with `Retry-After` header when bucket empty

Implementation: `internal/ratelimit/tokenbucket.go` with `sync.Map` keyed by `tenant_id`.

## Copilot / Scaffold hints (what to generate)

1. Generate `cmd/chatapi/main.go` to initialize config, DB, services, HTTP server, signal handlers
2. Generate `internal/db/migrations/*.sql` for tables above
3. Scaffold services interfaces and simple implementations: `ChatroomService`, `MessageService`, `RealtimeService`, `NotificationService`, `DeliveryWorker`. Small files
4. `handlers/rest` for endpoints listed. Use `net/http` handlers + `encoding/json`
5. `handlers/ws` using `gorilla/websocket` to handle connection lifecycle, register/unregister, read loop for incoming messages, write loop with buffered channel
6. `worker` that periodically reads `notifications` and `undelivered_messages` tables and tries delivery
7. `internal/transport/shutdown.go` for graceful shutdown logic
8. `internal/ratelimit/tokenbucket.go` for rate limiting
9. Minimal tests: message insert + seq increment, WS connect send/receive, ack flow, reconnect sync

## Example: DM creation (deterministic)

**POST /rooms** body:

```json
{
  "type": "dm",
  "members": ["alice", "bob"]
}
```

Server:

1. Normalize: `ids := sort(members)` → `["alice", "bob"]`
2. `unique_key := fmt.Sprintf("dm:%s:%s", ids[0], ids[1])` → `"dm:alice:bob"`
3. `SELECT room_id FROM rooms WHERE tenant_id=? AND unique_key=?` → return if exists
4. Else transaction:
   - INSERT `rooms` with `unique_key`
   - INSERT `room_members` for each user
   - Return room object

## Example: Message send flow

Client (HTTP or WS) → sends message. Server:

1. Verify tenant + user (auth headers)
2. Check rate limit (token bucket for tenant)
3. Transactionally increment `rooms.last_seq` and insert `messages` with seq
4. Publish to realtime (online users get delivered immediately via WS)
5. Insert `undelivered_messages` rows for offline members
6. Respond with `{message_id, seq, created_at}`

## Example: Reconnect sync flow

1. Client connects WS with `X-User-Id: alice`
2. Server registers connection
3. Server queries `delivery_state` for alice's `last_ack` per room
4. Server queries `messages` WHERE `seq > last_ack` for each room
5. Server streams missed messages in order: `{"type": "message", ...}`
6. Client ACKs each message
7. Server resumes realtime updates

## Deliverables

- Copilot-ready README/spec file (this document)
- SQL migrations in `internal/db/migrations/`
- Minimal scaffolded Go project skeleton with key files and TODOs for implementation
- Example WS client code snippet for SDKs (Go / JS)
- Health check endpoint for monitoring
- Graceful shutdown handler
- Structured logging setup with `log/slog`