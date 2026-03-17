#!/bin/bash

# Indian Stock Terminal - Setup & Run Script
# Works on macOS, Linux, and Windows (Git Bash/WSL)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default ports
DEFAULT_BACKEND_PORT=8001
DEFAULT_FRONTEND_PORT=5173

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}   Indian Stock Terminal - Setup & Run${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}[*]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if port is available
is_port_available() {
    local port=$1
    if command -v lsof &> /dev/null; then
        ! lsof -i :$port &> /dev/null
    elif command -v netstat &> /dev/null; then
        ! netstat -an | grep -q ":$port.*LISTEN"
    else
        # Assume available if we can't check
        return 0
    fi
}

# Find an available port starting from a given port
find_available_port() {
    local start_port=$1
    local port=$start_port
    local max_port=$((start_port + 100))

    while [ $port -lt $max_port ]; do
        if is_port_available $port; then
            echo $port
            return 0
        fi
        port=$((port + 1))
    done

    echo $start_port
    return 1
}

# Get port configuration
configure_ports() {
    echo ""
    echo -e "${CYAN}Port Configuration${NC}"
    echo -e "${CYAN}------------------${NC}"
    echo ""
    echo "Default ports: Backend=$DEFAULT_BACKEND_PORT, Frontend=$DEFAULT_FRONTEND_PORT"
    echo ""
    echo "Options:"
    echo "  1) Use default ports (auto-find if busy)"
    echo "  2) Enter custom ports"
    echo ""
    read -p "Choose option [1]: " PORT_OPTION
    PORT_OPTION=${PORT_OPTION:-1}

    if [ "$PORT_OPTION" = "2" ]; then
        # Custom ports
        read -p "Backend API port [$DEFAULT_BACKEND_PORT]: " BACKEND_PORT
        BACKEND_PORT=${BACKEND_PORT:-$DEFAULT_BACKEND_PORT}

        read -p "Frontend port [$DEFAULT_FRONTEND_PORT]: " FRONTEND_PORT
        FRONTEND_PORT=${FRONTEND_PORT:-$DEFAULT_FRONTEND_PORT}
    else
        # Auto-detect available ports
        if is_port_available $DEFAULT_BACKEND_PORT; then
            BACKEND_PORT=$DEFAULT_BACKEND_PORT
        else
            print_warning "Port $DEFAULT_BACKEND_PORT is busy, finding available port..."
            BACKEND_PORT=$(find_available_port $DEFAULT_BACKEND_PORT)
        fi

        if is_port_available $DEFAULT_FRONTEND_PORT; then
            FRONTEND_PORT=$DEFAULT_FRONTEND_PORT
        else
            print_warning "Port $DEFAULT_FRONTEND_PORT is busy, finding available port..."
            FRONTEND_PORT=$(find_available_port $DEFAULT_FRONTEND_PORT)
        fi
    fi

    print_step "Using ports: Backend=$BACKEND_PORT, Frontend=$FRONTEND_PORT"

    # Export for use in other functions
    export BACKEND_PORT
    export FRONTEND_PORT
}

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Darwin*)    OS="macos";;
        Linux*)     OS="linux";;
        CYGWIN*|MINGW*|MSYS*) OS="windows";;
        *)          OS="unknown";;
    esac
    print_step "Detected OS: $OS"
}

# Check if conda is installed
check_conda() {
    if command -v conda &> /dev/null; then
        print_step "Conda found: $(conda --version)"
        return 0
    else
        return 1
    fi
}

# Install Miniconda if not present
install_conda() {
    print_step "Conda not found. Installing Miniconda..."

    CONDA_DIR="$HOME/miniconda3"

    case $OS in
        macos)
            if [[ $(uname -m) == "arm64" ]]; then
                CONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
            else
                CONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
            fi
            ;;
        linux)
            CONDA_URL="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
            ;;
        windows)
            print_error "Please install Miniconda manually from: https://docs.conda.io/en/latest/miniconda.html"
            exit 1
            ;;
    esac

    curl -fsSL "$CONDA_URL" -o /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p "$CONDA_DIR"
    rm /tmp/miniconda.sh

    # Initialize conda
    export PATH="$CONDA_DIR/bin:$PATH"
    conda init bash 2>/dev/null || true

    print_step "Miniconda installed at $CONDA_DIR"
}

# Setup conda environment
setup_conda_env() {
    ENV_NAME="stock-terminal"

    # Source conda
    if [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
        source "$HOME/miniconda3/etc/profile.d/conda.sh"
    elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
        source "$HOME/anaconda3/etc/profile.d/conda.sh"
    elif [[ -f "/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh" ]]; then
        source "/opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh"
    fi

    # Check if environment exists
    if conda env list | grep -q "^${ENV_NAME} "; then
        print_step "Conda environment '$ENV_NAME' already exists"
    else
        print_step "Creating conda environment '$ENV_NAME' with Python 3.11..."
        conda create -n "$ENV_NAME" python=3.11 -y
    fi

    print_step "Activating conda environment..."
    conda activate "$ENV_NAME"

    print_step "Installing Python dependencies..."
    pip install -r requirements.txt --quiet
}

# Check and install Node.js
check_node() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_step "Node.js found: $NODE_VERSION"
        return 0
    else
        return 1
    fi
}

install_node() {
    print_step "Node.js not found. Installing..."

    case $OS in
        macos)
            if command -v brew &> /dev/null; then
                brew install node
            else
                print_error "Please install Node.js from: https://nodejs.org/"
                exit 1
            fi
            ;;
        linux)
            if command -v apt-get &> /dev/null; then
                curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
                sudo apt-get install -y nodejs
            elif command -v yum &> /dev/null; then
                curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
                sudo yum install -y nodejs
            else
                print_error "Please install Node.js from: https://nodejs.org/"
                exit 1
            fi
            ;;
        windows)
            print_error "Please install Node.js from: https://nodejs.org/"
            exit 1
            ;;
    esac
}

# Update frontend config with correct backend port
update_frontend_config() {
    print_step "Updating frontend configuration for port $BACKEND_PORT..."

    CONFIG_FILE="$SCRIPT_DIR/bloomberg-terminal/src/config.js"

    cat > "$CONFIG_FILE" << EOF
// API Configuration - Auto-generated by start.sh
// Backend port: $BACKEND_PORT
export const API_BASE = import.meta.env.PROD ? '/api' : 'http://localhost:$BACKEND_PORT/api'
EOF
}

# Setup frontend
setup_frontend() {
    print_step "Setting up frontend..."
    cd "$SCRIPT_DIR/bloomberg-terminal"

    if [[ ! -d "node_modules" ]]; then
        print_step "Installing npm dependencies..."
        npm install --silent
    else
        print_step "npm dependencies already installed"
    fi

    cd "$SCRIPT_DIR"
}

# Start services
start_services() {
    print_step "Starting services..."

    # Kill any existing processes on our ports
    if command -v lsof &> /dev/null; then
        lsof -ti:$BACKEND_PORT | xargs kill -9 2>/dev/null || true
        lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
    fi
    sleep 1

    # Start backend
    print_step "Starting backend API server on port $BACKEND_PORT..."
    cd "$SCRIPT_DIR"
    nohup uvicorn api_server:app --host 0.0.0.0 --port $BACKEND_PORT > api.log 2>&1 &
    BACKEND_PID=$!

    # Start frontend with custom port
    print_step "Starting frontend on port $FRONTEND_PORT..."
    cd "$SCRIPT_DIR/bloomberg-terminal"
    nohup npm run dev -- --port $FRONTEND_PORT > frontend.log 2>&1 &
    FRONTEND_PID=$!

    cd "$SCRIPT_DIR"

    # Wait for services to start
    print_step "Waiting for services to start..."
    sleep 5

    # Verify services
    if curl -s http://localhost:$BACKEND_PORT/docs > /dev/null 2>&1; then
        print_step "Backend API is running on port $BACKEND_PORT"
    else
        print_warning "Backend may still be starting..."
    fi

    if curl -s http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        print_step "Frontend is running on port $FRONTEND_PORT"
    else
        print_warning "Frontend may still be starting..."
    fi

    # Save config for stop script
    cat > "$SCRIPT_DIR/.server.config" << EOF
BACKEND_PID=$BACKEND_PID
FRONTEND_PID=$FRONTEND_PID
BACKEND_PORT=$BACKEND_PORT
FRONTEND_PORT=$FRONTEND_PORT
EOF
}

# Open browser
open_browser() {
    URL="http://localhost:$FRONTEND_PORT"

    print_step "Opening browser..."

    case $OS in
        macos)
            open "$URL" 2>/dev/null || true
            ;;
        linux)
            xdg-open "$URL" 2>/dev/null || true
            ;;
        windows)
            start "$URL" 2>/dev/null || true
            ;;
    esac
}

# Main execution
main() {
    print_header

    detect_os

    configure_ports

    # Setup conda
    if ! check_conda; then
        install_conda
    fi

    setup_conda_env

    # Setup Node.js
    if ! check_node; then
        install_node
    fi

    # Update frontend config with backend port
    update_frontend_config

    setup_frontend

    start_services

    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}   Setup Complete!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo -e "   Frontend: ${BLUE}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "   Backend:  ${BLUE}http://localhost:$BACKEND_PORT${NC}"
    echo -e "   API Docs: ${BLUE}http://localhost:$BACKEND_PORT/docs${NC}"
    echo ""
    echo -e "   To stop: ${YELLOW}./stop.sh${NC}"
    echo ""

    open_browser
}

# Run
main
