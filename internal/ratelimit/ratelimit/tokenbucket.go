package ratelimit

import (
	"sync"
	"time"
)

// TokenBucket implements a token bucket rate limiter
type TokenBucket struct {
	mu        sync.Mutex
	tokens    int
	capacity  int
	refillRate time.Duration // time between token refills
	lastRefill time.Time
}

// NewTokenBucket creates a new token bucket rate limiter
// rate: tokens per second
// capacity: maximum tokens in bucket
func NewTokenBucket(rate, capacity int) *TokenBucket {
	return &TokenBucket{
		tokens:     capacity,
		capacity:   capacity,
		refillRate: time.Second / time.Duration(rate),
		lastRefill: time.Now(),
	}
}

// Allow checks if a request should be allowed and consumes a token
func (tb *TokenBucket) Allow() bool {
	tb.mu.Lock()
	defer tb.mu.Unlock()

	now := time.Now()
	elapsed := now.Sub(tb.lastRefill)

	// Calculate how many tokens to add
	tokensToAdd := int(elapsed / tb.refillRate)
	if tokensToAdd > 0 {
		tb.tokens += tokensToAdd
		if tb.tokens > tb.capacity {
			tb.tokens = tb.capacity
		}
		tb.lastRefill = now
	}

	// Check if we have a token to spend
	if tb.tokens > 0 {
		tb.tokens--
		return true
	}

	return false
}

// Tokens returns the current number of tokens in the bucket
func (tb *TokenBucket) Tokens() int {
	tb.mu.Lock()
	defer tb.mu.Unlock()
	return tb.tokens
}