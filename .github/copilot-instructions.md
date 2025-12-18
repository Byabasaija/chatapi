# Go ChatAPI — AI Agent Guidelines

## Architecture Overview

Lightweight Go service for multitenant chat, using SQLite + WebSocket. Service-based architecture in `internal/`: config, db, models, services, handlers, transport, worker, ratelimit.

Key components:
- **Services**: Business logic (tenant validation, chatroom ops, message sequencing, realtime pub/sub, delivery retries)
- **Handlers**: REST (`/rooms`, `/messages`, `/acks`, `/notify`) and WS (`/ws`) endpoints
- **Workers**: Background tasks for delivery retries and WAL checkpoints
- **DB**: SQLite with WAL mode, embedded migrations in `internal/db/migrations/`

## Key Patterns

- **Multitenancy**: API-key based, stateless; parent app provides `X-User-Id`
- **Message Sequencing**: Atomic `UPDATE last_seq +1` then `INSERT message` in transaction
- **Realtime**: In-memory WS registry; fan-out to online users, queue undelivered for offline
- **Durable Delivery**: Store-then-send, at-least-once with ACKs and retries
- **Logging**: Structured JSON with `slog`, include `tenant_id`, `user_id`, etc.
- **Migrations**: Embedded FS, run on startup, track in `schema_migrations`

## Developer Workflows

- **Build**: `go build ./cmd/chatapi`
- **Run**: Set env vars (`LISTEN_ADDR`, `DATABASE_DSN`), `./chatapi`
- **Health**: `GET /health` for uptime and DB check
- **Debug**: `LOG_LEVEL=debug`, use `slog` for tracing
- **Migrations**: Auto-run on start; add new `.sql` in `internal/db/migrations/`

## Conventions

- **Services**: Take `*sql.DB`, return structs from `internal/models`
- **Handlers**: Use `AuthMiddleware` for tenant/rate limit; parse JSON requests
- **WS**: Gorilla/websocket; JSON messages; reconnect sync missed messages
- **Errors**: Wrap with `fmt.Errorf`, log with `slog.Error`
- **IDs**: UUID for messages, deterministic keys for DMs (`dm:min:max`)
- **Config**: Env vars loaded via `internal/config`

## Integration Points

- **External**: Parent app calls REST/WS with `X-API-Key` and `X-User-Id`
- **Realtime**: WS for live events; HTTP for history/acks
- **Notifications**: POST `/notify` to relay to subscribers
- **Rate Limiting**: In-memory token bucket per tenant

Reference: [Full Spec](README.md), [API Docs](docs/)
