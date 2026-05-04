from flask import Flask, request, jsonify
import subprocess
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ── Email Configuration ──────────────────────────────────────
EMAIL_CONFIG = {
    "sender_email": "shellyatri07mail@gmail.com",     
    "sender_password": "nije jqnl ddsg wiji",    
    "receiver_email": "chaudharyyash0809@gmail.com",    
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587
}

# ── Track actions ────────────────────────────────────────────
action_log = []

def send_email_notification(alert_name, pod, namespace, action, success):
    """Send email notification after remediation"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🚨 [{alert_name}] Auto-Remediation {'✅ SUCCESS' if success else '❌ FAILED'}"
        msg["From"]    = EMAIL_CONFIG["sender_email"]
        msg["To"]      = EMAIL_CONFIG["receiver_email"]

        # Email body
        status_color = "#28a745" if success else "#dc3545"
        status_text  = "SUCCESS" if success else "FAILED"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background:#1a1a2e; color:white; padding:20px; border-radius:10px;">
                <h2 style="color:#e94560;">🚨 DevOps Incident Response System</h2>
                <h3>Auto-Remediation Report</h3>
                <hr style="border-color:#444;">
                <table style="width:100%; color:white;">
                    <tr>
                        <td><b>Alert Name:</b></td>
                        <td style="color:#f0a500;">{alert_name}</td>
                    </tr>
                    <tr>
                        <td><b>Pod:</b></td>
                        <td>{pod}</td>
                    </tr>
                    <tr>
                        <td><b>Namespace:</b></td>
                        <td>{namespace}</td>
                    </tr>
                    <tr>
                        <td><b>Action Taken:</b></td>
                        <td>{action}</td>
                    </tr>
                    <tr>
                        <td><b>Status:</b></td>
                        <td style="color:{status_color};"><b>{status_text}</b></td>
                    </tr>
                    <tr>
                        <td><b>Timestamp:</b></td>
                        <td>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                </table>
                <hr style="border-color:#444;">
                <p style="color:#aaa; font-size:12px;">
                    This is an automated message from your 
                    DevOps Incident Response System 🤖
                </p>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(html, "html"))

        # Send email
        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.sendmail(
                EMAIL_CONFIG["sender_email"],
                EMAIL_CONFIG["receiver_email"],
                msg.as_string()
            )

        logger.info(f"📧 Email notification sent for {alert_name}")
        return True

    except Exception as e:
        logger.error(f"❌ Email failed: {str(e)}")
        return False

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
    success, msg = run_kubectl(
        ['delete', 'pod', pod, '-n', namespace, '--grace-period=30']
    )
    entry = log_action('pod_restart', 'delete_pod', f"{namespace}/{pod}", success, msg)
    # Send email after action
    send_email_notification('PodCrashLooping', pod, namespace, 'Pod Deleted & Restarted', success)
    return entry

def scale_deployment(deployment, namespace, replicas=2):
    success, msg = run_kubectl(
        ['scale', 'deployment', deployment, f'--replicas={replicas}', '-n', namespace]
    )
    entry = log_action('scale_up', 'scale_deployment', f"{namespace}/{deployment}", success, msg)
    send_email_notification('HighCPUUsage', deployment, namespace, f'Scaled to {replicas} replicas', success)
    return entry

def get_pod_for_namespace(namespace):
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
    alerts  = data.get('alerts', [])
    results = []

    for alert in alerts:
        labels     = alert.get('labels', {})
        alert_name = labels.get('alertname', 'Unknown')
        namespace  = labels.get('namespace', 'default')
        pod        = labels.get('pod', '')
        status     = alert.get('status', '')
        incident   = labels.get('incident_type', '')

        logger.info(f"📢 {alert_name} | status={status} | ns={namespace} | pod={pod}")

        if status != 'firing':
            results.append({"alert": alert_name, "action": "skipped", "reason": "resolved"})
            continue

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
            deployment = labels.get('deployment', '')
            if deployment:
                result = scale_deployment(deployment, namespace, replicas=2)
                results.append(result)
            else:
                results.append({"alert": alert_name, "action": "logged"})

        elif incident == 'high_memory':
            if pod:
                result = restart_pod(pod, namespace)
                results.append(result)

        else:
            logger.info(f"ℹ️ No rule for: {alert_name}")
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
    return jsonify({
        "total_actions": len(action_log),
        "actions": action_log[-20:]
    }), 200


@app.route('/test-email', methods=['GET'])
def test_email():
    """Test email endpoint"""
    success = send_email_notification(
        alert_name="TestAlert",
        pod="test-pod-123",
        namespace="default",
        action="Test Notification",
        success=True
    )
    if success:
        return jsonify({"status": "Email sent successfully! ✅"}), 200
    else:
        return jsonify({"status": "Email failed ❌ - check credentials"}), 500


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "DevOps Incident Response System",
        "version": "2.0",
        "endpoints": {
            "POST /alert": "Receive alerts from Alertmanager",
            "GET /health": "Health check",
            "GET /logs": "View remediation history",
            "GET /test-email": "Test email notification"
        }
    }), 200


if __name__ == '__main__':
    logger.info("🚀 Remediation Engine v2.0 starting on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)