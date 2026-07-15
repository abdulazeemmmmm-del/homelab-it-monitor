# config.py
# Never commit this file with real secrets - it's already in .gitignore

KEY_PATH = r"C:\Users\B650M GAMING WIFI\Downloads\homelab-key.pem"
SSH_USER = "ec2-user"

INSTANCES = [
    {
        "name": "web-server-1",
        "ip": "13.229.184.94",
        "check_service": "nginx"
    },
    {
        "name": "cron-host",
        "ip": "47.129.217.180",
        "check_service": None  # we'll check the cron log file instead
    },
    {
        "name": "control-node",
        "ip": "54.169.115.42",
        "check_service": None
    }
]