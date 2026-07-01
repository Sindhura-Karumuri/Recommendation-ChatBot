import "./TypingIndicator.css";

export default function TypingIndicator() {
  return (
    <div className="message-row agent" style={{ padding: "6px 20px", maxWidth: 820, margin: "0 auto", width: "100%" }}>
      <div className="avatar agent-avatar" aria-hidden="true">◈</div>
      <div className="typing-bubble" aria-label="Agent is typing">
        <span className="dot" />
        <span className="dot" />
        <span className="dot" />
      </div>
    </div>
  );
}
