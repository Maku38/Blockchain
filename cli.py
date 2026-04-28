#!/usr/bin/env python3
"""
CS-Coin CLI - Interact with blockchain and wallets from command line
"""
import requests
import json
import sys
from database.users import get_all_users
from blockchain.cscoin import cli

API = "http://100.119.187.10:5000/api"

def show_users():
    """List all registered users/wallets"""
    print("\n" + "="*70)
    print("📋 ALL REGISTERED WALLETS")
    print("="*70)
    users = get_all_users()
    if not users:
        print("No users registered yet")
        return
    
    for user in users:
        print(f"\n👤 Username: {user['username']}")
        print(f"   Address:  {user['csc_address']}")
        try:
            balance = float(cli(["getreceivedbyaddress", user['csc_address'], "0"]))
            print(f"   Balance:  {balance:.4f} CSC")
        except:
            print(f"   Balance:  0.0000 CSC")

def show_blockchain_info():
    """Show blockchain information"""
    print("\n" + "="*70)
    print("⛓  BLOCKCHAIN INFO")
    print("="*70)
    try:
        r = requests.get(f"{API}/blockchain/info")
        data = r.json()
        if data.get("status") == "ok":
            info = data.get("info", {})
            print(f"Blocks:       {info.get('blocks')}")
            print(f"Difficulty:   {info.get('difficulty')}")
            print(f"Chain:        {info.get('chain')}")
            print(f"Best Hash:    {info.get('bestblockhash', '')[:32]}...")
            print(f"Network:      {info.get('networkactive')}")
            print(f"Node Balance: {data.get('balance', 0):.4f} CSC")
    except Exception as e:
        print(f"Error: {e}")

def show_transactions():
    """Show recent transactions"""
    print("\n" + "="*70)
    print("📜 RECENT TRANSACTIONS")
    print("="*70)
    try:
        r = requests.get(f"{API}/wallet/transactions")
        data = r.json()
        if data.get("status") == "ok":
            txs = data.get("transactions", [])
            if not txs:
                print("No transactions yet")
                return
            for tx in txs[:20]:
                print(f"\n  TX: {tx['txid'][:16]}...")
                print(f"     Amount: {tx.get('amount', 0):.4f} CSC")
                print(f"     From:   {tx.get('address', 'N/A')}")
                print(f"     Status: {'Confirmed' if tx.get('confirmations', 0) > 0 else 'Unconfirmed'}")
    except Exception as e:
        print(f"Error: {e}")

def send_coin(to_address, amount):
    """Send CSC to an address"""
    print(f"\n💸 Sending {amount} CSC to {to_address}...")
    try:
        tx_id = cli(["sendtoaddress", to_address, str(amount)])
        print(f"✓ Success! TX ID: {tx_id}")
    except Exception as e:
        print(f"✗ Error: {e}")

def mine_block():
    """Mine a block"""
    print("\n⛏  Mining block...")
    try:
        r = requests.post(f"{API}/wallet/mine")
        data = r.json()
        if data.get("status") == "ok":
            print(f"✓ Block mined!")
            print(f"  Hash: {data.get('block_hash', '')[:16]}...")
            print(f"  New balance: {data.get('new_balance', 0):.4f} CSC")
    except Exception as e:
        print(f"✗ Error: {e}")

def get_wallet_balance(address):
    """Get balance for a specific address"""
    print(f"\n💰 Getting balance for {address[:12]}...")
    try:
        r = requests.get(f"{API}/wallet/balance/{address}")
        data = r.json()
        if data.get("status") == "ok":
            print(f"Balance: {data.get('balance', 0):.4f} CSC")
    except Exception as e:
        print(f"✗ Error: {e}")

def show_help():
    """Show help"""
    print("""
    CS-Coin CLI
    ===========
    
    Usage: ./cli.py <command> [args]
    
    Commands:
      users              - List all registered users/wallets
      blockchain         - Show blockchain info
      transactions       - Show recent transactions
      balance <address>  - Get balance for address
      send <addr> <amt>  - Send CSC to address
      mine               - Mine a block
      help               - Show this help
    
    Examples:
      ./cli.py users
      ./cli.py blockchain
      ./cli.py send cSCoinAddress 10.5
      ./cli.py mine
    """)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "users":
        show_users()
    elif cmd == "blockchain":
        show_blockchain_info()
    elif cmd == "transactions":
        show_transactions()
    elif cmd == "balance" and len(sys.argv) > 2:
        get_wallet_balance(sys.argv[2])
    elif cmd == "send" and len(sys.argv) > 3:
        send_coin(sys.argv[2], float(sys.argv[3]))
    elif cmd == "mine":
        mine_block()
    elif cmd == "help" or cmd == "-h":
        show_help()
    else:
        print(f"Unknown command: {cmd}")
        show_help()
