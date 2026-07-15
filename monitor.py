import paramiko
import boto3
import csv
from datetime import datetime
from config import KEY_PATH, SSH_USER, INSTANCES

LOG_FILE = "ticket_log.csv"
SNS_TOPIC_ARN = "arn:aws:sns:ap-southeast-1:401624246750:homelab-alerts"

sns = boto3.client("sns", region_name="ap-southeast-1")

def connect(ip):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=ip, username=SSH_USER, key_filename=KEY_PATH, timeout=10)
    return client

def run_command(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    output = stdout.read().decode().strip()
    error = stderr.read().decode().strip()
    return output, error

def log_ticket(instance_name, issue, action, result):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, instance_name, issue, action, result])
    print(f"  [LOGGED] {issue} -> {action} -> {result}")

def send_alert(instance_name, issue):
    message = f"ALERT: {instance_name} has an unresolved issue.\n\nIssue: {issue}\n\nManual intervention needed."
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Homelab Alert: {instance_name}",
            Message=message
        )
    except Exception as e:
        print(f"  [ALERT FAILED] Could not send SNS alert: {e}")

def check_instance(instance):
    print(f"\nChecking {instance['name']} ({instance['ip']})...")
    try:
        client = connect(instance['ip'])

        disk_out, _ = run_command(client, "df -h / | tail -1 | awk '{print $5}'")
        print(f"  Disk usage: {disk_out}")

        mem_out, _ = run_command(client, "free -m | grep Mem | awk '{print $3\"/\"$2\" MB\"}'")
        print(f"  Memory: {mem_out}")

        if instance['check_service']:
            service = instance['check_service']
            status_out, _ = run_command(client, f"systemctl is-active {service}")
            print(f"  Service '{service}': {status_out}")

            if status_out != "active":
                print(f"  ISSUE DETECTED: {service} is not active. Attempting restart...")
                run_command(client, f"sudo systemctl restart {service}")

                recheck, _ = run_command(client, f"systemctl is-active {service}")
                if recheck == "active":
                    log_ticket(instance['name'], f"{service} was {status_out}", f"restarted {service}", "SUCCESS - now active")
                else:
                    log_ticket(instance['name'], f"{service} was {status_out}", f"attempted restart {service}", "FAILED - still not active")
                    send_alert(instance['name'], f"{service} could not be restarted automatically")

        client.close()
    except Exception as e:
        print(f"  ERROR connecting to {instance['name']}: {e}")
        send_alert(instance['name'], f"Could not connect to instance: {e}")

if __name__ == "__main__":
    for instance in INSTANCES:
        check_instance(instance)