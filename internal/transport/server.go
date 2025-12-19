package transport

import (
	"context"
	"log/slog"
	"net/http"
	"time"

	"github.com/hastenr/chatapi/internal/config"
	"github.com/hastenr/chatapi/internal/db"
	"github.com/hastenr/chatapi/internal/handlers/rest"
	"github.com/hastenr/chatapi/internal/handlers/ws"
	"github.com/hastenr/chatapi/internal/services/chatroom"
	"github.com/hastenr/chatapi/internal/services/delivery"
	"github.com/hastenr/chatapi/internal/services/message"
	"github.com/hastenr/chatapi/internal/services/notification"
	"github.com/hastenr/chatapi/internal/services/realtime"
	"github.com/hastenr/chatapi/internal/services/tenant"
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
	db *db.DB,
	tenantSvc *tenant.Service,
	realtimeSvc *realtime.Service,
	deliverySvc *delivery.Service,
) *Server {
	// Create handlers
	chatroomSvc := chatroom.NewService(db.DB)
	messageSvc := message.NewService(db.DB)
	notifSvc := notification.NewService(db.DB)

	restHandler := rest.NewHandler(tenantSvc, chatroomSvc, messageSvc, realtimeSvc, deliverySvc, notifSvc, cfg)
	wsHandler := ws.NewHandler(tenantSvc, chatroomSvc, messageSvc, realtimeSvc)

	// Create mux and register routes
	mux := http.NewServeMux()

	// Apply auth middleware to protected routes
	protectedMux := http.NewServeMux()
	protectedMux.HandleFunc("POST /rooms", restHandler.AuthMiddleware(restHandler.HandleCreateRoom))
	protectedMux.HandleFunc("GET /rooms/{room_id}", restHandler.AuthMiddleware(restHandler.HandleGetRoom))
	protectedMux.HandleFunc("GET /rooms/{room_id}/members", restHandler.AuthMiddleware(restHandler.HandleGetRoomMembers))
	protectedMux.HandleFunc("POST /rooms/{room_id}/messages", restHandler.AuthMiddleware(restHandler.HandleSendMessage))
	protectedMux.HandleFunc("GET /rooms/{room_id}/messages", restHandler.AuthMiddleware(restHandler.HandleGetMessages))
	protectedMux.HandleFunc("POST /acks", restHandler.AuthMiddleware(restHandler.HandleAck))
	protectedMux.HandleFunc("POST /notify", restHandler.AuthMiddleware(restHandler.HandleNotify))
	protectedMux.HandleFunc("GET /admin/dead-letters", restHandler.AuthMiddleware(restHandler.HandleGetDeadLetters))

	// Register public routes
	mux.HandleFunc("GET /health", restHandler.HandleHealth)
	mux.HandleFunc("GET /ws", wsHandler.HandleConnection)

	// Mount protected routes with auth middleware
	mux.Handle("/", restHandler.AuthMiddleware(func(w http.ResponseWriter, r *http.Request) {
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
