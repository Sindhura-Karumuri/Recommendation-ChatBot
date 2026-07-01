import { useState, useRef, useEffect } from "react";
import ChatMessage from "./components/ChatMessage.jsx";
import RecommendationCard from "./components/RecommendationCard.jsx";
import TypingIndicator from "./components/TypingIndicator.jsx";
import "./App.css";

const WELCOME = {
  role: "assistant",
  content:
    "Hi! I'm the SHL Assessment Recommender. Tell me about the role you're hiring for and I'll suggest the right assessments from the SHL catalog.",
  recommendations: [],
};

export default function App() {
  const [messages, setMessages] = useState([WELCOME]);
  const [history, setHistory] = useState([]); // API history (no welcome msg)
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [ended, setEnded] = useState(false);
  const [lastRecs, setLastRecs] = useState([]);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(text) {
    if (!text.trim() || loading || ended) return;

    const userMsg = { role: "user", content: text };
    const newHistory = [...history, userMsg];

    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setHistory(newHistory);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newHistory }),
      });

      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();

      const assistantMsg = {
        role: "assistant",
        content: data.reply,
        recommendations: data.recommendations || [],
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setHistory((prev) => [...prev, { role: "assistant", content: data.reply }]);

      if (data.recommendations?.length > 0) {
        setLastRecs(data.recommendations);
      }
      if (data.end_of_conversation) {
        setEnded(true);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Something went wrong: ${err.message}. Please try again.`,
          recommendations: [],
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  function reset() {
    setMessages([WELCOME]);
    setHistory([]);
    setInput("");
    setEnded(false);
    setLastRecs([]);
    inputRef.current?.focus();
  }

  const turnCount = history.filter((m) => m.role === "user").length;
  const showSidebar = lastRecs.length > 0;

  return (
    <div className={`layout ${showSidebar ? "with-sidebar" : ""}`}>
      {/* ── Header ── */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-icon">◈</span>
            <span className="logo-text">SHL Recommender</span>
          </div>
          {turnCount > 0 && (
            <span className="turn-badge">Turn {turnCount} / 8</span>
          )}
        </div>
        <button className="btn-ghost" onClick={reset} title="Start new conversation">
          ↺ New conversation
        </button>
      </header>

      {/* ── Chat pane ── */}
      <main className="chat-pane">
        <div className="messages">
          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}
          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {/* ── Input ── */}
        <div className="input-area">
          {ended ? (
            <div className="ended-banner">
              Conversation complete.{" "}
              <button className="link-btn" onClick={reset}>
                Start a new one
              </button>
            </div>
          ) : (
            <div className="input-row">
              <textarea
                ref={inputRef}
                className="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Describe the role you're hiring for…"
                rows={1}
                disabled={loading}
              />
              <button
                className="send-btn"
                onClick={() => sendMessage(input)}
                disabled={!input.trim() || loading}
                aria-label="Send message"
              >
                ↑
              </button>
            </div>
          )}
          <p className="input-hint">Enter to send · Shift+Enter for new line</p>
        </div>
      </main>

      {/* ── Recommendations sidebar ── */}
      {showSidebar && (
        <aside className="sidebar">
          <div className="sidebar-header">
            <span className="sidebar-title">Shortlisted Assessments</span>
            <span className="rec-count">{lastRecs.length}</span>
          </div>
          <div className="rec-list">
            {lastRecs.map((rec, i) => (
              <RecommendationCard key={i} rec={rec} index={i + 1} />
            ))}
          </div>
        </aside>
      )}
    </div>
  );
}
