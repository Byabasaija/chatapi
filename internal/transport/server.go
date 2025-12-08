package transport

import (
	"context"
	"log/slog"
	"net/http"
	"time"

	"github.com/yourusername/chatapi/internal/config"
	"github.com/yourusername/chatapi/internal/handlers/rest"
	"github.com/yourusername/chatapi/internal/handlers/ws"
	"github.com/yourusername/chatapi/internal/services/chatroom"
	"github.com/yourusername/chatapi/internal/services/delivery"
	"github.com/yourusername/chatapi/internal/services/message"
	"github.com/yourusername/chatapi/internal/services/notification"
	"github.com/yourusername/chatapi/internal/services/realtime"
	"github.com/yourusername/chatapi/internal/services/tenant"
)

// Server represents the HTTP server
type Server struct {
	httpServer  *http.Server
	config      *config.Config
	realtimeSvc *realtime.Service
}

// NewServer creates a new HTTP server
func NewServer(
	cfg *config.Config,
	tenantSvc *tenant.Service,
	realtimeSvc *realtime.Service,
	deliverySvc *delivery.Service,
) *Server {
	// Create handlers
	chatroomSvc := chatroom.NewService(nil) // TODO: inject DB
	messageSvc := message.NewService(nil)   // TODO: inject DB
	notifSvc := notification.NewService(nil) // TODO: inject DB

	restHandler := rest.NewHandler(tenantSvc, chatroomSvc, messageSvc, realtimeSvc, deliverySvc, notifSvc)
	wsHandler := ws.NewHandler(tenantSvc, chatroomSvc, messageSvc, realtimeSvc)

	// Create mux and register routes
	mux := http.NewServeMux()

	// Apply auth middleware to protected routes
	protectedMux := http.NewServeMux()
	protectedMux.HandleFunc("POST /rooms", restHandler.authMiddleware(restHandler.handleCreateRoom))
	protectedMux.HandleFunc("GET /rooms/{room_id}", restHandler.authMiddleware(restHandler.handleGetRoom))
	protectedMux.HandleFunc("GET /rooms/{room_id}/members", restHandler.authMiddleware(restHandler.handleGetRoomMembers))
	protectedMux.HandleFunc("POST /rooms/{room_id}/messages", restHandler.authMiddleware(restHandler.handleSendMessage))
	protectedMux.HandleFunc("GET /rooms/{room_id}/messages", restHandler.authMiddleware(restHandler.handleGetMessages))
	protectedMux.HandleFunc("POST /acks", restHandler.authMiddleware(restHandler.handleAck))
	protectedMux.HandleFunc("POST /notify", restHandler.authMiddleware(restHandler.handleNotify))

	// Register public routes
	mux.HandleFunc("GET /health", restHandler.handleHealth)
	mux.HandleFunc("GET /ws", wsHandler.HandleConnection)

	// Mount protected routes with auth middleware
	mux.Handle("/", restHandler.authMiddleware(func(w http.ResponseWriter, r *http.Request) {
		protectedMux.ServeHTTP(w, r)
	}))

	// Create HTTP server
	httpServer := &http.Server{
		Addr:         cfg.ListenAddr,
		Handler:      mux,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	return &Server{
		httpServer:  httpServer,
		config:      cfg,
		realtimeSvc: realtimeSvc,
	}
}

// Start starts the HTTP server
func (s *Server) Start() error {
	slog.Info("Starting HTTP server", "addr", s.config.ListenAddr)
	return s.httpServer.ListenAndServe()
}

// Shutdown gracefully shuts down the server
func (s *Server) Shutdown() {
	slog.Info("Shutting down HTTP server")

	// Create shutdown context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), s.config.ShutdownDrainTimeout)
	defer cancel()

	// Shutdown HTTP server
	if err := s.httpServer.Shutdown(ctx); err != nil {
		slog.Error("HTTP server shutdown error", "error", err)
	}

	// Shutdown realtime service
	if err := s.realtimeSvc.Shutdown(ctx); err != nil {
		slog.Error("Realtime service shutdown error", "error", err)
	}

	slog.Info("HTTP server shutdown complete")
}