package chatroom

import (
	"database/sql"
	"fmt"
	"log/slog"
	"sort"

	"github.com/Byabasaija/chatapi/internal/models"
	"github.com/google/uuid"
)

// Service handles chatroom operations
type Service struct {
	db *sql.DB
}

// NewService creates a new chatroom service
func NewService(db *sql.DB) *Service {
	return &Service{db: db}
}

// CreateRoom creates a new chatroom
func (s *Service) CreateRoom(tenantID string, req *models.CreateRoomRequest) (*models.Room, error) {
	var room *models.Room
	var err error

	switch req.Type {
	case "dm":
		room, err = s.createDMRoom(tenantID, req)
	case "group", "channel":
		room, err = s.createGroupRoom(tenantID, req)
	default:
		return nil, fmt.Errorf("invalid room type: %s", req.Type)
	}

	if err != nil {
		return nil, err
	}

	// Add members to the room
	if err := s.addMembers(tenantID, room.RoomID, req.Members); err != nil {
		return nil, fmt.Errorf("failed to add members: %w", err)
	}

	slog.Info("Created room", "tenant_id", tenantID, "room_id", room.RoomID, "type", req.Type)
	return room, nil
}

// createDMRoom creates a DM room with deterministic unique_key
func (s *Service) createDMRoom(tenantID string, req *models.CreateRoomRequest) (*models.Room, error) {
	if len(req.Members) != 2 {
		return nil, fmt.Errorf("DM rooms must have exactly 2 members")
	}

	// Sort members for deterministic key
	members := make([]string, len(req.Members))
	copy(members, req.Members)
	sort.Strings(members)

	uniqueKey := fmt.Sprintf("dm:%s:%s", members[0], members[1])

	// Check if DM already exists
	var existingRoom models.Room
	query := `
		SELECT room_id, tenant_id, type, unique_key, name, last_seq, created_at
		FROM rooms
		WHERE tenant_id = ? AND unique_key = ?
	`

	err := s.db.QueryRow(query, tenantID, uniqueKey).Scan(
		&existingRoom.RoomID,
		&existingRoom.TenantID,
		&existingRoom.Type,
		&existingRoom.UniqueKey,
		&existingRoom.Name,
		&existingRoom.LastSeq,
		&existingRoom.CreatedAt,
	)

	if err == nil {
		// Room already exists
		return &existingRoom, nil
	}

	if err != sql.ErrNoRows {
		return nil, fmt.Errorf("failed to check existing DM: %w", err)
	}

	// Create new DM room
	roomID := generateRoomID()
	room := &models.Room{
		RoomID:    roomID,
		TenantID:  tenantID,
		Type:      "dm",
		UniqueKey: uniqueKey,
		Name:      req.Name, // Optional custom name for DMs
		LastSeq:   0,
	}

	insertQuery := `
		INSERT INTO rooms (room_id, tenant_id, type, unique_key, name, last_seq)
		VALUES (?, ?, ?, ?, ?, ?)
	`

	_, err = s.db.Exec(insertQuery, room.RoomID, room.TenantID, room.Type, room.UniqueKey, room.Name, room.LastSeq)
	if err != nil {
		return nil, fmt.Errorf("failed to create DM room: %w", err)
	}

	return room, nil
}

// createGroupRoom creates a group or channel room
func (s *Service) createGroupRoom(tenantID string, req *models.CreateRoomRequest) (*models.Room, error) {
	if len(req.Members) < 2 {
		return nil, fmt.Errorf("group/channel rooms must have at least 2 members")
	}

	roomID := generateRoomID()
	room := &models.Room{
		RoomID:   roomID,
		TenantID: tenantID,
		Type:     req.Type,
		Name:     req.Name,
		LastSeq:  0,
	}

	query := `
		INSERT INTO rooms (room_id, tenant_id, type, name, last_seq)
		VALUES (?, ?, ?, ?, ?)
	`

	_, err := s.db.Exec(query, room.RoomID, room.TenantID, room.Type, room.Name, room.LastSeq)
	if err != nil {
		return nil, fmt.Errorf("failed to create group room: %w", err)
	}

	return room, nil
}

// addMembers adds members to a room
func (s *Service) addMembers(tenantID, roomID string, userIDs []string) error {
	if len(userIDs) == 0 {
		return nil
	}

	// Use a transaction for atomicity
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	query := `
		INSERT INTO room_members (chatroom_id, tenant_id, user_id, role)
		VALUES (?, ?, ?, 'member')
	`

	for _, userID := range userIDs {
		_, err = tx.Exec(query, roomID, tenantID, userID)
		if err != nil {
			return fmt.Errorf("failed to add member %s: %w", userID, err)
		}
	}

	return tx.Commit()
}

// GetRoom retrieves a room by ID
func (s *Service) GetRoom(tenantID, roomID string) (*models.Room, error) {
	var room models.Room
	query := `
		SELECT room_id, tenant_id, type, unique_key, name, last_seq, created_at
		FROM rooms
		WHERE tenant_id = ? AND room_id = ?
	`

	err := s.db.QueryRow(query, tenantID, roomID).Scan(
		&room.RoomID,
		&room.TenantID,
		&room.Type,
		&room.UniqueKey,
		&room.Name,
		&room.LastSeq,
		&room.CreatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("room not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get room: %w", err)
	}

	return &room, nil
}

// GetRoomMembers retrieves all members of a room
func (s *Service) GetRoomMembers(tenantID, roomID string) ([]*models.RoomMember, error) {
	query := `
		SELECT chatroom_id, tenant_id, user_id, role, joined_at
		FROM room_members
		WHERE tenant_id = ? AND chatroom_id = ?
		ORDER BY joined_at
	`

	rows, err := s.db.Query(query, tenantID, roomID)
	if err != nil {
		return nil, fmt.Errorf("failed to get room members: %w", err)
	}
	defer rows.Close()

	var members []*models.RoomMember
	for rows.Next() {
		var member models.RoomMember
		err := rows.Scan(
			&member.ChatroomID,
			&member.TenantID,
			&member.UserID,
			&member.Role,
			&member.JoinedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan member: %w", err)
		}
		members = append(members, &member)
	}

	return members, nil
}

// AddMember adds a single member to a room
func (s *Service) AddMember(tenantID, roomID, userID string) error {
	query := `
		INSERT INTO room_members (chatroom_id, tenant_id, user_id, role)
		VALUES (?, ?, ?, 'member')
	`

	_, err := s.db.Exec(query, roomID, tenantID, userID)
	if err != nil {
		return fmt.Errorf("failed to add member: %w", err)
	}

	slog.Info("Added member to room", "tenant_id", tenantID, "room_id", roomID, "user_id", userID)
	return nil
}

// RemoveMember removes a member from a room
func (s *Service) RemoveMember(tenantID, roomID, userID string) error {
	query := `
		DELETE FROM room_members
		WHERE tenant_id = ? AND chatroom_id = ? AND user_id = ?
	`

	result, err := s.db.Exec(query, tenantID, roomID, userID)
	if err != nil {
		return fmt.Errorf("failed to remove member: %w", err)
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to get rows affected: %w", err)
	}

	if rowsAffected == 0 {
		return fmt.Errorf("member not found in room")
	}

	slog.Info("Removed member from room", "tenant_id", tenantID, "room_id", roomID, "user_id", userID)
	return nil
}

// generateRoomID generates a unique room ID
// In a real implementation, this would use UUID or similar
func generateRoomID() string {
	return uuid.New().String()
}
