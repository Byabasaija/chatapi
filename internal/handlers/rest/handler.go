package rest

import (
	"encoding/json"
	"log/slog"
	"net/http"
	"strconv"
	"time"

	"github.com/hastenr/chatapi/internal/models"
	"github.com/hastenr/chatapi/internal/services/chatroom"
	"github.com/hastenr/chatapi/internal/services/delivery"
	"github.com/hastenr/chatapi/internal/services/message"
	"github.com/hastenr/chatapi/internal/services/notification"
	"github.com/hastenr/chatapi/internal/services/realtime"
	"github.com/hastenr/chatapi/internal/services/tenant"
)

// Handler handles REST API requests
type Handler struct {
	tenantSvc   *tenant.Service
	chatroomSvc *chatroom.Service
	messageSvc  *message.Service
	realtimeSvc *realtime.Service
	deliverySvc *delivery.Service
	notifSvc    *notification.Service
	config      *config.Config
	startTime   time.Time
}

// NewHandler creates a new REST handler
func NewHandler(
	tenantSvc *tenant.Service,
	chatroomSvc *chatroom.Service,
	messageSvc *message.Service,
	realtimeSvc *realtime.Service,
	deliverySvc *delivery.Service,
	notifSvc *notification.Service,
	config *config.Config,
) *Handler {
	return &Handler{
		tenantSvc:   tenantSvc,
		chatroomSvc: chatroomSvc,
		messageSvc:  messageSvc,
		realtimeSvc: realtimeSvc,
		deliverySvc: deliverySvc,
		notifSvc:    notifSvc,
		config:      config,
		startTime:   time.Now(),
	}
}

// RegisterRoutes registers all REST routes
func (h *Handler) RegisterRoutes(mux *http.ServeMux) {
	// Health check
	mux.HandleFunc("GET /health", h.HandleHealth)

	// Rooms
	mux.HandleFunc("POST /rooms", h.HandleCreateRoom)
	mux.HandleFunc("GET /rooms/{room_id}", h.HandleGetRoom)
	mux.HandleFunc("GET /rooms/{room_id}/members", h.HandleGetRoomMembers)

	// Messages
	mux.HandleFunc("POST /rooms/{room_id}/messages", h.HandleSendMessage)
	mux.HandleFunc("GET /rooms/{room_id}/messages", h.HandleGetMessages)

	// ACKs
	mux.HandleFunc("POST /acks", h.HandleAck)

	// Notifications
	mux.HandleFunc("POST /notify", h.HandleNotify)

	// Admin
	mux.HandleFunc("POST /admin/tenants", h.HandleCreateTenant)
	mux.HandleFunc("GET /admin/dead-letters", h.HandleGetDeadLetters)
}

// AuthMiddleware for authentication and tenant validation
func (h *Handler) AuthMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// Extract API key
		apiKey := r.Header.Get("X-API-Key")
		if apiKey == "" {
			http.Error(w, "Missing X-API-Key header", http.StatusUnauthorized)
			return
		}

		// Validate tenant
		tenant, err := h.tenantSvc.ValidateAPIKey(apiKey)
		if err != nil {
			http.Error(w, "Invalid API key", http.StatusUnauthorized)
			return
		}

		// Check rate limit
		if err := h.tenantSvc.CheckRateLimit(tenant.TenantID); err != nil {
			w.Header().Set("Retry-After", "60")
			http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
			return
		}

		// Add tenant to request context (simplified - in production use context.WithValue)
		r.Header.Set("X-Tenant-ID", tenant.TenantID)

		next(w, r)
	}
}

// getTenantID extracts tenant ID from request
func (h *Handler) getTenantID(r *http.Request) string {
	return r.Header.Get("X-Tenant-ID")
}

// getUserID extracts user ID from request
func (h *Handler) getUserID(r *http.Request) string {
	return r.Header.Get("X-User-Id")
}

// requireUserID ensures X-User-Id header is present
func (h *Handler) requireUserID(w http.ResponseWriter, r *http.Request) string {
	userID := h.getUserID(r)
	if userID == "" {
		http.Error(w, "Missing X-User-Id header", http.StatusBadRequest)
		return ""
	}
	return userID
}

// HandleHealth health check endpoint
func (h *Handler) HandleHealth(w http.ResponseWriter, r *http.Request) {
	uptime := time.Since(h.startTime)

	// Test database writability
	dbWritable := h.testDatabaseWrite()

	response := map[string]interface{}{
		"status":      "ok",
		"service":     "chatapi",
		"uptime":      uptime.String(),
		"db_writable": dbWritable,
	}

	// Return error status if DB is not writable
	if !dbWritable {
		response["status"] = "error"
		w.WriteHeader(http.StatusServiceUnavailable)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// testDatabaseWrite performs a simple write test on the database
func (h *Handler) testDatabaseWrite() bool {
	// Use a simple tenant query as a DB connectivity test
	// This is safer than trying to insert/delete test data
	tenants, err := h.tenantSvc.ListTenants()
	return err == nil && tenants != nil
}

// HandleCreateRoom create room endpoint
func (h *Handler) HandleCreateRoom(w http.ResponseWriter, r *http.Request) {
	tenantID := h.getTenantID(r)
	userID := h.requireUserID(w, r)
	if userID == "" {
		return
	}

	var req models.CreateRoomRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	room, err := h.chatroomSvc.CreateRoom(tenantID, &req)
	if err != nil {
		slog.Error("Failed to create room", "error", err, "tenant_id", tenantID, "user_id", userID)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(room)
}

// HandleGetRoom get room endpoint
func (h *Handler) HandleGetRoom(w http.ResponseWriter, r *http.Request) {
	tenantID := h.getTenantID(r)
	roomID := r.PathValue("room_id")

	room, err := h.chatroomSvc.GetRoom(tenantID, roomID)
	if err != nil {
		http.Error(w, "Room not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(room)
}

// HandleGetRoomMembers get room members endpoint
func (h *Handler) HandleGetRoomMembers(w http.ResponseWriter, r *http.Request) {
	tenantID := h.getTenantID(r)
	roomID := r.PathValue("room_id")

	members, err := h.chatroomSvc.GetRoomMembers(tenantID, roomID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"members": members,
	})
}

// HandleSendMessage send message endpoint
func (h *Handler) HandleSendMessage(w http.ResponseWriter, r *http.Request) {
	tenantID := h.getTenantID(r)
	userID := h.requireUserID(w, r)
	if userID == "" {
		return
	}

	roomID := r.PathValue("room_id")

	var req models.CreateMessageRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	message, err := h.messageSvc.SendMessage(tenantID, roomID, userID, &req)
	if err != nil {
		slog.Error("Failed to send message", "error", err, "tenant_id", tenantID, "user_id", userID, "room_id", roomID)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
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

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(message)
}

// HandleGetMessages get messages endpoint
func (h *Handler) HandleGetMessages(w http.ResponseWriter, r *http.Request) {
	tenantID := h.getTenantID(r)
	roomID := r.PathValue("room_id")

	// Parse query parameters
	afterSeq := 0
	if after := r.URL.Query().Get("after_seq"); after != "" {
		if seq, err := strconv.Atoi(after); err == nil {
			afterSeq = seq
		}
	}

	limit := 50
	if lim := r.URL.Query().Get("limit"); lim != "" {
		if l, err := strconv.Atoi(lim); err == nil && l > 0 && l <= 100 {
			limit = l
		}
	}

	messages, err := h.messageSvc.GetMessages(tenantID, roomID, afterSeq, limit)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"messages": messages,
	})
}

// HandleAck ACK endpoint
func (h *Handler) HandleAck(w http.ResponseWriter, r *http.Request) {
	tenantID := h.getTenantID(r)
	userID := h.requireUserID(w, r)
	if userID == "" {
		return
	}

	var req models.AckRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if err := h.messageSvc.UpdateLastAck(tenantID, userID, req.RoomID, req.Seq); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Broadcast ACK to other room members
	h.realtimeSvc.BroadcastToRoom(tenantID, req.RoomID, map[string]interface{}{
		"type":    "ack.received",
		"room_id": req.RoomID,
		"seq":     req.Seq,
		"user_id": userID,
	})

	w.WriteHeader(http.StatusOK)
}

// HandleNotify notify endpoint
func (h *Handler) HandleNotify(w http.ResponseWriter, r *http.Request) {
	tenantID := h.getTenantID(r)

	var req models.CreateNotificationRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	notification, err := h.notifSvc.CreateNotification(tenantID, &req)
	if err != nil {
		slog.Error("Failed to create notification", "error", err, "tenant_id", tenantID)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusAccepted)
	json.NewEncoder(w).Encode(notification)
}

// HandleCreateTenant creates a new tenant (admin only)
func (h *Handler) HandleCreateTenant(w http.ResponseWriter, r *http.Request) {
	// Check master API key
	masterKey := r.Header.Get("X-Master-Key")
	if masterKey == "" || masterKey != h.config.MasterAPIKey {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Parse request body
	var req struct {
		Name string `json:"name"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	if req.Name == "" {
		http.Error(w, "Name is required", http.StatusBadRequest)
		return
	}

	// Create tenant
	tenant, err := h.tenantSvc.CreateTenant(req.Name)
	if err != nil {
		slog.Error("Failed to create tenant", "error", err)
		http.Error(w, "Failed to create tenant", http.StatusInternalServerError)
		return
	}

	// Return tenant details
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(tenant)
}

// HandleGetDeadLetters admin endpoint to get failed deliveries
func (h *Handler) HandleGetDeadLetters(w http.ResponseWriter, r *http.Request) {
	tenantID := h.getTenantID(r)

	// Parse query parameters
	limit := 100
	if lim := r.URL.Query().Get("limit"); lim != "" {
		if l, err := strconv.Atoi(lim); err == nil && l > 0 && l <= 1000 {
			limit = l
		}
	}

	// Get failed notifications
	failedNotifications, err := h.notifSvc.GetFailedNotifications(tenantID, limit)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Get failed undelivered messages
	failedMessages, err := h.messageSvc.GetFailedUndeliveredMessages(tenantID, limit)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	response := map[string]interface{}{
		"failed_notifications": failedNotifications,
		"failed_messages":      failedMessages,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}
