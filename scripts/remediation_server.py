from flask import Flask, request, jsonify
import subprocess
import logging
from datetime import datetime

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ── Track actions taken ──────────────────────────────────────
action_log = []

def log_action(alert_name, action, target, success, message=""):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "alert": alert_name,
        "action": action,
        "target": target,
        "success": success,
        "message": message
    }
    action_log.append(entry)
    logger.info(f"{'✅' if success else '❌'} [{alert_name}] {action} → {target}")
    return entry

def run_kubectl(args, timeout=30):
    """Run a kubectl command safely"""
    try:
        result = subprocess.run(
            ['kubectl'] + args,
            capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout or result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def restart_pod(pod, namespace):
    success, msg = run_kubectl(['delete', 'pod', pod, '-n', namespace, '--grace-period=30'])
    return log_action('pod_restart', 'delete_pod', f"{namespace}/{pod}", success, msg)

def scale_deployment(deployment, namespace, replicas=2):
    success, msg = run_kubectl(['scale', 'deployment', deployment,
                                f'--replicas={replicas}', '-n', namespace])
    return log_action('scale_up', 'scale_deployment', f"{namespace}/{deployment}", success, msg)

def get_pod_for_namespace(namespace):
    """Find a crashlooping pod in a namespace"""
    success, output = run_kubectl([
        'get', 'pods', '-n', namespace,
        '--field-selector=status.phase!=Running',
        '-o', 'jsonpath={.items[0].metadata.name}'
    ])
    return output.strip() if success else None

# ── Main Alert Handler ───────────────────────────────────────
@app.route('/alert', methods=['POST'])
def handle_alert():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    logger.info("🔔 Alert received from Alertmanager")
    alerts = data.get('alerts', [])
    results = []

    for alert in alerts:
        labels      = alert.get('labels', {})
        alert_name  = labels.get('alertname', 'Unknown')
        namespace   = labels.get('namespace', 'default')
        pod         = labels.get('pod', '')
        status      = alert.get('status', '')
        incident    = labels.get('incident_type', '')

        logger.info(f"📢 {alert_name} | status={status} | ns={namespace} | pod={pod}")

        if status != 'firing':
            results.append({"alert": alert_name, "action": "skipped", "reason": "resolved"})
            continue

        # ── Remediation Decision Tree ────────────────────────
        if incident == 'pod_crash' and pod:
            result = restart_pod(pod, namespace)
            results.append(result)

        elif incident == 'pod_not_ready':
            if pod:
                result = restart_pod(pod, namespace)
            else:
                found_pod = get_pod_for_namespace(namespace)
                if found_pod:
                    result = restart_pod(found_pod, namespace)
                else:
                    result = log_action(alert_name, 'no_action', namespace, False, 'Pod not found')
            results.append(result)

        elif incident == 'high_cpu':
            # Scale up to handle load
            deployment = labels.get('deployment', '')
            if deployment:
                result = scale_deployment(deployment, namespace, replicas=2)
                results.append(result)
            else:
                results.append({"alert": alert_name, "action": "logged", "note": "No deployment label"})

        elif incident == 'high_memory':
            if pod:
                result = restart_pod(pod, namespace)
                results.append(result)

        else:
            logger.info(f"ℹ️ No remediation rule for: {alert_name}")
            results.append({"alert": alert_name, "action": "none"})

    return jsonify({
        "status": "processed",
        "timestamp": datetime.now().isoformat(),
        "alerts_received": len(alerts),
        "results": results
    }), 200


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "remediation-engine"}), 200


@app.route('/logs', methods=['GET'])
def get_logs():
    """See all remediation actions taken"""
    return jsonify({
        "total_actions": len(action_log),
        "actions": action_log[-20:]  # last 20
    }), 200


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "DevOps Incident Response System",
        "version": "1.0",
        "endpoints": {
            "POST /alert": "Receive alerts from Alertmanager",
            "GET /health": "Health check",
            "GET /logs": "View remediation history"
        }
    }), 200


if __name__ == '__main__':
    logger.info("🚀 Remediation Engine starting on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)