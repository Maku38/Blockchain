#!/bin/bash
echo "Stopping CS-Coin System..."
~/Documents/Blockchain\ /bitcoin/build/bin/bitcoin-cli -regtest -datadir=$HOME/.cscoin stop
pkill -f "python app.py"
pkill -f "vite"
echo "✅ All services stopped"
