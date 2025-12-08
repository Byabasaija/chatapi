package delivery

import (
	"database/sql"
	"fmt"
	"log/slog"
	"time"

	"github.com/yourusername/chatapi/internal/models"
	"github.com/yourusername/chatapi/internal/services/realtime"
)

// Service handles message and notification delivery with retries
type Service struct {
	db         *sql.DB
	realtimeSvc *realtime.Service
	maxAttempts int
}

// NewService creates a new delivery service
func NewService(db *sql.DB, realtimeSvc *realtime.Service) *Service {
	return &Service{
		db:          db,
		realtimeSvc: realtimeSvc,
		maxAttempts: 5,
	}
}

// ProcessUndeliveredMessages processes messages that haven't been delivered yet
func (s *Service) ProcessUndeliveredMessages(tenantID string, limit int) error {
	if limit <= 0 || limit > 100 {
		limit = 50
	}

	query := `
		SELECT id, tenant_id, user_id, chatroom_id, message_id, seq, attempts
		FROM undelivered_messages
		WHERE tenant_id = ? AND attempts < ?
		ORDER BY created_at ASC
		LIMIT ?
	`

	rows, err := s.db.Query(query, tenantID, s.maxAttempts, limit)
	if err != nil {
		return fmt.Errorf("failed to get undelivered messages: %w", err)
	}
	defer rows.Close()

	for rows.Next() {
		var msg models.UndeliveredMessage
		err := rows.Scan(
			&msg.ID,
			&msg.TenantID,
			&msg.UserID,
			&msg.ChatroomID,
			&msg.MessageID,
			&msg.Seq,
			&msg.Attempts,
		)
		if err != nil {
			slog.Error("Failed to scan undelivered message", "error", err)
			continue
		}

		if err := s.attemptMessageDelivery(&msg); err != nil {
			slog.Warn("Failed to deliver message",
				"message_id", msg.MessageID,
				"user_id", msg.UserID,
				"attempts", msg.Attempts,
				"error", err)
		}
	}

	return nil
}

// attemptMessageDelivery tries to deliver a message to a user
func (s *Service) attemptMessageDelivery(msg *models.UndeliveredMessage) error {
	// Check if user is online
	if s.realtimeSvc.IsUserOnline(msg.TenantID, msg.UserID) {
		// Get the full message to send
		fullMsg, err := s.getMessage(msg.TenantID, msg.MessageID)
		if err != nil {
			return fmt.Errorf("failed to get message: %w", err)
		}

		// Send via WebSocket
		messagePayload := map[string]interface{}{
			"type":        "message",
			"room_id":     msg.ChatroomID,
			"seq":         msg.Seq,
			"message_id":  msg.MessageID,
			"sender_id":   fullMsg.SenderID,
			"content":     fullMsg.Content,
			"created_at":  fullMsg.CreatedAt.Format(time.RFC3339),
		}

		if fullMsg.Meta != "" {
			messagePayload["meta"] = fullMsg.Meta
		}

		s.realtimeSvc.SendToUser(msg.TenantID, msg.UserID, messagePayload)

		// Mark as delivered
		return s.markMessageDelivered(msg.ID)
	}

	// User is offline, increment attempts
	return s.incrementMessageAttempts(msg.ID)
}

// ProcessNotifications processes pending notifications
func (s *Service) ProcessNotifications(tenantID string, limit int) error {
	if limit <= 0 || limit > 100 {
		limit = 50
	}

	query := `
		SELECT notification_id, tenant_id, topic, payload, attempts
		FROM notifications
		WHERE tenant_id = ? AND status IN ('pending', 'processing') AND attempts < ?
		ORDER BY created_at ASC
		LIMIT ?
	`

	rows, err := s.db.Query(query, tenantID, s.maxAttempts, limit)
	if err != nil {
		return fmt.Errorf("failed to get pending notifications: %w", err)
	}
	defer rows.Close()

	for rows.Next() {
		var notif models.Notification
		err := rows.Scan(
			&notif.NotificationID,
			&notif.TenantID,
			&notif.Topic,
			&notif.Payload,
			&notif.Attempts,
		)
		if err != nil {
			slog.Error("Failed to scan notification", "error", err)
			continue
		}

		if err := s.attemptNotificationDelivery(&notif); err != nil {
			slog.Warn("Failed to deliver notification",
				"notification_id", notif.NotificationID,
				"topic", notif.Topic,
				"attempts", notif.Attempts,
				"error", err)
		}
	}

	return nil
}

// attemptNotificationDelivery tries to deliver a notification
func (s *Service) attemptNotificationDelivery(notif *models.Notification) error {
	// For now, broadcast to all online users in the tenant
	// In a more sophisticated implementation, you'd look up subscribers
	// and send to specific users or endpoints

	notificationPayload := map[string]interface{}{
		"type":            "notification",
		"notification_id": notif.NotificationID,
		"topic":           notif.Topic,
		"payload":         notif.Payload,
		"timestamp":       time.Now().Unix(),
	}

	// Get online users and send to them
	onlineUsers := s.realtimeSvc.GetOnlineUsers(notif.TenantID)
	for _, userID := range onlineUsers {
		s.realtimeSvc.SendToUser(notif.TenantID, userID, notificationPayload)
	}

	// Mark as delivered (simplified - in reality, you'd track per-user delivery)
	return s.markNotificationDelivered(notif.NotificationID)
}

// CleanupOldEntries removes old delivered entries to prevent unbounded growth
func (s *Service) CleanupOldEntries(tenantID string, maxAge time.Duration) error {
	cutoffTime := time.Now().Add(-maxAge)

	// Clean up old undelivered messages that are marked as delivered
	// (In practice, you'd have a separate delivered_messages table)

	// For now, just clean up very old undelivered messages that have exceeded max attempts
	query := `
		DELETE FROM undelivered_messages
		WHERE tenant_id = ? AND attempts >= ? AND created_at < ?
	`

	_, err := s.db.Exec(query, tenantID, s.maxAttempts, cutoffTime)
	if err != nil {
		return fmt.Errorf("failed to cleanup old undelivered messages: %w", err)
	}

	// Clean up old dead notifications
	notifQuery := `
		DELETE FROM notifications
		WHERE tenant_id = ? AND status = 'dead' AND created_at < ?
	`

	_, err = s.db.Exec(notifQuery, tenantID, cutoffTime)
	if err != nil {
		return fmt.Errorf("failed to cleanup old notifications: %w", err)
	}

	slog.Info("Cleaned up old delivery entries",
		"tenant_id", tenantID,
		"max_age", maxAge)

	return nil
}

// Helper methods

func (s *Service) getMessage(tenantID, messageID string) (*models.Message, error) {
	var msg models.Message
	query := `
		SELECT message_id, tenant_id, chatroom_id, sender_id, seq, content, meta, created_at
		FROM messages
		WHERE tenant_id = ? AND message_id = ?
	`

	err := s.db.QueryRow(query, tenantID, messageID).Scan(
		&msg.MessageID,
		&msg.TenantID,
		&msg.ChatroomID,
		&msg.SenderID,
		&msg.Seq,
		&msg.Content,
		&msg.Meta,
		&msg.CreatedAt,
	)

	if err != nil {
		return nil, err
	}

	return &msg, nil
}

func (s *Service) markMessageDelivered(id int) error {
	query := `DELETE FROM undelivered_messages WHERE id = ?`
	_, err := s.db.Exec(query, id)
	return err
}

func (s *Service) incrementMessageAttempts(id int) error {
	query := `
		UPDATE undelivered_messages
		SET attempts = attempts + 1, last_attempt_at = CURRENT_TIMESTAMP
		WHERE id = ?
	`
	_, err := s.db.Exec(query, id)
	return err
}

func (s *Service) markNotificationDelivered(notificationID string) error {
	query := `
		UPDATE notifications
		SET status = 'delivered', last_attempt_at = CURRENT_TIMESTAMP
		WHERE notification_id = ?
	`
	_, err := s.db.Exec(query, notificationID)
	return err
}