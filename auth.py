from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from database.users import init_users_db, create_user, verify_password, get_user
from blockchain.cscoin import cli, get_balance, mine_block
from logger import get_logger
import json

logger = get_logger("auth")
auth_bp = Blueprint('auth', __name__)
init_users_db()

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    csc_address = data.get("csc_address", "").strip()
    if not username or not password or not csc_address:
        return jsonify({"status": "error", "message": "username, password and csc_address required"}), 400
    if len(username) < 3:
        return jsonify({"status": "error", "message": "Username must be at least 3 characters"}), 400
    if len(password) < 6:
        return jsonify({"status": "error", "message": "Password must be at least 6 characters"}), 400
    try:
        user = create_user(username, password, csc_address)
        access_token = create_access_token(identity=username)
        logger.info(f"New user registered: {username}")
        return jsonify({"status": "ok", "message": f"Welcome to CS-Coin, {username}!", "token": access_token, "user": {"username": username, "csc_address": csc_address}})
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")
    user = verify_password(username, password)
    if not user:
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401
    access_token = create_access_token(identity=username)
    logger.info(f"User logged in: {username}")
    return jsonify({"status": "ok", "token": access_token, "user": {"username": user["username"], "csc_address": user["csc_address"]}})

@auth_bp.route('/api/auth/me', methods=['GET'])
@jwt_required()
def me():
    username = get_jwt_identity()
    user = get_user(username)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404
    return jsonify({"status": "ok", "user": {"username": user["username"], "csc_address": user["csc_address"]}})

@auth_bp.route('/api/wallet/balance/<address>', methods=['GET'])
def get_address_balance(address):
    """Get spendable balance using scantxoutset"""
    try:
        result = json.loads(cli(["scantxoutset", "start",
            json.dumps([{"desc": f"addr({address})"}])]))
        balance = result.get("total_amount", 0.0)
        return jsonify({"status": "ok", "address": address, "balance": balance})
    except Exception as e:
        logger.error(f"Balance check failed for {address}: {e}")
        return jsonify({"status": "ok", "address": address, "balance": 0.0})

@auth_bp.route('/api/wallet/txhistory/<address>', methods=['GET'])
def get_tx_history(address):
    """Get transaction history filtered by address"""
    try:
        txs = json.loads(cli(["listtransactions", "*", "50"]))
        addr_txs = [tx for tx in txs if tx.get("address") == address]
        return jsonify({"status": "ok", "transactions": addr_txs})
    except Exception as e:
        return jsonify({"status": "ok", "transactions": []})

@auth_bp.route('/api/wallet/broadcast', methods=['POST'])
@jwt_required()
def broadcast_tx():
    data = request.json
    signed_tx_hex = data.get("signed_tx")
    if not signed_tx_hex:
        return jsonify({"status": "error", "message": "signed_tx required"}), 400
    try:
        tx_id = cli(["sendrawtransaction", signed_tx_hex])
        mine_block()
        logger.info(f"Transaction broadcast: {tx_id}")
        return jsonify({"status": "ok", "tx_id": tx_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@auth_bp.route('/api/wallet/utxos/<address>', methods=['GET'])
def get_utxos(address):
    try:
        result = json.loads(cli(["scantxoutset", "start", json.dumps([{"desc": f"addr({address})"}])]))
        utxos = result.get("unspents", [])
        return jsonify({"status": "ok", "utxos": utxos, "total": result.get("total_amount", 0)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
