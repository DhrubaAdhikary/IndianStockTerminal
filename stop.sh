#!/bin/bash

# Indian Stock Terminal - Stop Script

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo -e "${GREEN}Stopping Indian Stock Terminal...${NC}"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load saved config
if [[ -f "$SCRIPT_DIR/.server.config" ]]; then
    source "$SCRIPT_DIR/.server.config"

    # Kill by PID
    if [[ -n "$BACKEND_PID" ]]; then
        kill "$BACKEND_PID" 2>/dev/null && echo "Stopped backend (PID: $BACKEND_PID)" || true
    fi

    if [[ -n "$FRONTEND_PID" ]]; then
        kill "$FRONTEND_PID" 2>/dev/null && echo "Stopped frontend (PID: $FRONTEND_PID)" || true
    fi

    # Also kill by port (backup)
    if [[ -n "$BACKEND_PORT" ]] && command -v lsof &> /dev/null; then
        lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
    fi

    if [[ -n "$FRONTEND_PORT" ]] && command -v lsof &> /dev/null; then
        lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
    fi

    rm "$SCRIPT_DIR/.server.config"
else
    echo -e "${YELLOW}No config found. Trying to stop by process name...${NC}"
fi

# Fallback: kill by process name
pkill -f "uvicorn api_server" 2>/dev/null && echo "Stopped uvicorn processes" || true
pkill -f "vite" 2>/dev/null && echo "Stopped vite processes" || true

# Clean up old pid files if they exist
rm -f "$SCRIPT_DIR/.backend.pid" "$SCRIPT_DIR/.frontend.pid" 2>/dev/null

echo ""
echo -e "${GREEN}All services stopped.${NC}"
echo ""
