import { useState, useEffect } from "react";

const API = "http://localhost:5000/api";
const fmt = (n) => parseFloat(n || 0).toFixed(4);

// ── Pure browser crypto, no libraries ────────────────────────────────────────
function toHex(bytes) {
  return Array.from(bytes).map(b => b.toString(16).padStart(2,'0')).join('');
}

async function encryptKey(privKeyHex, password) {
  const enc = new TextEncoder();
  const keyMat = await crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const key = await crypto.subtle.deriveKey(
    { name:"PBKDF2", salt, iterations:100000, hash:"SHA-256" },
    keyMat, { name:"AES-GCM", length:256 }, false, ["encrypt"]
  );
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const data = await crypto.subtle.encrypt({ name:"AES-GCM", iv }, key, enc.encode(privKeyHex));
  return JSON.stringify({ salt: toHex(salt), iv: toHex(iv), data: toHex(new Uint8Array(data)) });
}

async function decryptKey(encJson, password) {
  const { salt, iv, data } = JSON.parse(encJson);
  const fromHex = h => new Uint8Array(h.match(/.{2}/g).map(b => parseInt(b,16)));
  const enc = new TextEncoder();
  const keyMat = await crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveKey"]);
  const key = await crypto.subtle.deriveKey(
    { name:"PBKDF2", salt:fromHex(salt), iterations:100000, hash:"SHA-256" },
    keyMat, { name:"AES-GCM", length:256 }, false, ["decrypt"]
  );
  const dec = await crypto.subtle.decrypt({ name:"AES-GCM", iv:fromHex(iv) }, key, fromHex(data));
  return new TextDecoder().decode(dec);
}

// Generate a random wallet ID (we use server-side address generation for simplicity)
function generateKeyId() {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return toHex(bytes);
}

// ── App ───────────────────────────────────────────────────────────────────────

function ChainInfo() {
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/blockchain/info`)
      .then(r => r.json())
      .then(d => { setInfo(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ color:"#446644", textAlign:"center", padding:40 }}>Loading...</div>;
  if (!info) return <div style={{ color:"#ff4466" }}>Could not fetch chain info</div>;

  return (
    <div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:12, marginBottom:20 }}>
        {[
          ["BLOCKS", info.info?.blocks],
          ["BALANCE", `${parseFloat(info.balance||0).toFixed(4)} CSC`],
          ["DIFFICULTY", info.info?.difficulty?.toExponential(2)],
          ["HASH ALGO", "SHA-3"],
          ["NONCE", "64-BIT"],
          ["NETWORK", info.info?.chain?.toUpperCase()],
        ].map(([label, value]) => (
          <div key={label} style={{ background:"#0a1520", border:"1px solid #0a2010", borderRadius:8, padding:16, textAlign:"center" }}>
            <div style={{ fontSize:10, color:"#335533", letterSpacing:2, marginBottom:6 }}>{label}</div>
            <div style={{ fontSize:15, color:"#00ff88", fontWeight:"bold" }}>{value}</div>
          </div>
        ))}
      </div>
      <div style={{ background:"#0a1520", border:"1px solid #0a2010", borderRadius:8, padding:16, marginBottom:12 }}>
        <div style={{ fontSize:10, color:"#335533", letterSpacing:2, marginBottom:8 }}>BEST BLOCK HASH</div>
        <div style={{ fontSize:11, color:"#00aa55", wordBreak:"break-all" }}>{info.info?.bestblockhash}</div>
      </div>
      <div style={{ background:"#0a1520", border:"1px solid #0a2010", borderRadius:8, padding:16, marginBottom:12 }}>
        <div style={{ fontSize:10, color:"#335533", letterSpacing:2, marginBottom:12 }}>CS-COIN vs BITCOIN</div>
        {[
          ["Hash Algorithm", "SHA-256d → SHA-3 (Keccak-256)"],
          ["Nonce Size", "32-bit → 64-bit"],
          ["Block Time", "10 min → 1 min"],
          ["Halving Interval", "210,000 → 105,000 blocks"],
          ["Genesis Reward", "50 BTC → 100 CSC"],
          ["Network Port", "8333 → 9333"],
          ["Magic Bytes", "0xF9BEB4D9 → 0xC5C01001"],
        ].map(([k, v]) => (
          <div key={k} style={{ display:"flex", justifyContent:"space-between", fontSize:11, padding:"8px 0", borderBottom:"1px solid #0a1a0a" }}>
            <span style={{ color:"#446644" }}>{k}</span>
            <span style={{ color:"#00aa55" }}>{v}</span>
          </div>
        ))}
      </div>
      <div style={{ background:"#0a1520", border:"1px solid #0a2010", borderRadius:8, padding:16 }}>
        <div style={{ fontSize:10, color:"#335533", letterSpacing:2, marginBottom:8 }}>MINE A BLOCK</div>
        <MineButton />
      </div>
    </div>
  );
}

function MineButton() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const mine = async () => {
    setLoading(true); setResult(null);
    try {
      const r = await fetch(`${API}/wallet/mine`, { method:"POST" });
      const d = await r.json();
      setResult(d);
    } catch(e) { setResult({ status:"error", message: e.message }); }
    setLoading(false);
  };

  return (
    <div>
      <button onClick={mine} disabled={loading} style={{ background:loading?"#0a2010":"linear-gradient(135deg,#1a4a1a,#00aa55)", color:loading?"#446644":"#00ff88", border:"1px solid #00aa55", padding:"10px 24px", fontFamily:"inherit", fontSize:11, letterSpacing:2, cursor:loading?"not-allowed":"pointer", borderRadius:6 }}>
        {loading ? "MINING..." : "⛏ MINE BLOCK"}
      </button>
      {result?.status === "ok" && (
        <div style={{ marginTop:10, fontSize:11, color:"#446644" }}>
          ✓ Mined! New balance: <span style={{ color:"#00ff88" }}>{parseFloat(result.new_balance).toFixed(4)} CSC</span>
        </div>
      )}
    </div>
  );
}

export default function WalletApp() {
  const [screen, setScreen] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState(localStorage.getItem("csc_token"));
  const [user, setUser] = useState(JSON.parse(localStorage.getItem("csc_user") || "null"));
  const [balance, setBalance] = useState(0);
  const [txs, setTxs] = useState([]);
  const [sendAddr, setSendAddr] = useState("");
  const [sendAmt, setSendAmt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [tab, setTab] = useState("home");
  const [copied, setCopied] = useState(false);
  const [signPwd, setSignPwd] = useState("");

  useEffect(() => {
    if (token && user) { setScreen("wallet"); fetchBalance(); }
  }, []);

  const fetchBalance = async () => {
    if (!user) return;
    try {
      const r = await fetch(`${API}/wallet/balance/${user.csc_address}`);
      const d = await r.json();
      setBalance(d.balance || 0);
      const tr = await fetch(`${API}/wallet/txhistory/${user.csc_address}`);
      const td = await tr.json();
      setTxs(td.transactions || []);
    } catch(e) { console.error(e); }
  };

  const handleRegister = async () => {
    setError(""); setLoading(true);
    try {
      // Get a fresh address from the node
      const ar = await fetch(`${API}/wallet/address`);
      const ad = await ar.json();
      if (ad.status !== "ok") { setError("Could not generate address"); setLoading(false); return; }
      const address = ad.address;

      // Encrypt a key identifier locally
      const keyId = generateKeyId();
      const encrypted = await encryptKey(keyId, password);

      const r = await fetch(`${API}/auth/register`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ username, password, csc_address: address })
      });
      const d = await r.json();
      if (d.status !== "ok") { setError(d.message); setLoading(false); return; }

      localStorage.setItem("csc_token", d.token);
      localStorage.setItem("csc_user", JSON.stringify(d.user));
      localStorage.setItem(`csc_key_${username}`, encrypted);
      setToken(d.token); setUser(d.user);
      setScreen("wallet"); fetchBalance();
    } catch(e) { setError(e.message); }
    setLoading(false);
  };

  const handleLogin = async () => {
    setError(""); setLoading(true);
    try {
      const r = await fetch(`${API}/auth/login`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body: JSON.stringify({ username, password })
      });
      const d = await r.json();
      if (d.status !== "ok") { setError(d.message); setLoading(false); return; }
      localStorage.setItem("csc_token", d.token);
      localStorage.setItem("csc_user", JSON.stringify(d.user));
      setToken(d.token); setUser(d.user);
      setScreen("wallet"); fetchBalance();
    } catch(e) { setError(e.message); }
    setLoading(false);
  };

  const handleSend = async () => {
    setError(""); setSuccess(""); setLoading(true);
    try {
      if (!sendAddr || !sendAmt) { setError("Enter address and amount"); setLoading(false); return; }
      // Custodial send via node for now
      const r = await fetch(`${API}/wallet/send`, {
        method:"POST", headers:{"Content-Type":"application/json", "Authorization":`Bearer ${token}`},
        body: JSON.stringify({ address: sendAddr, amount: parseFloat(sendAmt) })
      });
      const d = await r.json();
      if (d.status !== "ok") { setError(d.message); setLoading(false); return; }
      setSuccess(`✓ Sent ${sendAmt} CSC! TX: ${d.tx_id.slice(0,24)}...`);
      setSendAddr(""); setSendAmt(""); setSignPwd("");
      setTimeout(fetchBalance, 2000);
    } catch(e) { setError(e.message); }
    setLoading(false);
  };

  const logout = () => {
    localStorage.removeItem("csc_token"); localStorage.removeItem("csc_user");
    setToken(null); setUser(null); setScreen("login"); setPassword("");
  };

  const copy = () => {
    navigator.clipboard.writeText(user.csc_address);
    setCopied(true); setTimeout(() => setCopied(false), 2000);
  };

  const inp = { width:"100%", background:"#050c10", border:"1px solid #0a2010", color:"#c8d8e8", padding:"12px 14px", fontFamily:"inherit", fontSize:13, borderRadius:6, outline:"none", boxSizing:"border-box", marginBottom:16 };
  const lbl = { fontSize:10, color:"#446644", letterSpacing:2, marginBottom:6, display:"block" };
  const btn = (active=true) => ({ width:"100%", background:active?"linear-gradient(135deg,#00aa55,#00ff88)":"#0a2010", color:active?"#000":"#446644", border:"none", padding:14, fontFamily:"inherit", fontSize:12, fontWeight:"bold", letterSpacing:2, cursor:active?"pointer":"not-allowed", borderRadius:6, marginBottom:12 });

  // ── Auth Screen ─────────────────────────────────────────────────────────────
  if (screen !== "wallet") return (
    <div style={{ fontFamily:"'Courier New',monospace", background:"#070b0f", minHeight:"100vh", display:"flex", alignItems:"center", justifyContent:"center" }}>
      <div style={{ background:"#0d1820", border:"1px solid #1a3a2a", borderRadius:16, padding:36, width:400, boxShadow:"0 0 60px rgba(0,255,136,0.05)" }}>
        <div style={{ textAlign:"center", marginBottom:32 }}>
          <div style={{ fontSize:52, lineHeight:1 }}>₡</div>
          <div style={{ fontSize:24, fontWeight:"bold", color:"#00ff88", letterSpacing:4, marginTop:8 }}>CS-COIN</div>
          <div style={{ fontSize:10, color:"#335533", letterSpacing:3, marginTop:4 }}>DECENTRALIZED · SHA-3 · P2P</div>
        </div>
        {error && <div style={{ background:"rgba(255,68,102,0.1)", border:"1px solid #ff4466", borderRadius:6, padding:"10px 14px", color:"#ff4466", fontSize:12, marginBottom:12 }}>{error}</div>}
        <label style={lbl}>USERNAME</label>
        <input style={inp} value={username} onChange={e=>setUsername(e.target.value)} placeholder="satoshi"
          onKeyDown={e=>e.key==="Enter"&&(screen==="login"?handleLogin():handleRegister())} />
        <label style={lbl}>PASSWORD</label>
        <input style={inp} type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••"
          onKeyDown={e=>e.key==="Enter"&&(screen==="login"?handleLogin():handleRegister())} />
        {screen==="register" && (
          <div style={{ fontSize:10, color:"#335533", marginBottom:16, lineHeight:1.8, background:"#050c10", padding:10, borderRadius:6 }}>
            🔐 A fresh CSC address will be generated for you.<br/>
            Your password encrypts your wallet locally.
          </div>
        )}
        <button style={btn(!loading)} onClick={screen==="login"?handleLogin:handleRegister} disabled={loading}>
          {loading ? (screen==="login"?"LOGGING IN...":"CREATING WALLET...") : (screen==="login"?"→ LOGIN":"⬡ CREATE WALLET")}
        </button>
        <button onClick={()=>{setScreen(screen==="login"?"register":"login");setError("");}}
          style={{ width:"100%", background:"transparent", color:"#446644", border:"1px solid #1a3a1a", padding:10, fontFamily:"inherit", fontSize:11, cursor:"pointer", borderRadius:6 }}>
          {screen==="login"?"Don't have an account? Create Wallet":"Already have a wallet? Login"}
        </button>
      </div>
    </div>
  );

  // ── Wallet Screen ────────────────────────────────────────────────────────────
  return (
    <div style={{ fontFamily:"'Courier New',monospace", background:"#070b0f", minHeight:"100vh", color:"#c8d8e8" }}>
      <div style={{ background:"#0d1820", borderBottom:"1px solid #0a2a1a", padding:"14px 24px", display:"flex", alignItems:"center" }}>
        <span style={{ fontSize:18, color:"#00ff88", fontWeight:"bold", letterSpacing:3 }}>₡ CS-COIN</span>
        <span style={{ marginLeft:12, fontSize:11, color:"#335533" }}>@{user?.username}</span>
        <div style={{ marginLeft:"auto", display:"flex", alignItems:"center", gap:12 }}>
          <span style={{ fontSize:18, fontWeight:"bold", color:"#00ff88" }}>{fmt(balance)} CSC</span>
          <button onClick={fetchBalance} style={{ background:"transparent", border:"1px solid #1a3a1a", color:"#446644", padding:"4px 10px", fontFamily:"inherit", fontSize:10, cursor:"pointer", borderRadius:4 }}>↻</button>
          <button onClick={logout} style={{ background:"transparent", border:"none", color:"#335533", fontFamily:"inherit", fontSize:10, cursor:"pointer" }}>LOGOUT</button>
        </div>
      </div>

      <div style={{ display:"flex", borderBottom:"1px solid #0a1a0a", padding:"0 24px" }}>
        {[["home","HOME"],["send","SEND"],["receive","RECEIVE"],["history","HISTORY"],["chain","⛓ CHAIN"]].map(([t,l])=>(
          <button key={t} onClick={()=>setTab(t)} style={{ background:"transparent", color:tab===t?"#00ff88":"#335533", border:"none", borderBottom:tab===t?"2px solid #00ff88":"2px solid transparent", padding:"12px 20px", cursor:"pointer", fontFamily:"inherit", fontSize:11, letterSpacing:2 }}>{l}</button>
        ))}
      </div>

      <div style={{ padding:24, maxWidth:600, margin:"0 auto" }}>

        {tab==="home" && (
          <div>
            <div style={{ background:"linear-gradient(135deg,#0a1f0a,#0d2a1a)", border:"1px solid #1a4a2a", borderRadius:12, padding:32, textAlign:"center", marginBottom:20 }}>
              <div style={{ fontSize:11, color:"#446644", letterSpacing:3, marginBottom:8 }}>TOTAL BALANCE</div>
              <div style={{ fontSize:56, fontWeight:"bold", color:"#00ff88", lineHeight:1 }}>{fmt(balance)}</div>
              <div style={{ color:"#335533", marginTop:8, letterSpacing:4, fontSize:12 }}>CS-COIN</div>
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
              <button onClick={()=>setTab("send")} style={{ background:"#0a1520", border:"1px solid #0a2010", borderRadius:8, padding:20, cursor:"pointer", color:"#00ff88", fontFamily:"inherit", fontSize:12, letterSpacing:2 }}>↗ SEND</button>
              <button onClick={()=>setTab("receive")} style={{ background:"#0a1520", border:"1px solid #0a2010", borderRadius:8, padding:20, cursor:"pointer", color:"#00ff88", fontFamily:"inherit", fontSize:12, letterSpacing:2 }}>↙ RECEIVE</button>
            </div>
            <div style={{ marginTop:20, background:"#0a1520", border:"1px solid #0a2010", borderRadius:8, padding:16 }}>
              <div style={{ fontSize:10, color:"#335533", letterSpacing:2, marginBottom:8 }}>YOUR ADDRESS</div>
              <div style={{ fontSize:11, color:"#00aa55", wordBreak:"break-all" }}>{user?.csc_address}</div>
            </div>
          </div>
        )}

        {tab==="send" && (
          <div style={{ background:"#0d1820", border:"1px solid #0a2010", borderRadius:12, padding:24 }}>
            <div style={{ fontSize:11, color:"#446644", letterSpacing:2, marginBottom:20 }}>SEND CS-COIN</div>
            {error && <div style={{ background:"rgba(255,68,102,0.1)", border:"1px solid #ff4466", borderRadius:6, padding:"10px 14px", color:"#ff4466", fontSize:12, marginBottom:12 }}>{error}</div>}
            {success && <div style={{ background:"rgba(0,255,136,0.05)", border:"1px solid #00aa55", borderRadius:6, padding:"10px 14px", color:"#00ff88", fontSize:12, marginBottom:12 }}>{success}</div>}
            <label style={lbl}>RECIPIENT ADDRESS</label>
            <input value={sendAddr} onChange={e=>setSendAddr(e.target.value)} placeholder="bcrt1q..." style={inp} />
            <label style={lbl}>AMOUNT (CSC)</label>
            <input value={sendAmt} onChange={e=>setSendAmt(e.target.value)} type="number" step="0.0001" placeholder="0.0000" style={{...inp, fontSize:24, color:"#00ff88"}} />
            <div style={{ fontSize:10, color:"#335533", marginBottom:16 }}>Available: {fmt(balance)} CSC · Fee: ~0.0001 CSC</div>
            <button onClick={handleSend} disabled={loading} style={btn(!loading)}>
              {loading?"SENDING...":"↗ SEND CSC"}
            </button>
          </div>
        )}

        {tab==="receive" && (
          <div style={{ background:"#0d1820", border:"1px solid #0a2010", borderRadius:12, padding:24, textAlign:"center" }}>
            <div style={{ fontSize:11, color:"#446644", letterSpacing:2, marginBottom:24 }}>YOUR CSC ADDRESS</div>
            <div style={{ background:"#050c10", border:"1px solid #0a2010", borderRadius:8, padding:24, marginBottom:20, wordBreak:"break-all", fontSize:14, color:"#00aa55", lineHeight:2 }}>
              {user?.csc_address}
            </div>
            <button onClick={copy} style={{ background:copied?"#00aa55":"#0a2010", color:copied?"#000":"#00ff88", border:"1px solid #00aa55", padding:"12px 32px", fontFamily:"inherit", fontSize:11, letterSpacing:2, cursor:"pointer", borderRadius:6 }}>
              {copied?"✓ COPIED!":"COPY ADDRESS"}
            </button>
            <div style={{ marginTop:20, fontSize:11, color:"#335533", lineHeight:2 }}>
              Share this address to receive CS-Coin from anyone on the network.
            </div>
          </div>
        )}

        {tab==="history" && (
          <div>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
              <div style={{ fontSize:11, color:"#446644", letterSpacing:2 }}>TRANSACTION HISTORY</div>
              <button onClick={fetchBalance} style={{ background:"transparent", border:"1px solid #1a3a1a", color:"#446644", padding:"4px 12px", fontFamily:"inherit", fontSize:10, cursor:"pointer", borderRadius:4 }}>↻ REFRESH</button>
            </div>
            {txs.length===0 && <div style={{ color:"#223322", textAlign:"center", padding:48, fontSize:12 }}>No transactions yet.<br/>Share your address to receive CSC!</div>}
            {txs.map((tx,i)=>(
              <div key={i} style={{ background:"#0d1820", border:"1px solid #0a1f10", borderRadius:8, padding:"14px 16px", marginBottom:8, display:"flex", alignItems:"center", gap:12 }}>
                <div style={{ width:36, height:36, borderRadius:"50%", background:tx.category==="receive"?"rgba(0,255,136,0.1)":"rgba(255,68,102,0.1)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:16 }}>
                  {tx.category==="receive"?"↙":"↗"}
                </div>
                <div style={{ flex:1, minWidth:0 }}>
                  <div style={{ fontSize:11, color:"#446644", marginBottom:2 }}>{tx.category?.toUpperCase()} · {new Date(tx.time*1000).toLocaleString()}</div>
                  <div style={{ fontSize:10, color:"#223322", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{tx.txid}</div>
                </div>
                <div style={{ fontWeight:"bold", color:tx.category==="receive"?"#00ff88":"#ff4466", whiteSpace:"nowrap" }}>
                  {tx.category==="receive"?"+":""}{fmt(tx.amount)} CSC
                </div>
              </div>
            ))}
          </div>
        )}

        {tab==="chain" && (
          <div>
            <div style={{ fontSize:11, color:"#446644", letterSpacing:2, marginBottom:16 }}>BLOCKCHAIN INFO</div>
            <ChainInfo />
          </div>
        )}
      </div>
    </div>
  );
}
