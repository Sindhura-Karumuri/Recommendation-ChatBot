import "./RecommendationCard.css";

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

const TYPE_COLORS = {
  A: "#4f9ef7",
  B: "#f7a44f",
  C: "#7ef74f",
  D: "#c44ff7",
  E: "#4ff7e8",
  K: "#4f6ef7",
  P: "#f74f9e",
  S: "#f7d44f",
};

export default function RecommendationCard({ rec, index }) {
  const color = TYPE_COLORS[rec.test_type] || "#8b92b8";
  const label = TYPE_LABELS[rec.test_type] || rec.test_type;

  return (
    <a
      href={rec.url}
      target="_blank"
      rel="noopener noreferrer"
      className="rec-card"
      aria-label={`${rec.name} — ${label}`}
    >
      <div className="rec-index" style={{ color }}>{index}</div>
      <div className="rec-body">
        <div className="rec-name">{rec.name}</div>
        <div className="rec-meta">
          <span className="rec-type-badge" style={{ background: `${color}22`, color }}>
            {label}
          </span>
        </div>
      </div>
      <span className="rec-arrow">↗</span>
    </a>
  );
}
