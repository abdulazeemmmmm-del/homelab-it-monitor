Homelab IT Monitor
I built this to get some real hands-on practice with the stuff I've been learning — AWS, Linux, and Python — and to have something concrete to show for it beyond a certificate.
The idea: a few EC2 servers, a script that watches them, and a system that tries to fix problems on its own before bothering a human. Basically a tiny version of what a help desk / IT support setup looks like in the real world.
What it actually does
It SSHes into each server, checks if it's healthy (disk space, memory, and whether the right service is running), and if something's down, it tries to restart it. Whatever happens gets written to a log file — like a ticket history. If it tries to fix something and can't, it emails me so I know to go look at it myself.
So the loop is: check → try to fix → double check it worked → write it down → email me if it's still broken.
Architecture
```
                    ┌─────────────────────────────────────┐
                    │      AWS EC2 (Linux instances)       │
                    │                                       │
                    │  web-server-1   cron-host   control-  │
                    │  (nginx)        (cron job)  node      │
                    └───────────────┬───────────────────────┘
                                    │ SSH (paramiko)
                                    ▼
                        ┌───────────────────────┐
                        │   monitor.py           │
                        │   Python monitoring    │
                        │   \& remediation script │
                        └───────┬───────┬────────┘
                                │       │
                    ┌───────────▼──┐ ┌──▼─────────────┐
                    │ ticket\_log   │ │ AWS SNS         │
                    │ .csv         │ │ (email alert)   │
                    │ audit trail  │ │ on unresolved   │
                    └──────────────┘ └─────────────────┘
```
Components
3 EC2 instances (Amazon Linux 2023, free tier eligible)
`web-server-1` — running nginx, this is the one that actually gets monitored
`cron-host` — has a cron job running every minute, logging to a file
`control-node` — left alone on purpose, just a baseline to compare against
`monitor.py` — the actual script. Connects over SSH with paramiko, checks each server, and restarts a service if it's found down
`ticket\_log.csv` — every issue and every fix attempt gets a row here with a timestamp, so there's an actual record of what happened
AWS SNS — sends me an email if the script tries to fix something and fails
`config.py` — instance IPs, SSH key path, that kind of thing (kept out of git, obviously — has real details in it)
Setting it up
You'll need an AWS account, an IAM user (don't use root for this), Python, and an SSH key pair.
1. Clone it and set up a virtual environment
```powershell
git clone https://github.com/abdulazeemmmmm-del/homelab-it-monitor.git
cd homelab-it-monitor
python -m venv venv
venv\\Scripts\\activate
pip install paramiko boto3
```
2. Launch the EC2 instances
3x t2.micro/t3.micro, Amazon Linux 2023. Open port 22 (SSH, restricted to your IP) and port 80 if you're running nginx on one of them. Put nginx on one instance, a cron job on another, leave the third one idle.
3. Set up alerting
Create an SNS topic, subscribe your email to it, confirm the subscription (check your inbox), then create an IAM access key and run `aws configure` locally so the script can actually send to it.
4. Fill in `config.py`
Your instance IPs, the path to your `.pem` key, and your SNS topic ARN go here.
5. Run it
```powershell
python monitor.py
```
What happens when something goes wrong
Situation	How it's caught	What the script does	If that doesn't work
nginx (or whatever service) stops	`systemctl is-active` comes back non-active	Restarts it, then checks again	Logs it as failed, sends me an email
Can't SSH into the instance at all	Connection just throws an error	Nothing to fix here — logs it right away	Sends me an email with the error
Disk or memory looks off	Shown every run	Nothing automatic yet, just reported	I'd have to check manually
Every single thing it catches, and whatever it did about it, ends up as a row in `ticket\_log.csv` with a timestamp.
What it actually looks like running
```
Checking web-server-1 (13.229.184.94)...
  Disk usage: 22%
  Memory: 175/912 MB
  Service 'nginx': inactive
  ISSUE DETECTED: nginx is not active. Attempting restart...
  \[LOGGED] nginx was inactive -> restarted nginx -> SUCCESS - now active
```
Why I built this
I'm working toward becoming a cloud engineer, and I wanted something that actually proves I can use Linux, AWS, and Python together, not just define them. This covers a lot of what comes up day to day in IT support — checking on servers, fixing the obvious stuff, knowing when to escalate, and keeping a record of what happened.
Things I might add later
Auto-fixing high disk usage (clearing logs/temp files)
Running this on a schedule instead of manually (cron, or EventBridge)
A small dashboard instead of just a CSV, so the ticket history is easier to look at