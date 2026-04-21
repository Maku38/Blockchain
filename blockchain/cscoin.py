import subprocess
import json
import os
from typing import Optional
from logger import get_logger

logger = get_logger("blockchain")

BITCOIN_CLI = os.path.expanduser("~/Documents/Blockchain /bitcoin/build/bin/bitcoin-cli")
DATADIR = os.path.expanduser("~/.cscoin")
NETWORK = "-regtest"
WALLET = "cscoin_wallet"

def cli(command: list) -> str:
    cmd = [BITCOIN_CLI, NETWORK, f"-datadir={DATADIR}", f"-rpcwallet={WALLET}"] + command
    logger.debug(f"CLI command: {' '.join(command)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        err = result.stderr.strip()
        logger.error(f"CLI error: {err}")
        raise RuntimeError(f"bitcoin-cli error: {err}")
    return result.stdout.strip()

def is_node_running() -> bool:
    try:
        cli(["getblockchaininfo"])
        return True
    except RuntimeError:
        return False

def get_new_address() -> str:
    addr = cli(["getnewaddress"])
    logger.debug(f"New address: {addr}")
    return addr

def get_balance() -> float:
    balance = float(cli(["getbalance"]))
    logger.debug(f"Balance: {balance} CSC")
    return balance

def mine_block() -> str:
    address = get_new_address()
    result = cli(["generatetoaddress", "1", address])
    hashes = json.loads(result)
    logger.info(f"Mined block: {hashes[0][:16]}...")
    return hashes[0]

def log_booking_to_blockchain(booking_details: dict) -> str:
    """
    Log a confirmed booking as a CS-Coin OP_RETURN transaction.
    Booking data is encoded in transaction metadata (immutable proof).
    Returns the transaction ID.
    """
    booking_summary = (
        f"CSCOIN-BOOKING:"
        f"lab={booking_details['lab']},"
        f"teacher={booking_details['teacher']},"
        f"date={booking_details['date']},"
        f"time={booking_details['start_time']}-{booking_details['end_time']}"
    )
    booking_hex = booking_summary[:80].encode('utf-8').hex()
    logger.info(f"Logging to blockchain: {booking_summary[:60]}...")

    address = get_new_address()
    unspent = json.loads(cli(["listunspent"]))

    if not unspent:
        logger.info("No UTXOs found, mining a block first...")
        mine_block()
        unspent = json.loads(cli(["listunspent"]))

    if not unspent:
        raise RuntimeError("No UTXOs available after mining")

    utxo = unspent[0]
    fee = 0.0001

    if utxo["amount"] <= fee:
        raise RuntimeError(f"UTXO amount {utxo['amount']} too small to cover fee {fee}")

    change = round(utxo["amount"] - fee, 8)
    inputs = json.dumps([{"txid": utxo["txid"], "vout": utxo["vout"]}])
    outputs = json.dumps({"data": booking_hex, address: change})

    raw_tx = cli(["createrawtransaction", inputs, outputs])
    signed_result = json.loads(cli(["signrawtransactionwithwallet", raw_tx]))

    if not signed_result.get("complete"):
        raise RuntimeError("Transaction signing failed")

    tx_id = cli(["sendrawtransaction", signed_result["hex"]])
    mine_block()  # confirm immediately in regtest

    logger.info(f"Booking logged to blockchain. TX: {tx_id}")
    return tx_id

def get_transaction(tx_id: str) -> dict:
    return json.loads(cli(["gettransaction", tx_id]))

def get_blockchain_info() -> dict:
    return json.loads(cli(["getblockchaininfo"]))
