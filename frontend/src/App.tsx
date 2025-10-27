import { useEffect, useMemo, useState } from "react";

const API = import.meta.env.VITE_API_BASE || "http://localhost:8000";

type Daily = { date: string; temp_min_c: number; temp_max_c: number };
type Query = {
  id: number;
  raw_location: string;
  latitude: number;
  longitude: number;
  start_date?: string | null;
  end_date?: string | null;
  created_at: string;
  records: Daily[];
};

// NEW: add "stored" as a third view
type View = "current" | "forecast" | "stored" | null;

export default function App() {
  const [location, setLocation] = useState("Calgary");
  const [start, setStart] = useState<string>("");
  const [end, setEnd] = useState<string>("");
  const [current, setCurrent] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);
  const [queries, setQueries] = useState<Query[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string>("");

  // which result is being shown, and what was searched to produce it
  const [view, setView] = useState<View>(null);
  const [shownLocation, setShownLocation] = useState<string>("");

  // NEW: track which stored query is open
  const [selected, setSelected] = useState<Query | null>(null);

  const rangeValid = useMemo(() => {
    if (!start || !end) return true;
    return new Date(start) <= new Date(end);
  }, [start, end]);

  async function getCurrent() {
    setBusy(true);
    setMsg("");
    setView("current");
    setForecast(null);
    setSelected(null);                 // hide stored panel
    setShownLocation(location);
    try {
      const r = await fetch(`${API}/api/current?location=${encodeURIComponent(location)}`);
      if (!r.ok) throw new Error((await r.text()) || `Current request failed (${r.status})`);
      setCurrent(await r.json());
    } catch (e: any) {
      setCurrent(null);
      setMsg(e.message ?? "Failed to load current weather");
    } finally { setBusy(false); }
  }

  async function get5day() {
    setBusy(true);
    setMsg("");
    setView("forecast");
    setCurrent(null);
    setSelected(null);                 // hide stored panel
    setShownLocation(location);
    try {
      const r = await fetch(`${API}/api/forecast5?location=${encodeURIComponent(location)}`);
      if (!r.ok) throw new Error((await r.text()) || `Forecast request failed (${r.status})`);
      setForecast(await r.json());
    } catch (e: any) {
      setForecast(null);
      setMsg(e.message ?? "Failed to load forecast");
    } finally { setBusy(false); }
  }

  async function createQuery() {
    if (!rangeValid) { setMsg("Start must be before end"); return; }
    setBusy(true);
    try {
      const body: any = { location };
      if (start) body.start_date = start;
      if (end) body.end_date = end;
      const r = await fetch(`${API}/api/queries`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (!r.ok) throw new Error(await r.text());
      setMsg("Saved!");
      await loadQueries();
    } catch (e: any) {
      setMsg(e.message ?? "Failed");
    } finally { setBusy(false); }
  }

  async function loadQueries() {
    const r = await fetch(`${API}/api/queries`);
    setQueries(await r.json());
  }

  async function del(id: number) {
    // if deleting the one being viewed, close it
    if (selected?.id === id) { setSelected(null); setView(null); }
    await fetch(`${API}/api/queries/${id}`, { method: "DELETE" });
    await loadQueries();
  }

  function useMyLocation() {
    if (!navigator.geolocation) { setMsg("Geolocation not supported"); return; }
    navigator.geolocation.getCurrentPosition((pos) => {
      setLocation(`${pos.coords.latitude.toFixed(5)},${pos.coords.longitude.toFixed(5)}`);
    }, () => setMsg("Location permission denied"));
  }

  async function exportCSV() {
    const r = await fetch(`${API}/api/export?fmt=csv`);
    const data = await r.json();
    const blob = new Blob([data.csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "weather_export.csv"; a.click();
    URL.revokeObjectURL(url);
  }

  // NEW: open a stored query row
  function openStored(q: Query) {
    setSelected(q);
    setView("stored");
    setCurrent(null);
    setForecast(null);
    setMsg("");
  }

  useEffect(() => { loadQueries(); }, []);

  return (
    <div style={{ maxWidth: 900, margin: "2rem auto", padding: "1rem", fontFamily: "system-ui" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Weather Forecast</h1>
      </header>

      <section style={{ display: "grid", gap: 12, gridTemplateColumns: "2fr 1fr 1fr auto" }}>
        <input
          value={location}
          onChange={e => setLocation(e.target.value)}
          placeholder="City / postal / 'lat,lon'"
        />
        <input type="date" value={start} onChange={e => setStart(e.target.value)} />
        <input type="date" value={end} onChange={e => setEnd(e.target.value)} />
        <button onClick={useMyLocation}>📍 Use my location</button>
      </section>

      {!rangeValid && <p style={{ color: "crimson" }}>Start date must be before end date.</p>}
      {msg && <p style={{ color: "crimson" }}>{msg}</p>}

      <div style={{ display:"flex", gap:8, margin: "12px 0" }}>
        <button disabled={busy} onClick={getCurrent}>Current</button>
        <button disabled={busy} onClick={get5day}>5-day</button>
        <button disabled={busy} onClick={createQuery}>Save to DB (CRUD: Create)</button>
        <button onClick={exportCSV}>Export CSV</button>
      </div>

      {/* Only render the active live views */}
      {view === "current" && current && (
        <div style={{ padding: 12, border: "1px solid #ddd", borderRadius: 10, marginBottom: 12 }}>
          <h3 style={{ marginBottom: 6 }}>
            Current Weather{shownLocation ? ` — ${shownLocation}` : ""}
          </h3>
          <p>Temperature: {current.temperature_c} °C</p>
          {current.windspeed_kph != null && <p>Wind Speed: {current.windspeed_kph} km/h</p>}
          {current.winddirection_deg != null && <p>Wind Direction: {current.winddirection_deg}°</p>}
        </div>
      )}

      {view === "forecast" && forecast?.time && (
        <div style={{ padding: 12, border: "1px solid #ddd", borderRadius: 10, marginBottom: 12 }}>
          <h3 style={{ marginBottom: 6 }}>
            5-day Forecast{shownLocation ? ` — ${shownLocation}` : ""}
          </h3>
          <ul>
            {forecast.time.map((d: string, i: number) => (
              <li key={d}>
                {d}: {forecast.temperature_2m_min[i]}–{forecast.temperature_2m_max[i]} °C
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* NEW: stored query details */}
      {view === "stored" && selected && (
        <div style={{ padding: 12, border: "1px solid #ddd", borderRadius: 10, marginBottom: 12 }}>
          <h3 style={{ marginBottom: 6 }}>
            Stored Forecast — {selected.raw_location} ({selected.latitude.toFixed(3)},{selected.longitude.toFixed(3)})
          </h3>
          <p style={{ marginTop: 0, opacity: 0.8 }}>
            Range: {selected.start_date ?? "—"} → {selected.end_date ?? "—"} · {selected.records.length} day(s)
          </p>
          <ul>
            {selected.records.map((r) => (
              <li key={r.date}>{r.date}: {r.temp_min_c}–{r.temp_max_c} °C</li>
            ))}
          </ul>
          <div style={{ marginTop: 8 }}>
            <button onClick={() => { setSelected(null); setView(null); }}>Close</button>
          </div>
        </div>
      )}

      <h3>Saved Queries (CRUD: Read/Delete)</h3>
      <table style={{ width:"100%", borderCollapse: "collapse" }}>
        <thead>
          <tr><th align="left">#</th><th align="left">Location</th><th>Range</th><th>Days</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {queries.map(q => (
            <tr
              key={q.id}
              style={{ borderTop:"1px solid #eee", cursor: "pointer" }}
              onClick={() => openStored(q)}
              title="Click to view stored data"
            >
              <td>{q.id}</td>
              <td>{q.raw_location} ({q.latitude.toFixed(3)},{q.longitude.toFixed(3)})</td>
              <td>{q.start_date ?? "—"} → {q.end_date ?? "—"}</td>
              <td>{q.records.length}</td>
              <td>
                {/* stop row click when pressing Delete */}
                <button onClick={(e) => { e.stopPropagation(); del(q.id); }}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <footer style={{ marginTop: 24, opacity: 0.8 }}>
        <small>Built with React, FastAPI, Postgres, Docker.</small>
      </footer>
    </div>
  );
}
