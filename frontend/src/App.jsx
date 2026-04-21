import { useState, useEffect } from "react";

const API = "http://localhost:5000/api";

function App() {
  const [tab, setTab] = useState("book");
  const [teacher, setTeacher] = useState("Prof. Sharma");
  const [request, setRequest] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [chainInfo, setChainInfo] = useState(null);
  const [conflict, setConflict] = useState(null);

  useEffect(() => {
    fetchBookings();
    fetchChainInfo();
  }, []);

  const fetchBookings = async () => {
    const res = await fetch(`${API}/bookings`);
    const data = await res.json();
    setBookings(data.bookings || []);
  };

  const fetchChainInfo = async () => {
    const res = await fetch(`${API}/blockchain/info`);
    const data = await res.json();
    setChainInfo(data);
  };

  const handleBook = async () => {
    if (!request.trim()) return;
    setLoading(true);
    setResult(null);
    setConflict(null);
    try {
      const res = await fetch(`${API}/book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request, teacher }),
      });
      const data = await res.json();
      if (data.status === "conflict") {
        setConflict(data);
      } else {
        setResult(data);
        fetchBookings();
        fetchChainInfo();
      }
    } catch (e) {
      setResult({ status: "error", message: e.message });
    }
    setLoading(false);
  };

  const handleAcceptAlternate = async () => {
    if (!conflict) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/book/confirm-alternate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          teacher,
          lab: conflict.lab,
          date: conflict.date,
          start_time: conflict.alternate_start,
          end_time: conflict.alternate_end,
          purpose: conflict.parsed_request?.purpose || "Lab session",
        }),
      });
      const data = await res.json();
      setResult(data);
      setConflict(null);
      fetchBookings();
      fetchChainInfo();
    } catch (e) {
      setResult({ status: "error", message: e.message });
    }
    setLoading(false);
  };

  return (
    <div style={{ fontFamily: "monospace", background: "#0a0a0a", minHeight: "100vh", color: "#e0e0e0" }}>
      {/* Header */}
      <div style={{ background: "#111", borderBottom: "2px solid #f7931a", padding: "16px 32px", display: "flex", alignItems: "center", gap: 16 }}>
        <span style={{ fontSize: 28 }}>🪙</span>
        <div>
          <div style={{ fontSize: 22, fontWeight: "bold", color: "#f7931a" }}>CS-Coin</div>
          <div style={{ fontSize: 11, color: "#888" }}>Autonomous Academic Resource Management · Blockchain Powered</div>
        </div>
        {chainInfo && (
          <div style={{ marginLeft: "auto", textAlign: "right", fontSize: 12 }}>
            <div style={{ color: "#4caf50" }}>● Node Online</div>
            <div style={{ color: "#aaa" }}>Blocks: {chainInfo.info?.blocks} · Balance: {chainInfo.balance?.toFixed(2)} CSC</div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 0, borderBottom: "1px solid #222", padding: "0 32px" }}>
        {["book", "bookings", "blockchain"].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            background: tab === t ? "#1a1a1a" : "transparent",
            color: tab === t ? "#f7931a" : "#888",
            border: "none", borderBottom: tab === t ? "2px solid #f7931a" : "2px solid transparent",
            padding: "12px 24px", cursor: "pointer", fontSize: 13, fontFamily: "monospace", textTransform: "uppercase"
          }}>{t}</button>
        ))}
      </div>

      <div style={{ padding: "32px", maxWidth: 900, margin: "0 auto" }}>

        {/* BOOK TAB */}
        {tab === "book" && (
          <div>
            <div style={{ marginBottom: 24 }}>
              <div style={{ color: "#f7931a", fontSize: 13, marginBottom: 6 }}>TEACHER NAME</div>
              <input value={teacher} onChange={e => setTeacher(e.target.value)}
                style={{ width: "100%", background: "#111", border: "1px solid #333", color: "#e0e0e0", padding: "10px 14px", fontFamily: "monospace", fontSize: 14, borderRadius: 4 }} />
            </div>

            <div style={{ marginBottom: 24 }}>
              <div style={{ color: "#f7931a", fontSize: 13, marginBottom: 6 }}>BOOKING REQUEST (natural language)</div>
              <textarea value={request} onChange={e => setRequest(e.target.value)}
                placeholder='e.g. "Book Lab-A tomorrow at 2pm for 2 hours for my OS lab class"'
                rows={4} style={{ width: "100%", background: "#111", border: "1px solid #333", color: "#e0e0e0", padding: "10px 14px", fontFamily: "monospace", fontSize: 14, borderRadius: 4, resize: "vertical" }} />
            </div>

            <button onClick={handleBook} disabled={loading}
              style={{ background: loading ? "#333" : "#f7931a", color: "#000", border: "none", padding: "12px 32px", fontFamily: "monospace", fontSize: 14, fontWeight: "bold", cursor: loading ? "not-allowed" : "pointer", borderRadius: 4 }}>
              {loading ? "⏳ Processing..." : "🚀 Submit Booking Request"}
            </button>

            {/* Agent Flow Visualization */}
            {loading && (
              <div style={{ marginTop: 24, background: "#111", border: "1px solid #222", borderRadius: 6, padding: 20 }}>
                <div style={{ color: "#f7931a", marginBottom: 12, fontSize: 13 }}>AGENT PIPELINE</div>
                {["Teacher Agent → Parsing natural language...", "Lab Agent → Checking availability...", "Blockchain → Logging to CS-Coin..."].map((s, i) => (
                  <div key={i} style={{ color: "#888", fontSize: 12, marginBottom: 6 }}>⚙ {s}</div>
                ))}
              </div>
            )}

            {/* Conflict Resolution */}
            {conflict && (
              <div style={{ marginTop: 24, background: "#1a1100", border: "1px solid #f7931a", borderRadius: 6, padding: 20 }}>
                <div style={{ color: "#f7931a", fontWeight: "bold", marginBottom: 8 }}>⚠ BOOKING CONFLICT</div>
                <div style={{ color: "#ccc", fontSize: 13, marginBottom: 16 }}>{conflict.message}</div>
                {conflict.alternate_start && (
                  <div>
                    <div style={{ color: "#aaa", fontSize: 12, marginBottom: 12 }}>
                      Suggested alternate: <strong style={{ color: "#4caf50" }}>{conflict.alternate_start} – {conflict.alternate_end}</strong> on {conflict.date}
                    </div>
                    <button onClick={handleAcceptAlternate} style={{ background: "#4caf50", color: "#000", border: "none", padding: "10px 24px", fontFamily: "monospace", fontSize: 13, fontWeight: "bold", cursor: "pointer", borderRadius: 4, marginRight: 12 }}>
                      ✓ Accept Alternate Time
                    </button>
                    <button onClick={() => setConflict(null)} style={{ background: "#333", color: "#e0e0e0", border: "none", padding: "10px 24px", fontFamily: "monospace", fontSize: 13, cursor: "pointer", borderRadius: 4 }}>
                      ✗ Cancel
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Success Result */}
            {result && result.status === "confirmed" && (
              <div style={{ marginTop: 24, background: "#0a1a0a", border: "1px solid #4caf50", borderRadius: 6, padding: 20 }}>
                <div style={{ color: "#4caf50", fontWeight: "bold", marginBottom: 8 }}>✓ BOOKING CONFIRMED</div>
                <div style={{ color: "#ccc", fontSize: 13, marginBottom: 16 }}>{result.message}</div>
                <div style={{ background: "#111", borderRadius: 4, padding: 12, fontSize: 12 }}>
                  <div style={{ color: "#888", marginBottom: 4 }}>BLOCKCHAIN PROOF</div>
                  <div style={{ color: "#f7931a", wordBreak: "break-all" }}>TX: {result.tx_id}</div>
                  <div style={{ color: "#aaa", marginTop: 4 }}>Booking ID: #{result.booking_id}</div>
                </div>
              </div>
            )}

            {result && result.status === "error" && (
              <div style={{ marginTop: 24, background: "#1a0a0a", border: "1px solid #f44336", borderRadius: 6, padding: 20 }}>
                <div style={{ color: "#f44336" }}>✗ ERROR: {result.message}</div>
              </div>
            )}
          </div>
        )}

        {/* BOOKINGS TAB */}
        {tab === "bookings" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <div style={{ color: "#f7931a", fontSize: 16, fontWeight: "bold" }}>ALL BOOKINGS</div>
              <button onClick={fetchBookings} style={{ background: "#222", color: "#aaa", border: "1px solid #333", padding: "6px 16px", fontFamily: "monospace", fontSize: 12, cursor: "pointer", borderRadius: 4 }}>↻ Refresh</button>
            </div>
            {bookings.length === 0 ? (
              <div style={{ color: "#555", textAlign: "center", padding: 40 }}>No bookings yet</div>
            ) : (
              bookings.map(b => (
                <div key={b.id} style={{ background: "#111", border: "1px solid #222", borderRadius: 6, padding: 16, marginBottom: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                    <span style={{ color: "#f7931a", fontWeight: "bold" }}>{b.lab}</span>
                    <span style={{ color: "#4caf50", fontSize: 12 }}>#{b.id}</span>
                  </div>
                  <div style={{ fontSize: 13, color: "#ccc", marginBottom: 4 }}>👤 {b.teacher} · 📅 {b.date} · ⏰ {b.start_time}–{b.end_time}</div>
                  <div style={{ fontSize: 12, color: "#888", marginBottom: 8 }}>📋 {b.purpose}</div>
                  {b.tx_id && b.tx_id !== "blockchain-unavailable" && (
                    <div style={{ fontSize: 11, color: "#f7931a", wordBreak: "break-all" }}>⛓ TX: {b.tx_id}</div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* BLOCKCHAIN TAB */}
        {tab === "blockchain" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <div style={{ color: "#f7931a", fontSize: 16, fontWeight: "bold" }}>CS-COIN BLOCKCHAIN</div>
              <button onClick={fetchChainInfo} style={{ background: "#222", color: "#aaa", border: "1px solid #333", padding: "6px 16px", fontFamily: "monospace", fontSize: 12, cursor: "pointer", borderRadius: 4 }}>↻ Refresh</button>
            </div>
            {chainInfo && (
              <div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 24 }}>
                  {[
                    { label: "BLOCKS", value: chainInfo.info?.blocks },
                    { label: "BALANCE", value: `${chainInfo.balance?.toFixed(4)} CSC` },
                    { label: "DIFFICULTY", value: chainInfo.info?.difficulty?.toExponential(2) },
                    { label: "CHAIN", value: chainInfo.info?.chain?.toUpperCase() },
                    { label: "HASH ALGO", value: "SHA-3" },
                    { label: "NONCE", value: "64-bit" },
                  ].map(({ label, value }) => (
                    <div key={label} style={{ background: "#111", border: "1px solid #222", borderRadius: 6, padding: 16, textAlign: "center" }}>
                      <div style={{ color: "#555", fontSize: 11, marginBottom: 6 }}>{label}</div>
                      <div style={{ color: "#f7931a", fontSize: 16, fontWeight: "bold" }}>{value}</div>
                    </div>
                  ))}
                </div>
                <div style={{ background: "#111", border: "1px solid #222", borderRadius: 6, padding: 16 }}>
                  <div style={{ color: "#888", fontSize: 11, marginBottom: 8 }}>BEST BLOCK HASH</div>
                  <div style={{ color: "#4caf50", fontSize: 12, wordBreak: "break-all" }}>{chainInfo.info?.bestblockhash}</div>
                </div>
                <div style={{ marginTop: 16, background: "#111", border: "1px solid #222", borderRadius: 6, padding: 16 }}>
                  <div style={{ color: "#888", fontSize: 11, marginBottom: 12 }}>CS-COIN MODIFICATIONS</div>
                  {[
                    ["Hash Algorithm", "SHA-256d → SHA-3 (Keccak-256)"],
                    ["Nonce Size", "32-bit → 64-bit"],
                    ["Block Time", "10 min → 1 min"],
                    ["Halving Interval", "210,000 → 105,000 blocks"],
                    ["Genesis Reward", "50 BTC → 100 CSC"],
                    ["Network Port", "8333 → 9333"],
                    ["Magic Bytes", "0xF9BEB4D9 → 0xC5C01001"],
                  ].map(([k, v]) => (
                    <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 8, paddingBottom: 8, borderBottom: "1px solid #1a1a1a" }}>
                      <span style={{ color: "#888" }}>{k}</span>
                      <span style={{ color: "#e0e0e0" }}>{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
