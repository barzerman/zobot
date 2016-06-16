ssh -i "./scripts/botx.pem" ubuntu@ec2-52-34-35-240.us-west-2.compute.amazonaws.com << EOF
cd ~/zobot && git pull origin && ~/zobot/scripts/stop_bot.sh && ~/zobot/scripts/start_bot.sh
EOF