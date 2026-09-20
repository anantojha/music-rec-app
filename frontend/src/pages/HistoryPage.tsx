import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Waveform } from "@/components/Waveform";
import { deleteRecommendation, getRecommendationHistory } from "@/api/recommendations";
import type { RecommendationHistoryEntry } from "@/types";
import "@/pages/HistoryPage.css";

export function HistoryPage() {
  const navigate = useNavigate();
  const [history, setHistory] = useState<RecommendationHistoryEntry[] | null>(null);

  useEffect(() => {
    getRecommendationHistory().then(setHistory);
  }, []);

  async function handleDelete(id: string) {
    await deleteRecommendation(id);
    setHistory((prev) => prev?.filter((entry) => entry.id !== id) ?? null);
  }

  if (history === null) {
    return (
      <div className="container" style={{ paddingTop: "3rem" }}>
        <Waveform label="Loading history" />
      </div>
    );
  }

  return (
    <div className="container history-page">
      <header>
        <span className="eyebrow">Log</span>
        <h1>Recommendation history.</h1>
        <p>Every batch of songs GPT has generated for you, with the taste profile behind it.</p>
      </header>

      {history.length === 0 ? (
        <div className="card history-empty">
          <p>Nothing here yet. Generate your first batch of recommendations from the deck.</p>
        </div>
      ) : (
        <div className="history-list">
          {history.map((entry) => (
            <div key={entry.id} className="card history-entry">
              <button className="history-entry-main" onClick={() => navigate("/recommendations", { state: { recommendation: entry } })}>
                <div>
                  <span className="mono history-entry-date">
                    {new Date(entry.created_at).toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </span>
                  <p className="history-entry-summary">
                    {entry.items.length} songs · {entry.taste_profile.energy} energy ·{" "}
                    {entry.taste_profile.genres.slice(0, 3).join(", ") || "mixed genres"}
                  </p>
                </div>
              </button>
              <button
                className="btn-ghost history-entry-delete"
                onClick={() => handleDelete(entry.id)}
                aria-label="Delete this recommendation batch"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
