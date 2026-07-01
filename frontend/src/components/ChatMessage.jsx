import "./ChatMessage.css";

const TYPE_LABELS = {
  A: "Ability & Aptitude",
  B: "Biodata & SJT",
  C: "Competencies",
  D: "Development & 360",
  E: "Assessment Exercises",
  K: "Knowledge & Skills",
  P: "Personality & Behavior",
  S: "Simulations",
};

export default function ChatMessage({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`message-row ${isUser ? "user" : "agent"}`}>
      {!isUser && (
        <div className="avatar agent-avatar" aria-hidden="true">◈</div>
      )}
      <div className="bubble-wrap">
        <div className={`bubble ${isUser ? "user-bubble" : "agent-bubble"} ${message.isError ? "error-bubble" : ""}`}>
          {message.content}
        </div>

        {/* Inline recommendations (shown inside the message for smaller sets) */}
        {!isUser && message.recommendations?.length > 0 && (
          <div className="inline-recs">
            {message.recommendations.map((rec, i) => (
              <a
                key={i}
                href={rec.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-rec-chip"
              >
                <span className="chip-name">{rec.name}</span>
                <span className="chip-type" title={TYPE_LABELS[rec.test_type] || rec.test_type}>
                  {rec.test_type}
                </span>
              </a>
            ))}
          </div>
        )}
      </div>
      {isUser && (
        <div className="avatar user-avatar" aria-hidden="true">U</div>
      )}
    </div>
  );
}
