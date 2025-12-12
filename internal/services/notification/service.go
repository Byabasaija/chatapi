package notification

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log/slog"
	"time"

	"github.com/Byabasaija/chatapi/internal/models"
	"github.com/google/uuid"
)

// Service handles durable notifications
type Service struct {
	db *sql.DB
}

// NewService creates a new notification service
func NewService(db *sql.DB) *Service {
	return &Service{db: db}
}

// CreateNotification creates a new durable notification
func (s *Service) CreateNotification(tenantID string, req *models.CreateNotificationRequest) (*models.Notification, error) {
	// Generate notification ID
	notificationID := generateNotificationID()

	// Marshal payload
	payloadJSON, err := json.Marshal(req.Payload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal payload: %w", err)
	}

	// Insert notification
	query := `
		INSERT INTO notifications (notification_id, tenant_id, topic, payload, status)
		VALUES (?, ?, ?, ?, 'pending')
	`

	_, err = s.db.Exec(query, notificationID, tenantID, req.Topic, string(payloadJSON))
	if err != nil {
		return nil, fmt.Errorf("failed to create notification: %w", err)
	}

	notification := &models.Notification{
		NotificationID: notificationID,
		TenantID:       tenantID,
		Topic:          req.Topic,
		Payload:        string(payloadJSON),
		Status:         "pending",
		Attempts:       0,
		CreatedAt:      time.Now(),
	}

	slog.Info("Created notification",
		"tenant_id", tenantID,
		"notification_id", notificationID,
		"topic", req.Topic)

	return notification, nil
}

// GetPendingNotifications gets notifications ready for delivery
func (s *Service) GetPendingNotifications(tenantID string, limit int) ([]*models.Notification, error) {
	if limit <= 0 || limit > 100 {
		limit = 50
	}

	query := `
		SELECT notification_id, tenant_id, topic, payload, created_at, status, attempts, last_attempt_at
		FROM notifications
		WHERE tenant_id = ? AND status IN ('pending', 'processing')
		ORDER BY created_at ASC
		LIMIT ?
	`

	rows, err := s.db.Query(query, tenantID, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to get pending notifications: %w", err)
	}
	defer rows.Close()

	var notifications []*models.Notification
	for rows.Next() {
		var n models.Notification
		err := rows.Scan(
			&n.NotificationID,
			&n.TenantID,
			&n.Topic,
			&n.Payload,
			&n.CreatedAt,
			&n.Status,
			&n.Attempts,
			&n.LastAttemptAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan notification: %w", err)
		}
		notifications = append(notifications, &n)
	}

	return notifications, nil
}

// MarkNotificationDelivered marks a notification as delivered
func (s *Service) MarkNotificationDelivered(notificationID string) error {
	query := `
		UPDATE notifications
		SET status = 'delivered', last_attempt_at = CURRENT_TIMESTAMP
		WHERE notification_id = ?
	`

	_, err := s.db.Exec(query, notificationID)
	if err != nil {
		return fmt.Errorf("failed to mark notification delivered: %w", err)
	}

	return nil
}

// MarkNotificationFailed marks a notification as failed and increments attempts
func (s *Service) MarkNotificationFailed(notificationID string) error {
	query := `
		UPDATE notifications
		SET status = CASE WHEN attempts >= 4 THEN 'dead' ELSE 'pending' END,
			attempts = attempts + 1,
			last_attempt_at = CURRENT_TIMESTAMP
		WHERE notification_id = ?
	`

	_, err := s.db.Exec(query, notificationID)
	if err != nil {
		return fmt.Errorf("failed to mark notification failed: %w", err)
	}

	return nil
}

// GetNotificationSubscribers gets subscribers for a topic
func (s *Service) GetNotificationSubscribers(tenantID, topic string) ([]*models.NotificationSubscription, error) {
	query := `
		SELECT id, tenant_id, subscriber_id, topic, endpoint, metadata, created_at
		FROM notification_subscriptions
		WHERE tenant_id = ? AND topic = ?
	`

	rows, err := s.db.Query(query, tenantID, topic)
	if err != nil {
		return nil, fmt.Errorf("failed to get notification subscribers: %w", err)
	}
	defer rows.Close()

	var subscribers []*models.NotificationSubscription
	for rows.Next() {
		var sub models.NotificationSubscription
		err := rows.Scan(
			&sub.ID,
			&sub.TenantID,
			&sub.SubscriberID,
			&sub.Topic,
			&sub.Endpoint,
			&sub.Metadata,
			&sub.CreatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan subscriber: %w", err)
		}
		subscribers = append(subscribers, &sub)
	}

	return subscribers, nil
}

// generateNotificationID generates a unique notification ID
func generateNotificationID() string {
	return uuid.New().String()
}
