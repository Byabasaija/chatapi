package ratelimit

import (
	"sync"
	"time"
)

// TokenBucket implements a token bucket rate limiter
type TokenBucket struct {
	mu        sync.Mutex
	tokens    float64
	capacity  float64
	refillRate float64 // tokens per second
	lastRefill time.Time
}

// NewTokenBucket creates a new token bucket rate limiter
func NewTokenBucket(capacity float64, refillRate float64) *TokenBucket {
	return &TokenBucket{
		tokens:     capacity,
		capacity:   capacity,
		refillRate: refillRate,
		lastRefill: time.Now(),
	}
}

// Allow checks if a request should be allowed and consumes a token if so
func (tb *TokenBucket) Allow() bool {
	tb.mu.Lock()
	defer tb.mu.Unlock()

	now := time.Now()
	elapsed := now.Sub(tb.lastRefill)
	tb.lastRefill = now

	// Refill tokens based on elapsed time
	tb.tokens += elapsed.Seconds() * tb.refillRate
	if tb.tokens > tb.capacity {
		tb.tokens = tb.capacity
	}

	// Check if we have enough tokens
	if tb.tokens >= 1.0 {
		tb.tokens -= 1.0
		return true
	}

	return false
}

// Tokens returns the current number of tokens (for testing/debugging)
func (tb *TokenBucket) Tokens() float64 {
	tb.mu.Lock()
	defer tb.mu.Unlock()
	return tb.tokens
}

// RateLimiter manages rate limiting per tenant
type RateLimiter struct {
	mu      sync.RWMutex
	buckets map[string]*TokenBucket
}

// NewRateLimiter creates a new rate limiter
func NewRateLimiter() *RateLimiter {
	return &RateLimiter{
		buckets: make(map[string]*TokenBucket),
	}
}

// Allow checks if a tenant's request should be allowed
func (rl *RateLimiter) Allow(tenantID string, capacity float64, refillRate float64) bool {
	rl.mu.Lock()
	defer rl.mu.Unlock()

	bucket, exists := rl.buckets[tenantID]
	if !exists {
		bucket = NewTokenBucket(capacity, refillRate)
		rl.buckets[tenantID] = bucket
	}

	return bucket.Allow()
}

// GetTokens returns current token count for a tenant (for testing/debugging)
func (rl *RateLimiter) GetTokens(tenantID string) float64 {
	rl.mu.RLock()
	defer rl.mu.RUnlock()

	if bucket, exists := rl.buckets[tenantID]; exists {
		return bucket.Tokens()
	}
	return 0
}