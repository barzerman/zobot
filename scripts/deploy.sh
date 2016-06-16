#!/bin/bash
ssh -i "./scripts/botx.pem" ubuntu@ec2-52-34-35-240.us-west-2.compute.amazonaws.com << EOF
cd ~/zobot && git pull origin && source venv/bin/activate && pip install -r requirements.txt && echo "`whoami`" &&  (exec "./scripts/stop_bot.sh") && (exec "./scripts/start_bot.sh") && echo '[OK]'
EOF