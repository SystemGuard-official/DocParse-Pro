#!/bin/bash

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
readonly SCRIPT_NAME="$(basename "$0")"
readonly COMPOSE_DIR="backend/deployment/docker"
readonly BASE_FILE="${COMPOSE_DIR}/docker-compose.base.yml"
readonly CPU_FILE="${COMPOSE_DIR}/docker-compose.cpu.yml"
readonly GPU_FILE="${COMPOSE_DIR}/docker-compose.gpu.yml"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Usage message
usage() {
    cat << EOF
Usage: ${SCRIPT_NAME} <mode> [options]

MODES:
    cpu                     Deploy with CPU configuration
    gpu                     Deploy with GPU configuration

OPTIONS:
    -h, --help             Show this help message

EXAMPLES:
    ${SCRIPT_NAME} cpu
    ${SCRIPT_NAME} gpu

EOF
    exit "${1:-1}"
}

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  INFO:${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅ SUCCESS:${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠️  WARNING:${NC} $1"
}

log_error() {
    echo -e "${RED}❌ ERROR:${NC} $1" >&2
}

# Check if required files exist
check_dependencies() {
    local missing_files=()
    
    for file in "$BASE_FILE" "$CPU_FILE" "$GPU_FILE"; do
        if [[ ! -f "$file" ]]; then
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_error "Missing required files:"
        printf '  - %s\n' "${missing_files[@]}"
        exit 1
    fi
    
    # Check if docker-compose is available (prefer standalone docker-compose)
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
        log_info "Using: docker-compose"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
        log_info "Using: docker compose"
    else
        log_error "Neither 'docker-compose' nor 'docker compose' is available"
        exit 1
    fi
}

# Parse command line arguments
parse_arguments() {
    local mode=""
    
    # Check for minimum arguments
    if [[ $# -lt 1 ]]; then
        log_error "Missing required mode argument"
        usage
    fi
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            cpu|gpu)
                if [[ -n "$mode" ]]; then
                    log_error "Mode already specified: $mode"
                    usage
                fi
                mode="$1"
                shift
                ;;
            -h|--help)
                usage 0
                ;;
            *)
                log_error "Unknown argument: $1"
                usage
                ;;
        esac
    done
    
    # Validate required arguments
    if [[ -z "$mode" ]]; then
        log_error "Mode (cpu|gpu) is required"
        usage
    fi
    
    echo "$mode"
}

# Build docker-compose command
build_compose_command() {
    local mode="$1"
    local compose_files=("-f" "$BASE_FILE")
    
    case "$mode" in
        cpu)
            compose_files+=("-f" "$CPU_FILE")
            ;;
        gpu)
            compose_files+=("-f" "$GPU_FILE")
            ;;
    esac
    
    echo "${compose_files[@]}"
}

# Main deployment function
deploy() {
    local mode="$1"
    
    log_info "Starting deployment with $mode configuration..."
    
    # Log configuration details
    case "$mode" in
        cpu)
            log_info "Configuring CPU deployment"
            ;;
        gpu)
            log_info "Configuring GPU deployment"
            ;;
    esac
    
    # Build compose command
    local compose_files
    read -ra compose_files <<< "$(build_compose_command "$mode")"
    
    # Show what will be deployed
    log_info "Docker Compose files to be used:"
    for file in "${compose_files[@]}"; do
        [[ "$file" != "-f" ]] && echo "  - $file"
    done
    
    # Execute docker-compose
    local cmd_display="$DOCKER_COMPOSE_CMD ${compose_files[*]} up --build -d"
    log_info "Executing: $cmd_display"
    
    # Execute the command without color codes
    if $DOCKER_COMPOSE_CMD "${compose_files[@]}" up --build -d; then
        log_success "Deployment completed successfully! 🚀"
        log_info "Use 'docker ps' to check container status"
    else
        log_error "Deployment failed!"
        exit 1
    fi
}

# Cleanup function
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Script failed with exit code $exit_code"
    fi
    exit $exit_code
}

# Main function
main() {
    # Set up error handling
    trap cleanup EXIT
    
    # Parse arguments
    local parsed_args
    parsed_args=$(parse_arguments "$@")
    read -r mode <<< "$parsed_args"
    
    # Check dependencies
    check_dependencies
    
    # Deploy
    deploy "$mode"
}

# Run main function with all arguments
main "$@"