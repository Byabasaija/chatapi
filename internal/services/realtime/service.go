package realtime

import (
	"context"
	"database/sql"
	"encoding/json"
	"log/slog"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

// Service manages WebSocket connections and real-time messaging
type Service struct {
	mu           sync.RWMutex
	db           *sql.DB
	connections  map[string]map[string][]*websocket.Conn // tenant -> user -> connections
	presence     map[string]map[string]time.Time         // tenant -> user -> last seen
	broadcastCh  chan *broadcastMessage
	shutdownCh   chan struct{}
	shutdownOnce sync.Once
}

type broadcastMessage struct {
	tenantID string
	roomID   string
	message  interface{}
}

// NewService creates a new realtime service
func NewService(db *sql.DB) *Service {
	s := &Service{
		db:          db,
		connections: make(map[string]map[string][]*websocket.Conn),
		presence:    make(map[string]map[string]time.Time),
		broadcastCh: make(chan *broadcastMessage, 1000), // buffered channel
		shutdownCh:  make(chan struct{}),
	}

	// Start broadcast worker
	go s.broadcastWorker()

	// Start presence cleanup worker
	go s.presenceCleanupWorker()

	return s
}

// RegisterConnection registers a new WebSocket connection for a user
func (s *Service) RegisterConnection(tenantID, userID string, conn *websocket.Conn) {
	s.mu.Lock()
	defer s.mu.Unlock()

	// Initialize tenant map if needed
	if s.connections[tenantID] == nil {
		s.connections[tenantID] = make(map[string][]*websocket.Conn)
	}

	// Add connection
	s.connections[tenantID][userID] = append(s.connections[tenantID][userID], conn)

	// Update presence
	if s.presence[tenantID] == nil {
		s.presence[tenantID] = make(map[string]time.Time)
	}
	s.presence[tenantID][userID] = time.Now()

	slog.Info("WebSocket connection registered",
		"tenant_id", tenantID,
		"user_id", userID,
		"total_connections", len(s.connections[tenantID][userID]))
}

// UnregisterConnection removes a WebSocket connection for a user
func (s *Service) UnregisterConnection(tenantID, userID string, conn *websocket.Conn) {
	s.mu.Lock()
	defer s.mu.Unlock()

	connections, exists := s.connections[tenantID][userID]
	if !exists {
		return
	}

	// Remove the specific connection
	for i, c := range connections {
		if c == conn {
			// Remove connection from slice
			s.connections[tenantID][userID] = append(connections[:i], connections[i+1:]...)
			break
		}
	}

	// If no more connections for this user, update presence with grace period
	if len(s.connections[tenantID][userID]) == 0 {
		delete(s.connections[tenantID], userID)
		// Keep presence for 5 seconds to handle quick reconnects
		time.AfterFunc(5*time.Second, func() {
			s.mu.Lock()
			if presenceTime, exists := s.presence[tenantID][userID]; exists {
				if time.Since(presenceTime) >= 5*time.Second {
					delete(s.presence[tenantID], userID)
					s.broadcastPresenceUpdate(tenantID, userID, "offline")
				}
			}
			s.mu.Unlock()
		})
	}

	slog.Info("WebSocket connection unregistered",
		"tenant_id", tenantID,
		"user_id", userID,
		"remaining_connections", len(s.connections[tenantID][userID]))
}

// BroadcastToRoom broadcasts a message to all users in a room
func (s *Service) BroadcastToRoom(tenantID, roomID string, message interface{}) {
	select {
	case s.broadcastCh <- &broadcastMessage{
		tenantID: tenantID,
		roomID:   roomID,
		message:  message,
	}:
	default:
		slog.Warn("Broadcast channel full, dropping message",
			"tenant_id", tenantID,
			"room_id", roomID)
	}
}

// SendToUser sends a message directly to a specific user
func (s *Service) SendToUser(tenantID, userID string, message interface{}) {
	s.mu.RLock()
	connections, exists := s.connections[tenantID][userID]
	s.mu.RUnlock()

	if !exists || len(connections) == 0 {
		slog.Debug("No connections found for user, message not delivered",
			"tenant_id", tenantID,
			"user_id", userID)
		return
	}

	messageBytes, err := json.Marshal(message)
	if err != nil {
		slog.Error("Failed to marshal message for user",
			"tenant_id", tenantID,
			"user_id", userID,
			"error", err)
		return
	}

	for _, conn := range connections {
		if err := conn.WriteMessage(websocket.TextMessage, messageBytes); err != nil {
			slog.Warn("Failed to send message to user connection",
				"tenant_id", tenantID,
				"user_id", userID,
				"error", err)
			// Connection might be dead, but we'll let the connection handler deal with it
		}
	}
}

// IsUserOnline checks if a user has active connections
func (s *Service) IsUserOnline(tenantID, userID string) bool {
	s.mu.RLock()
	defer s.mu.RUnlock()

	connections, exists := s.connections[tenantID][userID]
	return exists && len(connections) > 0
}

// GetOnlineUsers returns all currently online users for a tenant
func (s *Service) GetOnlineUsers(tenantID string) []string {
	s.mu.RLock()
	defer s.mu.RUnlock()

	var onlineUsers []string
	if tenantPresence, exists := s.presence[tenantID]; exists {
		for userID := range tenantPresence {
			if s.IsUserOnline(tenantID, userID) {
				onlineUsers = append(onlineUsers, userID)
			}
		}
	}

	return onlineUsers
}

// BroadcastPresenceUpdate broadcasts presence changes
func (s *Service) BroadcastPresenceUpdate(tenantID, userID, status string) {
	s.broadcastPresenceUpdate(tenantID, userID, status)
}

// broadcastPresenceUpdate sends presence updates to relevant users
func (s *Service) broadcastPresenceUpdate(tenantID, userID, status string) {
	presenceMsg := map[string]interface{}{
		"type":      "presence.update",
		"user_id":   userID,
		"status":    status,
		"timestamp": time.Now().Unix(),
	}

	// For now, broadcast to all connected users in the tenant
	// In a more sophisticated implementation, you might track which users
	// are subscribed to which presence updates
	s.mu.RLock()
	tenantConnections := s.connections[tenantID]
	s.mu.RUnlock()

	messageBytes, err := json.Marshal(presenceMsg)
	if err != nil {
		slog.Error("Failed to marshal presence message", "error", err)
		return
	}

	for _, connections := range tenantConnections {
		for _, conn := range connections {
			if err := conn.WriteMessage(websocket.TextMessage, messageBytes); err != nil {
				slog.Warn("Failed to send presence update", "error", err)
			}
		}
	}
}

// broadcastWorker processes broadcast messages
func (s *Service) broadcastWorker() {
	for {
		select {
		case msg := <-s.broadcastCh:
			s.processBroadcast(msg)
		case <-s.shutdownCh:
			return
		}
	}
}

// processBroadcast handles a single broadcast message
func (s *Service) processBroadcast(msg *broadcastMessage) {
	// Query room members from database
	roomMembers, err := s.getRoomMembers(msg.tenantID, msg.roomID)
	if err != nil {
		slog.Error("Failed to get room members for broadcast",
			"tenant_id", msg.tenantID,
			"room_id", msg.roomID,
			"error", err)
		return
	}

	messageBytes, err := json.Marshal(msg.message)
	if err != nil {
		slog.Error("Failed to marshal broadcast message",
			"tenant_id", msg.tenantID,
			"room_id", msg.roomID,
			"error", err)
		return
	}

	s.mu.RLock()
	tenantConnections := s.connections[msg.tenantID]
	s.mu.RUnlock()

	// Only broadcast to room members who are connected
	for _, memberID := range roomMembers {
		if connections, exists := tenantConnections[memberID]; exists {
			for _, conn := range connections {
				if err := conn.WriteMessage(websocket.TextMessage, messageBytes); err != nil {
					slog.Warn("Failed to broadcast message to user",
						"tenant_id", msg.tenantID,
						"user_id", memberID,
						"room_id", msg.roomID,
						"error", err)
				}
			}
		}
	}
}

// getRoomMembers retrieves the list of user IDs who are members of a room
func (s *Service) getRoomMembers(tenantID, roomID string) ([]string, error) {
	query := `
		SELECT user_id
		FROM room_members
		WHERE tenant_id = ? AND chatroom_id = ?
	`

	rows, err := s.db.Query(query, tenantID, roomID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var members []string
	for rows.Next() {
		var userID string
		if err := rows.Scan(&userID); err != nil {
			return nil, err
		}
		members = append(members, userID)
	}

	return members, rows.Err()
}

	for {
		select {
		case <-ticker.C:
			s.cleanupStalePresence()
		case <-s.shutdownCh:
			return
		}
	}
}

// cleanupStalePresence removes presence entries for users who haven't been seen recently
func (s *Service) cleanupStalePresence() {
	s.mu.Lock()
	defer s.mu.Unlock()

	now := time.Now()
	staleThreshold := 5 * time.Minute // Consider users offline after 5 minutes of no activity

	for tenantID, tenantPresence := range s.presence {
		for userID, lastSeen := range tenantPresence {
			if now.Sub(lastSeen) > staleThreshold && !s.IsUserOnline(tenantID, userID) {
				delete(s.presence[tenantID], userID)
				slog.Debug("Cleaned up stale presence",
					"tenant_id", tenantID,
					"user_id", userID)
			}
		}
	}
}

// Shutdown gracefully shuts down the realtime service
func (s *Service) Shutdown(ctx context.Context) error {
	s.shutdownOnce.Do(func() {
		close(s.shutdownCh)
	})

	// Close all connections
	s.mu.Lock()
	defer s.mu.Unlock()

	shutdownMsg := map[string]interface{}{
		"type":             "server.shutdown",
		"reconnect_after_ms": 5000,
	}

	messageBytes, _ := json.Marshal(shutdownMsg)

	for tenantID, tenantConnections := range s.connections {
		for userID, connections := range tenantConnections {
			for _, conn := range connections {
				conn.WriteMessage(websocket.TextMessage, messageBytes)
				conn.Close()
			}
			slog.Info("Closed connections for user",
				"tenant_id", tenantID,
				"user_id", userID,
				"connections_closed", len(connections))
		}
	}

	// Clear connection maps
	s.connections = make(map[string]map[string][]*websocket.Conn)
	s.presence = make(map[string]map[string]time.Time)

	return nil
}