#!/bin/bash
# remediation-scripts.sh
# Auto-remediation actions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log_action() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

# ============ REMEDIATION FUNCTIONS ============

# Function: Restart a pod
restart_pod() {
    local pod_name=$1
    local namespace=${2:-default}
    
    log_action "Restarting pod: $pod_name in namespace: $namespace"
    
    if kubectl delete pod "$pod_name" -n "$namespace" --grace-period=30 2>/dev/null; then
        log_success "Pod $pod_name restarted successfully"
        return 0
    else
        log_error "Failed to restart pod $pod_name"
        return 1
    fi
}

# Function: Scale deployment up
scale_deployment_up() {
    local deployment=$1
    local namespace=${2:-default}
    
    log_action "Scaling up deployment: $deployment"
    
    # Get current replicas
    local current=$(kubectl get deployment "$deployment" -n "$namespace" -o jsonpath='{.spec.replicas}' 2>/dev/null)
    
    if [ -z "$current" ]; then
        log_error "Deployment $deployment not found"
        return 1
    fi
    
    local new=$((current + 1))
    
    if kubectl scale deployment "$deployment" --replicas="$new" -n "$namespace" 2>/dev/null; then
        log_success "Scaled $deployment: $current → $new replicas"
        return 0
    else
        log_error "Failed to scale deployment"
        return 1
    fi
}

# Function: Force delete pod
force_delete_pod() {
    local pod_name=$1
    local namespace=${2:-default}
    
    log_action "Force deleting pod: $pod_name"
    
    if kubectl delete pod "$pod_name" -n "$namespace" --grace-period=0 --force 2>/dev/null; then
        log_success "Pod $pod_name force-deleted"
        return 0
    else
        log_error "Failed to force-delete pod"
        return 1
    fi
}

# Function: Get pod logs
get_pod_logs() {
    local pod_name=$1
    local namespace=${2:-default}
    
    log_action "Getting logs for pod: $pod_name"
    kubectl logs "$pod_name" -n "$namespace" --tail=20
}

# ============ MAIN HANDLER ============

case "$1" in
    restart-pod)
        restart_pod "$2" "$3"
        ;;
    scale-up)
        scale_deployment_up "$2" "$3"
        ;;
    force-delete)
        force_delete_pod "$2" "$3"
        ;;
    get-logs)
        get_pod_logs "$2" "$3"
        ;;
    *)
        echo "Usage: $0 {restart-pod|scale-up|force-delete|get-logs} <pod/deployment> [namespace]"
        exit 1
        ;;
esac