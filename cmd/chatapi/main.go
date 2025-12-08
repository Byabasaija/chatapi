package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/yourusername/chatapi/internal/config"
	"github.com/yourusername/chatapi/internal/db"
	"github.com/yourusername/chatapi/internal/services/delivery"
	"github.com/yourusername/chatapi/internal/services/realtime"
	"github.com/yourusername/chatapi/internal/services/tenant"
	"github.com/yourusername/chatapi/internal/transport"
	"github.com/yourusername/chatapi/internal/worker"
)

func main() {
	// Initialize structured logging
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level: slog.LevelInfo,
	}))
	slog.SetDefault(logger)

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		slog.Error("Failed to load config", "error", err)
		os.Exit(1)
	}

	// Initialize database
	database, err := db.New(cfg.DatabaseDSN)
	if err != nil {
		slog.Error("Failed to initialize database", "error", err)
		os.Exit(1)
	}
	defer database.Close()

	// Run migrations
	if err := db.RunMigrations(database); err != nil {
		slog.Error("Failed to run migrations", "error", err)
		os.Exit(1)
	}

	// Initialize services
	tenantSvc := tenant.NewService(database)
	realtimeSvc := realtime.NewService()
	deliverySvc := delivery.NewService(database, realtimeSvc)

	// Initialize workers
	deliveryWorker := worker.NewDeliveryWorker(deliverySvc, cfg.WorkerInterval)

	// Start background workers
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	deliveryWorker.Start(ctx)

	// Initialize HTTP server
	server := transport.NewServer(cfg, tenantSvc, realtimeSvc, deliverySvc)

	// Handle graceful shutdown
	shutdown := make(chan os.Signal, 1)
	signal.Notify(shutdown, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		slog.Info("Starting ChatAPI server", "addr", cfg.ListenAddr)
		if err := server.Start(); err != nil {
			slog.Error("Server failed to start", "error", err)
			os.Exit(1)
		}
	}()

	// Wait for shutdown signal
	<-shutdown
	slog.Info("Received shutdown signal, initiating graceful shutdown")

	// Stop accepting new connections
	server.Shutdown()

	// Stop workers
	cancel()

	// Wait for ongoing operations to complete
	time.Sleep(cfg.ShutdownDrainTimeout)

	slog.Info("ChatAPI shutdown complete")
}