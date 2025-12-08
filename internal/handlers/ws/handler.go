package ws

import (
	"encoding/json"
	"log/slog"
	"net/http"
	"time"

	"github.com/gorilla/websocket"
	"github.com/Byabasaija/chatapi/internal/models"
	"github.com/Byabasaija/chatapi/internal/services/chatroom"
	"github.com/Byabasaija/chatapi/internal/services/message"
	"github.com/Byabasaija/chatapi/internal/services/realtime"
	"github.com/Byabasaija/chatapi/internal/services/tenant"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		// In production, implement proper origin checking
		return true
	},
}

// Handler handles WebSocket connections
type Handler struct {
	tenantSvc   *tenant.Service
	chatroomSvc *chatroom.Service
	messageSvc  *message.Service
	realtimeSvc *realtime.Service
}

// NewHandler creates a new WebSocket handler
func NewHandler(
	tenantSvc *tenant.Service,
	chatroomSvc *chatroom.Service,
	messageSvc *message.Service,
	realtimeSvc *realtime.Service,
) *Handler {
	return &Handler{
		tenantSvc:   tenantSvc,
		chatroomSvc: chatroomSvc,
		messageSvc:  messageSvc,
		realtimeSvc: realtimeSvc,
	}
}

// HandleConnection handles WebSocket connections
func (h *Handler) HandleConnection(w http.ResponseWriter, r *http.Request) {
	// Extract authentication from headers or query params
	apiKey := r.Header.Get("X-API-Key")
	userID := r.Header.Get("X-User-Id")

	// Fallback to query params for browser clients
	if apiKey == "" {
		apiKey = r.URL.Query().Get("api_key")
	}
	if userID == "" {
		userID = r.URL.Query().Get("user_id")
	}

	if apiKey == "" || userID == "" {
		http.Error(w, "Missing authentication", http.StatusUnauthorized)
		return
	}

	// Validate tenant
	tenant, err := h.tenantSvc.ValidateAPIKey(apiKey)
	if err != nil {
		http.Error(w, "Invalid authentication", http.StatusUnauthorized)
		return
	}

	// Check rate limit
	if err := h.tenantSvc.CheckRateLimit(tenant.TenantID); err != nil {
		http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
		return
	}

	// Upgrade to WebSocket
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		slog.Error("Failed to upgrade connection", "error", err)
		return
	}

	// Register connection
	h.realtimeSvc.RegisterConnection(tenant.TenantID, userID, conn)

	// Send presence update
	h.realtimeSvc.BroadcastPresenceUpdate(tenant.TenantID, userID, "online")

	// Handle reconnect sync - send missed messages
	go h.handleReconnectSync(tenant.TenantID, userID, conn)

	// Start connection handler
	go h.handleConnection(tenant.TenantID, userID, conn)
}

// handleReconnectSync sends missed messages to a reconnecting client
func (h *Handler) handleReconnectSync(tenantID, userID string, conn *websocket.Conn) {
	// Get user's rooms
	// This is a simplified implementation - in practice you'd query the database
	// for rooms the user is a member of

	// For now, we'll skip this and let the client request messages as needed
	// In a full implementation, you'd:
	// 1. Get user's rooms from database
	// 2. For each room, get last_ack
	// 3. Query messages where seq > last_ack
	// 4. Send them in order
}

// handleConnection handles messages from a WebSocket connection
func (h *Handler) handleConnection(tenantID, userID string, conn *websocket.Conn) {
	defer func() {
		h.realtimeSvc.UnregisterConnection(tenantID, userID, conn)
		conn.Close()
	}()

	// Set read deadline
	conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	conn.SetPongHandler(func(string) error {
		conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		_, message, err := conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				slog.Warn("WebSocket error", "tenant_id", tenantID, "user_id", userID, "error", err)
			}
			break
		}

		// Reset read deadline
		conn.SetReadDeadline(time.Now().Add(60 * time.Second))

		// Parse message
		var wsMsg models.WSMessage
		if err := json.Unmarshal(message, &wsMsg); err != nil {
			slog.Warn("Invalid WebSocket message", "tenant_id", tenantID, "user_id", userID, "error", err)
			continue
		}

		// Handle message based on type
		if err := h.handleMessage(tenantID, userID, &wsMsg); err != nil {
			slog.Error("Failed to handle WebSocket message",
				"tenant_id", tenantID,
				"user_id", userID,
				"type", wsMsg.Type,
				"error", err)
		}
	}
}

// handleMessage processes different types of WebSocket messages
func (h *Handler) handleMessage(tenantID, userID string, msg *models.WSMessage) error {
	switch msg.Type {
	case "send_message":
		return h.handleSendMessage(tenantID, userID, msg.Data)
	case "ack":
		return h.handleAck(tenantID, userID, msg.Data)
	case "typing.start":
		return h.handleTyping(tenantID, userID, msg.Data, "start")
	case "typing.stop":
		return h.handleTyping(tenantID, userID, msg.Data, "stop")
	default:
		slog.Warn("Unknown message type", "type", msg.Type, "tenant_id", tenantID, "user_id", userID)
		return nil
	}
}

// handleSendMessage handles message sending via WebSocket
func (h *Handler) handleSendMessage(tenantID, userID string, data interface{}) error {
	msgData, ok := data.(map[string]interface{})
	if !ok {
		return nil
	}

	roomID, ok := msgData["room_id"].(string)
	if !ok {
		return nil
	}

	content, ok := msgData["content"].(string)
	if !ok {
		return nil
	}

	req := &models.CreateMessageRequest{
		Content: content,
	}

	if meta, ok := msgData["meta"].(string); ok {
		req.Meta = meta
	}

	message, err := h.messageSvc.SendMessage(tenantID, roomID, userID, req)
	if err != nil {
		return err
	}

	// Broadcast to realtime subscribers
	h.realtimeSvc.BroadcastToRoom(tenantID, roomID, map[string]interface{}{
		"type":       "message",
		"room_id":    roomID,
		"seq":        message.Seq,
		"message_id": message.MessageID,
		"sender_id":  message.SenderID,
		"content":    message.Content,
		"created_at": message.CreatedAt.Format("2006-01-02T15:04:05Z07:00"),
	})

	return nil
}

// handleAck handles acknowledgment of message delivery
func (h *Handler) handleAck(tenantID, userID string, data interface{}) error {
	ackData, ok := data.(map[string]interface{})
	if !ok {
		return nil
	}

	roomID, ok := ackData["room_id"].(string)
	if !ok {
		return nil
	}

	seqFloat, ok := ackData["seq"].(float64)
	if !ok {
		return nil
	}
	seq := int(seqFloat)

	if err := h.messageSvc.UpdateLastAck(tenantID, userID, roomID, seq); err != nil {
		return err
	}

	// Broadcast ACK to other room members
	h.realtimeSvc.BroadcastToRoom(tenantID, roomID, map[string]interface{}{
		"type":    "ack.received",
		"room_id": roomID,
		"seq":     seq,
		"user_id": userID,
	})

	return nil
}

// handleTyping handles typing indicators
func (h *Handler) handleTyping(tenantID, userID string, data interface{}, action string) error {
	typingData, ok := data.(map[string]interface{})
	if !ok {
		return nil
	}

	roomID, ok := typingData["room_id"].(string)
	if !ok {
		return nil
	}

	// Broadcast typing indicator to room members
	h.realtimeSvc.BroadcastToRoom(tenantID, roomID, map[string]interface{}{
		"type":    "typing",
		"room_id": roomID,
		"user_id": userID,
		"action":  action,
	})

	return nil
}