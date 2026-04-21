# CS-Coin Bitcoin Fork - Build Instructions

## Prerequisites
```bash
sudo apt update
sudo apt install build-essential libtool autotools-dev automake pkg-config bsdmainutils python3
sudo apt install libevent-dev libboost-dev libsqlite3-dev
```

## Steps
1. Clone Bitcoin Core:
```bash
git clone https://github.com/bitcoin/bitcoin.git
cd bitcoin
```

2. Copy modified files from `bitcoin-fork/` into the cloned repo:
```bash
cp -r bitcoin-fork/src/* bitcoin/src/
cp bitcoin-fork/CMakeLists.txt bitcoin/
```

3. Build:
```bash
cmake -B build -DBUILD_GUI=OFF -DBUILD_TESTS=OFF -DBUILD_TX=OFF -DBUILD_UTIL=OFF -DENABLE_IPC=OFF
cmake --build build -j$(nproc)
```

4. Run:
```bash
mkdir -p ~/.cscoin
./build/bin/bitcoind -regtest -datadir=$HOME/.cscoin -daemon
```

## Changes Made to Bitcoin Core
| File | Change |
|---|---|
| src/hash.h | CHash256 → SHA3_256 (Keccak), HashWriter → SHA3 |
| src/primitives/block.h | nNonce: uint32_t → uint64_t |
| src/primitives/block.cpp | Format string %u → %lu for nNonce |
| src/chain.h | nNonce: uint32_t → uint64_t |
| src/rpc/mining.cpp | Nonce limit: uint32_t::max → uint64_t::max |
| src/kernel/chainparams.cpp | Magic bytes, port, block time, reward, halving |
| src/policy/feerate.h | Currency: BTC → CSC |
| CMakeLists.txt | Project name: BitcoinCore → CSCoin |
| src/common/args.cpp | Data dir: .bitcoin → .cscoin |
