#!/bin/bash
echo "🪙 Starting CS-Coin System..."

# Start blockchain node
echo "Starting CS-Coin node..."
~/Documents/Blockchain\ /bitcoin/build/bin/bitcoind -regtest -datadir=$HOME/.cscoin -daemon
sleep 3

# Activate venv and start Flask
echo "Starting AI Agent backend..."
cd ~/Documents/Blockchain\ /cscoin-agents
source ~/Documents/Blockchain\ /bitcoin/cscoin-env/bin/activate
python app.py &
FLASK_PID=$!
echo "Flask PID: $FLASK_PID"
sleep 2

# Start frontend
echo "Starting React frontend..."
cd ~/Documents/Blockchain\ /cscoin-agents/frontend
npm run dev &
VITE_PID=$!

echo ""
echo "✅ CS-Coin System Running!"
echo "   Frontend:   http://localhost:5173"
echo "   Backend:    http://localhost:5000"
echo "   Blockchain: regtest @ ~/.cscoin"
echo ""
echo "Press Ctrl+C to stop all services"
wait
