package config

import (
	"os"
	"strconv"
	"time"
)

// Config holds all configuration for the ChatAPI service
type Config struct {
	// Server configuration
	ListenAddr           string
	DataDir              string

	// Database configuration
	DatabaseDSN          string

	// Worker configuration
	WorkerInterval       time.Duration
	RetryMaxAttempts     int
	RetryInterval        time.Duration

	// Shutdown configuration
	ShutdownDrainTimeout time.Duration

	// Logging
	LogLevel             string

	// Rate limiting defaults
	DefaultRateLimit     int // requests per second per tenant

	// Admin configuration
	MasterAPIKey         string
}

// Load loads configuration from environment variables with sensible defaults
func Load() (*Config, error) {
	cfg := &Config{
		ListenAddr:           getEnv("LISTEN_ADDR", ":8080"),
		DataDir:              getEnv("DATA_DIR", "/var/chatapi"),
		LogDir:               getEnv("LOG_DIR", "/var/log/chatapi"),
		DatabaseDSN:          getEnv("DATABASE_DSN", "file:chatapi.db?_journal_mode=WAL&_busy_timeout=5000"),
		LogLevel:             getEnv("LOG_LEVEL", "info"),
		DefaultRateLimit:     getEnvAsInt("DEFAULT_RATE_LIMIT", 100),
		RetryMaxAttempts:     getEnvAsInt("RETRY_MAX_ATTEMPTS", 5),
		ShutdownDrainTimeout: getEnvAsDuration("SHUTDOWN_DRAIN_TIMEOUT", 10*time.Second),
		WorkerInterval:       getEnvAsDuration("WORKER_INTERVAL", 30*time.Second),
		RetryInterval:        getEnvAsDuration("RETRY_INTERVAL", 30*time.Second),
		MasterAPIKey:         getEnv("MASTER_API_KEY", ""),
	}

	return cfg, nil
}

// getEnv gets an environment variable or returns a default value
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// getEnvAsInt gets an environment variable as int or returns a default value
func getEnvAsInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

// getEnvAsDuration gets an environment variable as time.Duration or returns a default value
func getEnvAsDuration(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if duration, err := time.ParseDuration(value); err == nil {
			return duration
		}
	}
	return defaultValue
}