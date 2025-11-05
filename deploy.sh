#!/bin/bash

# ============================================================================
# AQI Prediction System - Deployment Script
# ============================================================================
# This script handles deployment tasks for the AQI prediction system
# Usage: ./deploy.sh [command]
# Commands: setup, build, start, stop, logs, health, clean
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if command -v docker &> /dev/null; then
        print_success "Docker is installed: $(docker --version)"
    else
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose is installed: $(docker-compose --version)"
    else
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check environment file
    if [ -f .env ]; then
        print_success ".env file exists"
    else
        print_warning ".env file not found"
        print_info "Creating .env from template..."
        cat > .env << EOF
DB_PASSWORD=change_me_in_production
SECRET_KEY=$(openssl rand -hex 32)
OPENWEATHER_API_KEY=your_key_here
IQAIR_API_KEY=your_key_here
CPCB_API_KEY=your_key_here
EOF
        print_success ".env file created - please update with your API keys"
    fi
}

# Setup environment
setup() {
    print_header "Setting Up Environment"
    
    check_prerequisites
    
    # Create necessary directories
    mkdir -p logs data/raw data/processed models/trained_models
    print_success "Created necessary directories"
    
    # Build Docker images
    print_info "Building Docker images..."
    docker-compose build
    print_success "Docker images built successfully"
    
    print_success "Setup complete!"
}

# Build Docker images
build() {
    print_header "Building Docker Images"
    docker-compose build
    print_success "Build complete"
}

# Start services
start() {
    print_header "Starting Services"
    
    # Check if services are already running
    if docker-compose ps | grep -q "Up"; then
        print_warning "Services are already running"
        print_info "Use './deploy.sh stop' to stop them first"
        return
    fi
    
    # Start services
    print_info "Starting all services..."
    docker-compose up -d
    
    # Wait for services to be healthy
    print_info "Waiting for services to be healthy..."
    sleep 10
    
    # Check health
    health
    
    print_success "All services started!"
    print_info "Access the application:"
    print_info "  - Backend API: http://localhost:5000"
    print_info "  - API Docs: http://localhost:5000/api/v1/docs"
    print_info "  - React Dashboard: http://localhost:80"
    print_info "  - PostgreSQL: localhost:5432"
    print_info "  - Redis: localhost:6379"
}

# Stop services
stop() {
    print_header "Stopping Services"
    docker-compose down
    print_success "All services stopped"
}

# Restart services
restart() {
    print_header "Restarting Services"
    stop
    sleep 2
    start
}

# View logs
logs() {
    print_header "Viewing Logs"
    
    if [ -z "$2" ]; then
        # Show all logs
        docker-compose logs -f
    else
        # Show specific service logs
        docker-compose logs -f "$2"
    fi
}

# Health check
health() {
    print_header "Health Check"
    
    # Check PostgreSQL
    if docker-compose exec -T postgres pg_isready -U postgres &> /dev/null; then
        print_success "PostgreSQL: Healthy"
    else
        print_error "PostgreSQL: Unhealthy"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        print_success "Redis: Healthy"
    else
        print_error "Redis: Unhealthy"
    fi
    
    # Check Backend API
    if curl -f http://localhost:5000/api/v1/health &> /dev/null; then
        print_success "Backend API: Healthy"
    else
        print_warning "Backend API: Not responding (may still be starting)"
    fi
    
    # Show container status
    echo ""
    print_info "Container Status:"
    docker-compose ps
}

# Clean up
clean() {
    print_header "Cleaning Up"
    
    print_warning "This will remove all containers, volumes, and images"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" == "yes" ]; then
        print_info "Stopping services..."
        docker-compose down -v
        
        print_info "Removing images..."
        docker rmi $(docker images -q aqi-prediction*) 2>/dev/null || true
        
        print_success "Cleanup complete"
    else
        print_info "Cleanup cancelled"
    fi
}

# Deploy to production
deploy_production() {
    print_header "Deploying to Production"
    
    # Run tests first
    print_info "Running tests..."
    python -m pytest tests/ -v || {
        print_error "Tests failed! Aborting deployment."
        exit 1
    }
    print_success "Tests passed"
    
    # Build optimized image
    print_info "Building production image..."
    docker build -t aqi-prediction:latest .
    print_success "Image built"
    
    # Tag image with timestamp
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    docker tag aqi-prediction:latest aqi-prediction:$TIMESTAMP
    print_success "Image tagged: aqi-prediction:$TIMESTAMP"
    
    # Commit and push to trigger Render deployment
    print_info "Pushing to GitHub..."
    git add .
    git commit -m "deploy: Production deployment $TIMESTAMP" || true
    git push origin main
    print_success "Pushed to GitHub"
    
    print_success "Deployment initiated!"
    print_info "Monitor deployment at: https://dashboard.render.com"
}

# Show usage
usage() {
    echo "Usage: ./deploy.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup       - Initial setup (creates dirs, builds images)"
    echo "  build       - Build Docker images"
    echo "  start       - Start all services"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  logs [svc]  - View logs (optional: specific service)"
    echo "  health      - Check service health"
    echo "  clean       - Clean up containers and images"
    echo "  deploy      - Deploy to production (Render)"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh setup"
    echo "  ./deploy.sh start"
    echo "  ./deploy.sh logs backend"
    echo "  ./deploy.sh health"
}

# Main script
case "$1" in
    setup)
        setup
        ;;
    build)
        build
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs "$@"
        ;;
    health)
        health
        ;;
    clean)
        clean
        ;;
    deploy)
        deploy_production
        ;;
    *)
        usage
        exit 1
        ;;
esac
