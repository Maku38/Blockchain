import subprocess
import json
import os

BITCOIN_CLI = os.path.expanduser("~/Documents/Blockchain /bitcoin/build/bin/bitcoin-cli")
DATADIR = os.path.expanduser("~/.cscoin")
NETWORK = "-regtest"
WALLET = "cscoin_wallet"

def cli(command: list) -> str:
    cmd = [BITCOIN_CLI, NETWORK, f"-datadir={DATADIR}", f"-rpcwallet={WALLET}"] + command
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"CLI error: {result.stderr.strip()}")
    return result.stdout.strip()

def get_new_address() -> str:
    return cli(["getnewaddress"])

def get_balance() -> float:
    return float(cli(["getbalance"]))

def log_booking_to_blockchain(booking_details: dict) -> str:
    booking_summary = (
        f"CSCOIN-BOOKING:"
        f"lab={booking_details['lab']},"
        f"teacher={booking_details['teacher']},"
        f"date={booking_details['date']},"
        f"time={booking_details['start_time']}-{booking_details['end_time']}"
    )
    booking_hex = booking_summary[:80].encode('utf-8').hex()
    address = get_new_address()

    unspent = json.loads(cli(["listunspent"]))
    if not unspent:
        mine_block()
        unspent = json.loads(cli(["listunspent"]))

    utxo = unspent[0]
    inputs = json.dumps([{"txid": utxo["txid"], "vout": utxo["vout"]}])
    fee = 0.0001
    change = round(utxo["amount"] - fee, 8)
    outputs = json.dumps({
        address: change,
        "data": booking_hex
    })

    raw_tx = cli(["createrawtransaction", inputs, outputs])
    signed = json.loads(cli(["signrawtransactionwithwallet", raw_tx]))
    tx_id = cli(["sendrawtransaction", signed["hex"]])
    mine_block()
    return tx_id

def mine_block():
    address = get_new_address()
    cli(["generatetoaddress", "1", address])

def get_transaction(tx_id: str) -> dict:
    return json.loads(cli(["gettransaction", tx_id]))

def get_blockchain_info() -> dict:
    return json.loads(cli(["getblockchaininfo"]))
