import { useState } from "react";

const API_URL = "http://localhost:8000/api/chat";

export default function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  async function handleSend() {
    const text = input.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: data.reply,
          venue: data.venue,
          original: data.original_image_base64,
          composited: data.composited_image_base64,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: `Error contacting backend: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>AI Storefront Visualizer</h1>
      <p style={styles.subtitle}>
        Ask for a business type + location, e.g. "Find me an independent
        cafe in Soho to pitch our planters to".
      </p>

      <div style={styles.chatWindow}>
        {messages.map((m, i) => (
          <div
            key={i}
            style={m.role === "user" ? styles.userBubble : styles.botBubble}
          >
            <div>{m.text}</div>

            {m.role === "bot" && m.original && m.composited && (
              <div style={styles.imageRow}>
                <div>
                  <div style={styles.imageLabel}>Original</div>
                  <img
                    src={`data:image/jpeg;base64,${m.original}`}
                    alt="Original storefront"
                    style={styles.image}
                  />
                </div>
                <div>
                  <div style={styles.imageLabel}>With planter</div>
                  <img
                    src={`data:image/jpeg;base64,${m.composited}`}
                    alt="Composited mockup"
                    style={styles.image}
                  />
                </div>
              </div>
            )}

            {m.role === "bot" && m.venue && (
              <div style={styles.venueInfo}>
                {m.venue.name} — {m.venue.address}
              </div>
            )}
          </div>
        ))}
        {loading && <div style={styles.botBubble}>Working on it…</div>}
      </div>

      <div style={styles.inputRow}>
        <input
          style={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Type a request…"
        />
        <button style={styles.button} onClick={handleSend} disabled={loading}>
          Send
        </button>
      </div>
    </div>
  );
}

const styles = {
  page: {
    maxWidth: 720,
    margin: "0 auto",
    padding: "24px 16px",
    fontFamily: "system-ui, sans-serif",
  },
  title: { marginBottom: 4 },
  subtitle: { color: "#666", marginTop: 0, marginBottom: 20, fontSize: 14 },
  chatWindow: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
    minHeight: 300,
    marginBottom: 16,
  },
  userBubble: {
    alignSelf: "flex-end",
    background: "#2563eb",
    color: "white",
    padding: "10px 14px",
    borderRadius: 12,
    maxWidth: "80%",
  },
  botBubble: {
    alignSelf: "flex-start",
    background: "#f1f5f9",
    color: "#111",
    padding: "10px 14px",
    borderRadius: 12,
    maxWidth: "90%",
  },
  imageRow: { display: "flex", gap: 12, marginTop: 10 },
  imageLabel: { fontSize: 12, color: "#666", marginBottom: 4 },
  image: { width: 220, borderRadius: 8, display: "block" },
  venueInfo: { fontSize: 12, color: "#555", marginTop: 8 },
  inputRow: { display: "flex", gap: 8 },
  input: {
    flex: 1,
    padding: "10px 12px",
    borderRadius: 8,
    border: "1px solid #ccc",
    fontSize: 14,
  },
  button: {
    padding: "10px 18px",
    borderRadius: 8,
    border: "none",
    background: "#2563eb",
    color: "white",
    fontSize: 14,
    cursor: "pointer",
  },
};
