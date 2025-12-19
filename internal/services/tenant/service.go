package tenant

import (
	"crypto/rand"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"log/slog"
	"sync"

	"github.com/hastenr/chatapi/internal/models"
	"github.com/hastenr/chatapi/internal/ratelimit"
)

// Service handles tenant operations
type Service struct {
	db            *sql.DB
	rateLimiters  sync.Map // map[string]*ratelimit.TokenBucket
	defaultRateLimit int
}

// TenantConfig represents per-tenant configuration
type TenantConfig struct {
	MaxMessageSize int `json:"max_message_size"`
	RetryLimit     int `json:"retry_limit"`
	DurableNotifications bool `json:"durable_notifications"`
	RateLimit      int `json:"rate_limit"` // requests per second
}

// NewService creates a new tenant service
func NewService(db *sql.DB) *Service {
	return &Service{
		db:               db,
		defaultRateLimit: 100, // requests per second
	}
}

// ValidateAPIKey validates an API key and returns the tenant
func (s *Service) ValidateAPIKey(apiKey string) (*models.Tenant, error) {
	var tenant models.Tenant
	query := `
		SELECT tenant_id, api_key, name, config, created_at
		FROM tenants
		WHERE api_key = ?
	`

	err := s.db.QueryRow(query, apiKey).Scan(
		&tenant.TenantID,
		&tenant.APIKey,
		&tenant.Name,
		&tenant.Config,
		&tenant.CreatedAt,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("invalid API key")
	}
	if err != nil {
		slog.Error("Failed to validate API key", "error", err)
		return nil, fmt.Errorf("database error")
	}

	return &tenant, nil
}

// CreateTenant creates a new tenant with a generated API key
func (s *Service) CreateTenant(name string) (*models.Tenant, error) {
	// Generate tenant ID (UUID)
	tenantID := generateTenantID()

	// Generate API key (32-byte random hex)
	apiKey := generateAPIKey()

	// Default config
	config := TenantConfig{
		MaxMessageSize:       1000,
		RetryLimit:           5,
		DurableNotifications: true,
		RateLimit:            s.defaultRateLimit,
	}
	configJSON, err := json.Marshal(config)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal config: %w", err)
	}

	// Insert tenant
	query := `
		INSERT INTO tenants (tenant_id, api_key, name, config)
		VALUES (?, ?, ?, ?)
	`
	_, err = s.db.Exec(query, tenantID, apiKey, name, string(configJSON))
	if err != nil {
		slog.Error("Failed to create tenant", "error", err)
		return nil, fmt.Errorf("failed to create tenant: %w", err)
	}

	tenant := &models.Tenant{
		TenantID: tenantID,
		APIKey:   apiKey,
		Name:     name,
		Config:   string(configJSON),
	}

	slog.Info("Tenant created", "tenant_id", tenantID, "name", name)
	return tenant, nil
}

// generateTenantID generates a unique tenant ID
func generateTenantID() string {
	return fmt.Sprintf("tenant_%s", generateRandomHex(8))
}

// generateAPIKey generates a random API key
func generateAPIKey() string {
	return generateRandomHex(32)
}

// generateRandomHex generates a random hex string of given byte length
func generateRandomHex(length int) string {
	bytes := make([]byte, length)
	if _, err := rand.Read(bytes); err != nil {
		panic("failed to generate random bytes")
	}
	return hex.EncodeToString(bytes)
}

// GetTenantConfig returns the configuration for a tenant
func (s *Service) GetTenantConfig(tenantID string) (*TenantConfig, error) {
	var configJSON string
	query := `SELECT config FROM tenants WHERE tenant_id = ?`

	err := s.db.QueryRow(query, tenantID).Scan(&configJSON)
	if err != nil {
		return nil, fmt.Errorf("failed to get tenant config: %w", err)
	}

	config := &TenantConfig{
		MaxMessageSize:      4096, // 4KB default
		RetryLimit:          5,
		DurableNotifications: true,
		RateLimit:           s.defaultRateLimit,
	}

	if configJSON != "" {
		if err := json.Unmarshal([]byte(configJSON), config); err != nil {
			slog.Warn("Failed to parse tenant config, using defaults", "tenant_id", tenantID, "error", err)
		}
	}

	return config, nil
}

// CheckRateLimit checks if a tenant is within their rate limit
func (s *Service) CheckRateLimit(tenantID string) error {
	// Get or create rate limiter for this tenant
	rateLimiter, exists := s.rateLimiters.Load(tenantID)
	if !exists {
		config, err := s.GetTenantConfig(tenantID)
		var bucket *ratelimit.TokenBucket
		if err != nil {
			slog.Warn("Failed to get tenant config for rate limiting, using default", "tenant_id", tenantID, "error", err)
			bucket = ratelimit.NewTokenBucket(float64(s.defaultRateLimit), float64(s.defaultRateLimit)/2.0)
		} else {
			bucket = ratelimit.NewTokenBucket(float64(config.RateLimit), float64(config.RateLimit)/2.0)
		}
		s.rateLimiters.Store(tenantID, bucket)
		rateLimiter = bucket
	}

	bucket := rateLimiter.(*ratelimit.TokenBucket)

	if !bucket.Allow() {
		return fmt.Errorf("rate limit exceeded")
	}

	return nil
}

// ListTenants returns all tenants (admin operation)
func (s *Service) ListTenants() ([]*models.Tenant, error) {
	query := `SELECT tenant_id, api_key, name, config, created_at FROM tenants ORDER BY created_at DESC`

	rows, err := s.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to list tenants: %w", err)
	}
	defer rows.Close()

	var tenants []*models.Tenant
	for rows.Next() {
		var tenant models.Tenant
		err := rows.Scan(
			&tenant.TenantID,
			&tenant.APIKey,
			&tenant.Name,
			&tenant.Config,
			&tenant.CreatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan tenant: %w", err)
		}
		tenants = append(tenants, &tenant)
	}

	return tenants, nil
}