#!/bin/bash

# Jatayu AI Quiz Backend - Service Management Script
# This script manages the FastAPI app, Celery worker, and scheduler components

set -e  # Exit on any error

# Configuration
PROJECT_NAME="Jatayu AI Quiz Backend"
LOG_DIR="logs"
FASTAPI_HOST="0.0.0.0"
FASTAPI_PORT="8000"
UVICORN_WORKERS="1"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to print banner
print_banner() {
    echo ""
    echo "=================================="
    echo "  $PROJECT_NAME"
    echo "=================================="
    echo ""
}

# Function to check if a process is running on a port
check_port() {
    local port=$1
    if netstat -tuln 2>/dev/null | grep -q ":$port "; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to check if Python virtual environment is activated
check_virtual_env() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo "WARNING: No virtual environment detected"
        echo "Consider activating your virtual environment first"
        echo ""
    else
        echo "Virtual environment active: $(basename $VIRTUAL_ENV)"
    fi
}

# Function to validate database connection
validate_database() {
    echo "Validating database connection..."
    if python validate_database.py > "$LOG_DIR/db_validation.log" 2>&1; then
        echo "Database validation passed"
    else
        echo "ERROR: Database validation failed"
        echo "Check $LOG_DIR/db_validation.log for details"
        return 1
    fi
}

# Function to start FastAPI application
start_fastapi() {
    echo "Starting FastAPI application..."
    
    if check_port $FASTAPI_PORT; then
        echo "WARNING: Port $FASTAPI_PORT is already in use"
        echo "Trying to start anyway (uvicorn will find another port)"
    fi
    
    local log_file="$LOG_DIR/fastapi.log"
    echo "FastAPI logs: $log_file"
    
    # Start FastAPI with uvicorn
    uvicorn main:app \
        --host $FASTAPI_HOST \
        --port $FASTAPI_PORT \
        --workers $UVICORN_WORKERS \
        --log-level info \
        --access-log \
        --reload \
        > "$log_file" 2>&1 &
    
    local fastapi_pid=$!
    echo $fastapi_pid > "$LOG_DIR/fastapi.pid"
    
    echo "FastAPI started (PID: $fastapi_pid)"
    echo "URL: http://$FASTAPI_HOST:$FASTAPI_PORT"
    echo "Docs: http://$FASTAPI_HOST:$FASTAPI_PORT/docs"
    
    return $fastapi_pid
}

# Function to start Celery worker
start_celery() {
    echo "Starting Celery worker..."
    
    local log_file="$LOG_DIR/celery.log"
    echo "Celery logs: $log_file"
    
    # Start Celery worker
    celery -A celery_app worker \
        --loglevel=info \
        -P solo \
        --logfile="$log_file" \
        --pidfile="$LOG_DIR/celery.pid" \
        --detach
    
    if [[ $? -eq 0 ]]; then
        local celery_pid=$(cat "$LOG_DIR/celery.pid" 2>/dev/null || echo "unknown")
        echo "Celery worker started (PID: $celery_pid)"
    else
        echo "ERROR: Failed to start Celery worker"
        return 1
    fi
}

# Function to start scheduler
start_scheduler() {
    echo "Starting scheduler..."
    
    local log_file="$LOG_DIR/scheduler.log"
    echo "Scheduler logs: $log_file"
    
    # Start scheduler
    python scheduler.py > "$log_file" 2>&1 &
    
    local scheduler_pid=$!
    echo $scheduler_pid > "$LOG_DIR/scheduler.pid"
    
    echo "Scheduler started (PID: $scheduler_pid)"
    
    return $scheduler_pid
}

# Function to stop all services
stop_services() {
    echo "Stopping all services..."
    
    # Stop FastAPI
    if [[ -f "$LOG_DIR/fastapi.pid" ]]; then
        local fastapi_pid=$(cat "$LOG_DIR/fastapi.pid")
        if kill -0 "$fastapi_pid" 2>/dev/null; then
            kill "$fastapi_pid"
            echo "FastAPI stopped (PID: $fastapi_pid)"
        fi
        rm -f "$LOG_DIR/fastapi.pid"
    fi
    
    # Stop Celery
    if [[ -f "$LOG_DIR/celery.pid" ]]; then
        local celery_pid=$(cat "$LOG_DIR/celery.pid")
        if kill -0 "$celery_pid" 2>/dev/null; then
            kill "$celery_pid"
            echo "Celery stopped (PID: $celery_pid)"
        fi
        rm -f "$LOG_DIR/celery.pid"
    fi
    
    # Stop Scheduler
    if [[ -f "$LOG_DIR/scheduler.pid" ]]; then
        local scheduler_pid=$(cat "$LOG_DIR/scheduler.pid")
        if kill -0 "$scheduler_pid" 2>/dev/null; then
            kill "$scheduler_pid"
            echo "Scheduler stopped (PID: $scheduler_pid)"
        fi
        rm -f "$LOG_DIR/scheduler.pid"
    fi
    
    # Also try to kill by process name as backup
    pkill -f "uvicorn main:app" 2>/dev/null || true
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "python.*scheduler.py" 2>/dev/null || true
}

# Function to check service status
check_status() {
    echo "Service Status:"
    echo ""
    
    # Check FastAPI
    if [[ -f "$LOG_DIR/fastapi.pid" ]]; then
        local fastapi_pid=$(cat "$LOG_DIR/fastapi.pid")
        if kill -0 "$fastapi_pid" 2>/dev/null; then
            echo "FastAPI: Running (PID: $fastapi_pid)"
        else
            echo "FastAPI: Not running (stale PID file)"
        fi
    else
        echo "FastAPI: Not running"
    fi
    
    # Check Celery
    if [[ -f "$LOG_DIR/celery.pid" ]]; then
        local celery_pid=$(cat "$LOG_DIR/celery.pid")
        if kill -0 "$celery_pid" 2>/dev/null; then
            echo "Celery: Running (PID: $celery_pid)"
        else
            echo "Celery: Not running (stale PID file)"
        fi
    else
        echo "Celery: Not running"
    fi
    
    # Check Scheduler
    if [[ -f "$LOG_DIR/scheduler.pid" ]]; then
        local scheduler_pid=$(cat "$LOG_DIR/scheduler.pid")
        if kill -0 "$scheduler_pid" 2>/dev/null; then
            echo "Scheduler: Running (PID: $scheduler_pid)"
        else
            echo "Scheduler: Not running (stale PID file)"
        fi
    else
        echo "Scheduler: Not running"
    fi
    
    echo ""
    echo "Log files location: $LOG_DIR/"
}

# Function to show logs
show_logs() {
    local service=$1
    local log_file="$LOG_DIR/${service}.log"
    
    if [[ -f "$log_file" ]]; then
        echo "Showing $service logs (last 50 lines):"
        echo ""
        tail -n 50 "$log_file"
        echo ""
        echo "To follow logs in real-time: tail -f $log_file"
    else
        echo "ERROR: Log file not found: $log_file"
    fi
}

# Function to restart all services
restart_services() {
    echo "Restarting all services..."
    stop_services
    sleep 2
    start_all_services
}

# Function to start all services
start_all_services() {
    print_banner
    check_virtual_env
    
    # Validate database first
    if ! validate_database; then
        echo "ERROR: Database validation failed. Please fix database issues first."
        exit 1
    fi
    
    # Start services
    start_celery
    sleep 2
    start_scheduler
    sleep 2
    start_fastapi
    
    echo ""
    echo "All services started successfully!"
    echo ""
    check_status
    
    echo ""
    echo "Useful commands:"
    echo "  - Check status: $0 status"
    echo "  - View logs: $0 logs [fastapi|celery|scheduler]"
    echo "  - Stop services: $0 stop"
    echo "  - Restart services: $0 restart"
}

# Function to show help
show_help() {
    print_banner
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       Start all services (FastAPI, Celery, Scheduler)"
    echo "  stop        Stop all services"
    echo "  restart     Restart all services"
    echo "  status      Show status of all services"
    echo "  logs        Show logs for all services"
    echo "  logs <svc>  Show logs for specific service (fastapi|celery|scheduler)"
    echo "  fastapi     Start only FastAPI"
    echo "  celery      Start only Celery worker"
    echo "  scheduler   Start only Scheduler"
    echo "  validate    Validate database connection"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start              # Start all services"
    echo "  $0 logs fastapi       # Show FastAPI logs"
    echo "  $0 status             # Check service status"
    echo ""
}

# Main script logic
case "${1:-start}" in
    "start")
        start_all_services
        ;;
    "stop")
        print_banner
        stop_services
        ;;
    "restart")
        print_banner
        restart_services
        ;;
    "status")
        print_banner
        check_status
        ;;
    "logs")
        if [[ -n "$2" ]]; then
            show_logs "$2"
        else
            echo "All service logs:"
            echo ""
            for service in fastapi celery scheduler; do
                echo "=== $service logs ==="
                show_logs "$service"
                echo ""
            done
        fi
        ;;
    "fastapi")
        print_banner
        check_virtual_env
        start_fastapi
        ;;
    "celery")
        print_banner
        check_virtual_env
        start_celery
        ;;
    "scheduler")
        print_banner
        check_virtual_env
        start_scheduler
        ;;
    "validate")
        print_banner
        validate_database
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "ERROR: Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
