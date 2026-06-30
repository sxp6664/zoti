import { useState, useEffect } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function CheckIn() {
  const [step, setStep] = useState("lookup");
  const [lastName, setLastName] = useState("");
  const [code, setCode] = useState("");
  const [reservation, setReservation] = useState(null);
  const [rooms, setRooms] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function call(path, body, method = "POST") {
    setError("");
    const res = await fetch(`${API}${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const e = await res.json().catch(() => ({}));
      throw new Error(e.detail || `Error ${res.status}`);
    }
    return res.json();
  }

  async function doLookup() {
    setBusy(true);
    try {
      const r = await call("/checkin/lookup", {
        last_name: lastName,
        confirmation_code: code || null,
      });
      setReservation(r);
      const list = await call("/checkin/available-rooms", null, "GET");
      setRooms(list);
      setStep("room");
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }

  async function scanId(file) {
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(`${API}/checkin/scan-id`, { method: "POST", body: fd });
      const data = await res.json();
      setLastName(data.extracted.last_name || "");
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }

  async function pickRoom(roomId) {
    setBusy(true);
    try {
      let r = await call("/checkin/select-room", {
        reservation_id: reservation.id, room_id: roomId,
      });
      r = await call("/checkin/pay", { reservation_id: r.id });
      r = await call("/checkin/complete", { reservation_id: r.id });
      setReservation(r);
      setStep("done");
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }

  return (
    <div style={styles.wrap}>
      <h1 style={styles.h1}>Zoti — Self Check-In</h1>
      {error && <div style={styles.err}>{error}</div>}

      {step === "lookup" && (
        <div style={styles.card}>
          <p style={styles.lead}>Find your reservation</p>
          <input style={styles.input} placeholder="Last name"
                 value={lastName} onChange={e => setLastName(e.target.value)} />
          <input style={styles.input} placeholder="Confirmation code (optional)"
                 value={code} onChange={e => setCode(e.target.value)} />
          <button style={styles.btn} disabled={busy || !lastName} onClick={doLookup}>
            {busy ? "Searching…" : "Find reservation"}
          </button>
          <div style={styles.or}>or scan your ID</div>
          <input type="file" accept="image/*"
                 onChange={e => e.target.files[0] && scanId(e.target.files[0])} />
        </div>
      )}

      {step === "room" && (
        <div style={styles.card}>
          <p style={styles.lead}>Welcome, {reservation.guest_full_name}</p>
          <p style={styles.sub}>Select your room ({reservation.nights} night(s))</p>
          <div style={styles.rooms}>
            {rooms.map(r => (
              <button key={r.id} style={styles.room}
                      disabled={busy} onClick={() => pickRoom(r.id)}>
                <strong>Room {r.number}</strong>
                <span>{r.room_type} · floor {r.floor}</span>
                <span>${r.price_per_night}/night</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {step === "done" && (
        <div style={styles.card}>
          <p style={styles.lead}>You're checked in ✓</p>
          <p style={styles.sub}>Your digital room key</p>
          <div style={styles.key}>{reservation.key_code}</div>
          <p style={styles.sub}>Room {reservation.room_id} · enjoy your stay</p>
        </div>
      )}
    </div>
  );
}

const styles = {
  wrap: { maxWidth: 480, margin: "40px auto", fontFamily: "system-ui, Arial" },
  h1: { fontSize: 22, fontWeight: 600 },
  card: { background: "#fff", border: "1px solid #e3e3e3", borderRadius: 12, padding: 24, marginTop: 16 },
  lead: { fontSize: 18, fontWeight: 600, margin: "0 0 12px" },
  sub: { color: "#666", margin: "4px 0 12px" },
  input: { width: "100%", padding: 10, marginBottom: 10, borderRadius: 8, border: "1px solid #ccc", boxSizing: "border-box" },
  btn: { width: "100%", padding: 12, borderRadius: 8, border: "none", background: "#1f3864", color: "#fff", fontSize: 15, cursor: "pointer" },
  or: { textAlign: "center", color: "#999", margin: "14px 0 8px" },
  rooms: { display: "grid", gap: 10 },
  room: { display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 2, padding: 12, borderRadius: 8, border: "1px solid #ccc", background: "#fafafa", cursor: "pointer", textAlign: "left" },
  key: { fontSize: 32, fontWeight: 700, letterSpacing: 4, textAlign: "center", padding: 16, background: "#f1f5fb", borderRadius: 10, color: "#1f3864" },
  err: { background: "#fdeaea", color: "#a32d2d", padding: 10, borderRadius: 8, marginTop: 12 },
};
