import { useState, useEffect, useRef } from "react";

const API = "http://localhost:5000/api";

const fmt = (n) => parseFloat(n || 0).toFixed(4);

function App() {
  const [tab, setTab] = useState("wallet");
  const [wallet, setWallet] = useState(null);
  const [chainInfo, setChainInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sendAddr, setSendAddr] = useState("");
  const [sendAmt, setSendAmt] = useState("");
  const [sendResult, setSendResult] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [bookRequest, setBookRequest] = useState("");
  const [teacher, setTeacher] = useState("Prof. Sharma");
  const [bookResult, setBookResult] = useState(null);
  const [conflict, setConflict] = useState(null);
  const [mineResult, setMineResult] = useState(null);
  const [copied, setCopied] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    fetchAll();
    intervalRef.current = setInterval(fetchAll, 10000);
    return () => clearInterval(intervalRef.current);
  }, []);

  const fetchAll = async () => {
    try {
      const [w, c, b] = await Promise.all([
        fetch(`${API}/wallet/info`).then(r => r.json()),
        fetch(`${API}/blockchain/info`).then(r => r.json()),
        fetch(`${API}/bookings`).then(r => r.json()),
      ]);
      if (w.status === "ok") setWallet(w);
      if (c.status === "ok") setChainInfo(c);
      if (b.status === "ok") setBookings(b.bookings);
    } catch (e) { console.error(e); }
  };

  const handleSend = async () => {
    if (!sendAddr || !sendAmt) return;
    setLoading(true); setSendResult(null);
    try {
      const r = await fetch(`${API}/wallet/send`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address: sendAddr, amount: parseFloat(sendAmt) })
      });
      const d = await r.json();
      setSendResult(d);
      if (d.status === "ok") { setSendAddr(""); setSendAmt(""); fetchAll(); }
    } catch (e) { setSendResult({ status: "error", message: e.message }); }
    setLoading(false);
  };

  const handleMine = async () => {
    setLoading(true); setMineResult(null);
    try {
      const r = await fetch(`${API}/wallet/mine`, { method: "POST" });
      const d = await r.json();
      setMineResult(d);
      fetchAll();
    } catch (e) { setMineResult({ status: "error", message: e.message }); }
    setLoading(false);
  };

  const handleBook = async () => {
    if (!bookRequest.trim()) return;
    setLoading(true); setBookResult(null); setConflict(null);
    try {
      const r = await fetch(`${API}/book`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request: bookRequest, teacher })
      });
      const d = await r.json();
      if (d.status === "conflict") setConflict(d);
      else { setBookResult(d); fetchAll(); }
    } catch (e) { setBookResult({ status: "error", message: e.message }); }
    setLoading(false);
  };

  const handleAcceptAlternate = async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/book/confirm-alternate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          teacher, lab: conflict.lab, date: conflict.date,
          start_time: conflict.alternate_start, end_time: conflict.alternate_end,
          purpose: conflict.parsed_request?.purpose || "Lab session"
        })
      });
      const d = await r.json();
      setBookResult(d); setConflict(null); fetchAll();
    } catch (e) { setBookResult({ status: "error", message: e.message }); }
    setLoading(false);
  };

  const copyAddress = () => {
    if (wallet?.receive_address) {
      navigator.clipboard.writeText(wallet.receive_address);
      setCopied(true); setTimeout(() => setCopied(false), 2000);
    }
  };

  const txColor = (cat) => cat === "receive" ? "#00ff88" : cat === "send" ? "#ff4466" : "#888";

  return (
    <div style={{
      fontFamily: "'Courier New', monospace",
      background: "#080c10",
      minHeight: "100vh",
      color: "#c8d8e8",
      backgroundImage: "radial-gradient(ellipse at 20% 50%, #0a1628 0%, transparent 60%), radial-gradient(ellipse at 80% 20%, #0d1f0d 0%, transparent 50%)"
    }}>
      {/* Header */}
      <div style={{
        background: "rgba(10,20,30,0.9)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid #1a3a2a",
        padding: "0 32px",
        display: "flex", alignItems: "center",
        position: "sticky", top: 0, zIndex: 100
      }}>
        <div style={{ padding: "16px 0", display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 36, height: 36, borderRadius: "50%",
            background: "linear-gradient(135deg, #00ff88, #00aa55)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 18, fontWeight: "bold", color: "#000"
          }}>₡</div>
          <div>
            <div style={{ fontSize: 18, fontWeight: "bold", letterSpacing: 3, color: "#00ff88" }}>CS-COIN</div>
            <div style={{ fontSize: 10, color: "#446644", letterSpacing: 2 }}>SHA-3 · 64-BIT NONCE · REGTEST</div>
          </div>
        </div>

        {chainInfo && (
          <div style={{ marginLeft: "auto", display: "flex", gap: 24, fontSize: 11 }}>
            <div style={{ textAlign: "center" }}>
              <div style={{ color: "#446644" }}>BLOCKS</div>
              <div style={{ color: "#00ff88", fontWeight: "bold" }}>{chainInfo.info?.blocks}</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ color: "#446644" }}>BALANCE</div>
              <div style={{ color: "#00ff88", fontWeight: "bold" }}>{fmt(chainInfo.balance)} CSC</div>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ color: "#446644" }}>NODE</div>
              <div style={{ color: "#00ff88" }}>● ONLINE</div>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 0, padding: "0 32px", borderBottom: "1px solid #0a2010" }}>
        {[["wallet","⬡ WALLET"], ["send","↗ SEND"], ["mine","⛏ MINE"], ["book","📋 BOOK LAB"], ["chain","⛓ CHAIN"]].map(([t, label]) => (
          <button key={t} onClick={() => setTab(t)} style={{
            background: "transparent",
            color: tab === t ? "#00ff88" : "#334433",
            border: "none",
            borderBottom: tab === t ? "2px solid #00ff88" : "2px solid transparent",
            padding: "14px 20px", cursor: "pointer",
            fontSize: 11, fontFamily: "inherit",
            letterSpacing: 2, transition: "all 0.2s"
          }}>{label}</button>
        ))}
      </div>

      <div style={{ padding: "32px", maxWidth: 860, margin: "0 auto" }}>

        {/* WALLET TAB */}
        {tab === "wallet" && wallet && (
          <div>
            {/* Balance Card */}
            <div style={{
              background: "linear-gradient(135deg, #0a1f0a, #0d2a1a)",
              border: "1px solid #1a4a2a",
              borderRadius: 12, padding: "32px",
              marginBottom: 24, textAlign: "center",
              position: "relative", overflow: "hidden"
            }}>
              <div style={{
                position: "absolute", top: -40, right: -40,
                width: 200, height: 200, borderRadius: "50%",
                background: "radial-gradient(circle, rgba(0,255,136,0.05) 0%, transparent 70%)"
              }} />
              <div style={{ fontSize: 11, color: "#446644", letterSpacing: 3, marginBottom: 8 }}>TOTAL BALANCE</div>
              <div style={{ fontSize: 52, fontWeight: "bold", color: "#00ff88", letterSpacing: -1 }}>
                {fmt(wallet.balance)}
              </div>
              <div style={{ fontSize: 16, color: "#336633", marginTop: 4 }}>CS-COIN</div>
            </div>

            {/* Receive Address */}
            <div style={{ background: "#0a1520", border: "1px solid #0a2a1a", borderRadius: 8, padding: 20, marginBottom: 24 }}>
              <div style={{ fontSize: 11, color: "#446644", letterSpacing: 2, marginBottom: 10 }}>YOUR RECEIVE ADDRESS</div>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{
                  flex: 1, background: "#050c10", border: "1px solid #0d2010",
                  borderRadius: 6, padding: "10px 14px",
                  fontSize: 12, color: "#00aa55", wordBreak: "break-all"
                }}>{wallet.receive_address}</div>
                <button onClick={copyAddress} style={{
                  background: copied ? "#00aa55" : "#0a2010",
                  color: copied ? "#000" : "#00ff88",
                  border: "1px solid #00ff88", borderRadius: 6,
                  padding: "10px 16px", cursor: "pointer",
                  fontFamily: "inherit", fontSize: 11, whiteSpace: "nowrap"
                }}>{copied ? "✓ COPIED" : "COPY"}</button>
              </div>
            </div>

            {/* Recent Transactions */}
            <div style={{ fontSize: 11, color: "#446644", letterSpacing: 2, marginBottom: 12 }}>RECENT TRANSACTIONS</div>
            {wallet.transactions?.length === 0 && (
              <div style={{ color: "#223322", textAlign: "center", padding: 32 }}>No transactions yet</div>
            )}
            {[...wallet.transactions || []].reverse().map((tx, i) => (
              <div key={i} style={{
                background: "#0a1520", border: "1px solid #0a1f10",
                borderRadius: 8, padding: "14px 16px", marginBottom: 8,
                display: "flex", alignItems: "center", gap: 16
              }}>
                <div style={{
                  width: 32, height: 32, borderRadius: "50%",
                  background: tx.category === "receive" ? "rgba(0,255,136,0.1)" : "rgba(255,68,102,0.1)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 14
                }}>{tx.category === "receive" ? "↙" : "↗"}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: "#557755", marginBottom: 2 }}>
                    {tx.category?.toUpperCase()} · {new Date(tx.time * 1000).toLocaleString()}
                  </div>
                  <div style={{ fontSize: 11, color: "#334433", wordBreak: "break-all" }}>
                    {tx.txid?.slice(0, 32)}...
                  </div>
                </div>
                <div style={{ fontSize: 16, fontWeight: "bold", color: txColor(tx.category) }}>
                  {tx.category === "receive" ? "+" : ""}{fmt(tx.amount)} CSC
                </div>
              </div>
            ))}
          </div>
        )}

        {/* SEND TAB */}
        {tab === "send" && (
          <div>
            <div style={{ fontSize: 11, color: "#446644", letterSpacing: 2, marginBottom: 24 }}>SEND CS-COIN</div>
            <div style={{ background: "#0a1520", border: "1px solid #0a2010", borderRadius: 10, padding: 24 }}>
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 11, color: "#446644", letterSpacing: 2, marginBottom: 8 }}>RECIPIENT ADDRESS</div>
                <input value={sendAddr} onChange={e => setSendAddr(e.target.value)}
                  placeholder="bcrt1q..."
                  style={{
                    width: "100%", background: "#050c10", border: "1px solid #0a2010",
                    color: "#00aa55", padding: "12px 14px", fontFamily: "inherit",
                    fontSize: 13, borderRadius: 6, outline: "none", boxSizing: "border-box"
                  }} />
              </div>
              <div style={{ marginBottom: 24 }}>
                <div style={{ fontSize: 11, color: "#446644", letterSpacing: 2, marginBottom: 8 }}>AMOUNT (CSC)</div>
                <input value={sendAmt} onChange={e => setSendAmt(e.target.value)}
                  placeholder="0.0000" type="number" step="0.0001"
                  style={{
                    width: "100%", background: "#050c10", border: "1px solid #0a2010",
                    color: "#00ff88", padding: "12px 14px", fontFamily: "inherit",
                    fontSize: 20, borderRadius: 6, outline: "none", boxSizing: "border-box"
                  }} />
              </div>
              <button onClick={handleSend} disabled={loading || !sendAddr || !sendAmt}
                style={{
                  width: "100%", background: loading ? "#0a2010" : "linear-gradient(135deg, #00aa55, #00ff88)",
                  color: "#000", border: "none", padding: "14px",
                  fontFamily: "inherit", fontSize: 13, fontWeight: "bold",
                  letterSpacing: 2, cursor: loading ? "not-allowed" : "pointer", borderRadius: 6
                }}>
                {loading ? "SENDING..." : "↗ SEND CSC"}
              </button>

              {sendResult && (
                <div style={{
                  marginTop: 16, padding: 14, borderRadius: 6,
                  background: sendResult.status === "ok" ? "rgba(0,255,136,0.05)" : "rgba(255,68,102,0.05)",
                  border: `1px solid ${sendResult.status === "ok" ? "#00aa55" : "#ff4466"}`
                }}>
                  {sendResult.status === "ok" ? (
                    <div>
                      <div style={{ color: "#00ff88", marginBottom: 4 }}>✓ TRANSACTION SENT</div>
                      <div style={{ fontSize: 11, color: "#446644", wordBreak: "break-all" }}>TX: {sendResult.tx_id}</div>
                    </div>
                  ) : (
                    <div style={{ color: "#ff4466" }}>✗ {sendResult.message}</div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* MINE TAB */}
        {tab === "mine" && (
          <div>
            <div style={{ fontSize: 11, color: "#446644", letterSpacing: 2, marginBottom: 24 }}>MINE BLOCKS</div>
            <div style={{ background: "#0a1520", border: "1px solid #0a2010", borderRadius: 10, padding: 32, textAlign: "center" }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>⛏</div>
              <div style={{ color: "#557755", marginBottom: 8, fontSize: 13 }}>Current Balance</div>
              <div style={{ fontSize: 36, color: "#00ff88", fontWeight: "bold", marginBottom: 24 }}>
                {fmt(wallet?.balance)} CSC
              </div>
              <button onClick={handleMine} disabled={loading}
                style={{
                  background: loading ? "#0a2010" : "linear-gradient(135deg, #1a4a1a, #00aa55)",
                  color: loading ? "#446644" : "#00ff88",
                  border: "1px solid #00aa55", padding: "16px 48px",
                  fontFamily: "inherit", fontSize: 13, fontWeight: "bold",
                  letterSpacing: 3, cursor: loading ? "not-allowed" : "pointer", borderRadius: 6
                }}>
                {loading ? "MINING..." : "⛏ MINE BLOCK"}
              </button>
              {mineResult && mineResult.status === "ok" && (
                <div style={{ marginTop: 20, fontSize: 12, color: "#446644" }}>
                  <div style={{ color: "#00ff88", marginBottom: 4 }}>✓ BLOCK MINED</div>
                  <div>New balance: {fmt(mineResult.new_balance)} CSC</div>
                  <div style={{ wordBreak: "break-all", marginTop: 4 }}>Hash: {mineResult.block_hash?.slice(0, 32)}...</div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* BOOK LAB TAB */}
        {tab === "book" && (
          <div>
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 11, color: "#446644", letterSpacing: 2, marginBottom: 8 }}>YOUR NAME</div>
              <input value={teacher} onChange={e => setTeacher(e.target.value)}
                style={{ width: "100%", background: "#0a1520", border: "1px solid #0a2010", color: "#c8d8e8", padding: "10px 14px", fontFamily: "inherit", fontSize: 13, borderRadius: 6, outline: "none", boxSizing: "border-box" }} />
            </div>
            <div style={{ marginBottom: 20 }}>
              <div style={{ fontSize: 11, color: "#446644", letterSpacing: 2, marginBottom: 8 }}>BOOKING REQUEST (NATURAL LANGUAGE)</div>
              <textarea value={bookRequest} onChange={e => setBookRequest(e.target.value)}
                placeholder='e.g. "Book Lab-A tomorrow at 2pm for 2 hours for OS lab"'
                rows={3} style={{ width: "100%", background: "#0a1520", border: "1px solid #0a2010", color: "#c8d8e8", padding: "10px 14px", fontFamily: "inherit", fontSize: 13, borderRadius: 6, outline: "none", resize: "vertical", boxSizing: "border-box" }} />
            </div>
            <button onClick={handleBook} disabled={loading}
              style={{ background: loading ? "#0a2010" : "linear-gradient(135deg, #1a3a4a, #0088aa)", color: loading ? "#446644" : "#88ddff", border: "none", padding: "12px 32px", fontFamily: "inherit", fontSize: 11, fontWeight: "bold", letterSpacing: 2, cursor: loading ? "not-allowed" : "pointer", borderRadius: 6 }}>
              {loading ? "PROCESSING AGENTS..." : "🤖 SUBMIT TO AI AGENTS"}
            </button>

            {conflict && (
              <div style={{ marginTop: 20, background: "rgba(255,170,0,0.05)", border: "1px solid #aa7700", borderRadius: 8, padding: 20 }}>
                <div style={{ color: "#ffaa00", fontWeight: "bold", marginBottom: 8 }}>⚠ CONFLICT DETECTED</div>
                <div style={{ color: "#887755", fontSize: 12, marginBottom: 12 }}>{conflict.message}</div>
                <div style={{ color: "#557755", fontSize: 12, marginBottom: 16 }}>
                  Alternate: <span style={{ color: "#00ff88" }}>{conflict.alternate_start}–{conflict.alternate_end}</span> on {conflict.date}
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={handleAcceptAlternate} style={{ background: "#00aa55", color: "#000", border: "none", padding: "8px 20px", fontFamily: "inherit", fontSize: 11, fontWeight: "bold", cursor: "pointer", borderRadius: 4 }}>✓ ACCEPT</button>
                  <button onClick={() => setConflict(null)} style={{ background: "#1a1a1a", color: "#888", border: "1px solid #333", padding: "8px 20px", fontFamily: "inherit", fontSize: 11, cursor: "pointer", borderRadius: 4 }}>CANCEL</button>
                </div>
              </div>
            )}

            {bookResult?.status === "confirmed" && (
              <div style={{ marginTop: 20, background: "rgba(0,255,136,0.03)", border: "1px solid #00aa55", borderRadius: 8, padding: 20 }}>
                <div style={{ color: "#00ff88", fontWeight: "bold", marginBottom: 8 }}>✓ BOOKING CONFIRMED</div>
                <div style={{ color: "#557755", fontSize: 12, marginBottom: 12 }}>{bookResult.message}</div>
                <div style={{ fontSize: 11, color: "#335533", wordBreak: "break-all" }}>⛓ TX: {bookResult.tx_id}</div>
              </div>
            )}

            <div style={{ marginTop: 32, fontSize: 11, color: "#446644", letterSpacing: 2, marginBottom: 12 }}>RECENT BOOKINGS</div>
            {bookings.slice(0, 5).map(b => (
              <div key={b.id} style={{ background: "#0a1520", border: "1px solid #0a1f10", borderRadius: 6, padding: "12px 16px", marginBottom: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ color: "#00aa55", fontSize: 12, marginBottom: 2 }}>{b.lab} · {b.date} · {b.start_time}–{b.end_time}</div>
                  <div style={{ color: "#335533", fontSize: 11 }}>{b.teacher} · {b.purpose}</div>
                </div>
                <div style={{ fontSize: 10, color: "#224422" }}>#{b.id}</div>
              </div>
            ))}
          </div>
        )}

        {/* CHAIN TAB */}
        {tab === "chain" && chainInfo && (
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 24 }}>
              {[
                ["BLOCKS", chainInfo.info?.blocks],
                ["BALANCE", `${fmt(chainInfo.balance)} CSC`],
                ["ALGO", "SHA-3"],
                ["NONCE", "64-BIT"],
                ["BLOCK TIME", "1 MIN"],
                ["NETWORK", "REGTEST"],
              ].map(([label, value]) => (
                <div key={label} style={{ background: "#0a1520", border: "1px solid #0a2010", borderRadius: 8, padding: 16, textAlign: "center" }}>
                  <div style={{ fontSize: 10, color: "#335533", letterSpacing: 2, marginBottom: 6 }}>{label}</div>
                  <div style={{ fontSize: 16, color: "#00ff88", fontWeight: "bold" }}>{value}</div>
                </div>
              ))}
            </div>
            <div style={{ background: "#0a1520", border: "1px solid #0a2010", borderRadius: 8, padding: 16, marginBottom: 12 }}>
              <div style={{ fontSize: 10, color: "#335533", letterSpacing: 2, marginBottom: 8 }}>BEST BLOCK HASH</div>
              <div style={{ fontSize: 11, color: "#00aa55", wordBreak: "break-all" }}>{chainInfo.info?.bestblockhash}</div>
            </div>
            <div style={{ background: "#0a1520", border: "1px solid #0a2010", borderRadius: 8, padding: 16 }}>
              <div style={{ fontSize: 10, color: "#335533", letterSpacing: 2, marginBottom: 12 }}>CS-COIN vs BITCOIN</div>
              {[
                ["Hash Algorithm", "SHA-256d", "SHA-3 (Keccak-256)"],
                ["Nonce Size", "32-bit", "64-bit"],
                ["Block Time", "10 min", "1 min"],
                ["Halving", "210,000 blocks", "105,000 blocks"],
                ["Genesis Reward", "50 BTC", "100 CSC"],
                ["Port", "8333", "9333"],
              ].map(([label, from, to]) => (
                <div key={label} style={{ display: "flex", justifyContent: "space-between", fontSize: 11, padding: "8px 0", borderBottom: "1px solid #0a1a0a" }}>
                  <span style={{ color: "#446644" }}>{label}</span>
                  <span style={{ color: "#334433" }}>{from} → <span style={{ color: "#00aa55" }}>{to}</span></span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
