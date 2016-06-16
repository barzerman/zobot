#!/bin/bash
python api.py &
sleep 1
python telegram_bot.py &
