package worker

import (
"context"
"log/slog"
"time"

"github.com/hastenr/chatapi/internal/db"
"github.com/hastenr/chatapi/internal/services/delivery"
)

// DeliveryWorker processes undelivered messages and notifications
type DeliveryWorker struct {
db          *db.DB
deliverySvc *delivery.Service
interval    time.Duration
stopCh      chan struct{}
}

// NewDeliveryWorker creates a new delivery worker
func NewDeliveryWorker(db *db.DB, deliverySvc *delivery.Service, interval time.Duration) *DeliveryWorker {
return &DeliveryWorker{
db:          db,
deliverySvc: deliverySvc,
interval:    interval,
stopCh:      make(chan struct{}),
}
}

// Start starts the delivery worker
func (w *DeliveryWorker) Start(ctx context.Context) {
slog.Info("Starting delivery worker", "interval", w.interval)

ticker := time.NewTicker(w.interval)
defer ticker.Stop()

for {
select {
case <-ctx.Done():
slog.Info("Delivery worker stopped")
return
case <-w.stopCh:
slog.Info("Delivery worker stopped")
return
case <-ticker.C:
w.processBatch()
}
}
}

// Stop stops the delivery worker
func (w *DeliveryWorker) Stop() {
close(w.stopCh)
}

// processBatch processes a batch of undelivered messages and notifications
func (w *DeliveryWorker) processBatch() {
// Query all tenants from database
tenants, err := w.getAllTenants()
if err != nil {
slog.Error("Failed to get tenants for processing", "error", err)
return
}

// Process each tenant
for _, tenantID := range tenants {
// Process undelivered messages
if err := w.deliverySvc.ProcessUndeliveredMessages(tenantID, 50); err != nil {
slog.Error("Failed to process undelivered messages", "error", err, "tenant_id", tenantID)
}

// Process notifications
if err := w.deliverySvc.ProcessNotifications(tenantID, 50); err != nil {
slog.Error("Failed to process notifications", "error", err, "tenant_id", tenantID)
}

// Cleanup old entries (older than 30 days)
if err := w.deliverySvc.CleanupOldEntries(tenantID, 30*24*time.Hour); err != nil {
slog.Error("Failed to cleanup old entries", "error", err, "tenant_id", tenantID)
}
}
}

// getAllTenants retrieves all tenant IDs from the database
func (w *DeliveryWorker) getAllTenants() ([]string, error) {
query := `SELECT tenant_id FROM tenants ORDER BY tenant_id`

rows, err := w.db.DB.Query(query)
if err != nil {
return nil, err
}
defer rows.Close()

var tenants []string
for rows.Next() {
var tenantID string
if err := rows.Scan(&tenantID); err != nil {
return nil, err
}
tenants = append(tenants, tenantID)
}

return tenants, rows.Err()
}

// WALCheckpointWorker performs periodic WAL checkpoints
type WALCheckpointWorker struct {
db      *db.DB
interval time.Duration
stopCh   chan struct{}
}

// NewWALCheckpointWorker creates a new WAL checkpoint worker
func NewWALCheckpointWorker(database *db.DB, interval time.Duration) *WALCheckpointWorker {
return &WALCheckpointWorker{
db:       database,
interval: interval,
stopCh:   make(chan struct{}),
}
}

// Start starts the WAL checkpoint worker
func (w *WALCheckpointWorker) Start(ctx context.Context) {
slog.Info("Starting WAL checkpoint worker", "interval", w.interval)

ticker := time.NewTicker(w.interval)
defer ticker.Stop()

for {
select {
case <-ctx.Done():
slog.Info("WAL checkpoint worker stopped")
return
case <-w.stopCh:
slog.Info("WAL checkpoint worker stopped")
return
case <-ticker.C:
if err := db.CheckpointWAL(w.db); err != nil {
slog.Error("Failed to checkpoint WAL", "error", err)
}
}
}
}

// Stop stops the WAL checkpoint worker
func (w *WALCheckpointWorker) Stop() {
close(w.stopCh)
}
