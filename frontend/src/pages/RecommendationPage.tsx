import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { SongCard } from "@/components/SongCard";
import { ExplanationModal } from "@/components/ExplanationModal";
import { SaveButton } from "@/components/SaveButton";
import { submitFeedback } from "@/api/recommendations";
import type { RecommendationHistoryEntry, RecommendationItem } from "@/types";
import "@/pages/RecommendationPage.css";

interface LocationState {
  recommendation?: RecommendationHistoryEntry;
}

export function RecommendationPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as LocationState | null;

  const [recommendation, setRecommendation] = useState<RecommendationHistoryEntry | undefined>(
    state?.recommendation
  );
  const [activeItem, setActiveItem] = useState<RecommendationItem | null>(null);

  if (!recommendation) {
    return (
      <div className="container">
        <p>
          No recommendation loaded. Head back to the <Link to="/dashboard">deck</Link> to generate one.
        </p>
      </div>
    );
  }

  async function handleLike(itemId: string, liked: boolean) {
    if (!recommendation) return;
    setRecommendation({
      ...recommendation,
      items: recommendation.items.map((i) => (i.track_id === itemId ? { ...i, liked } : i)),
    });
    try {
      await submitFeedback(recommendation.id, itemId, liked);
    } catch {
      // Feedback is a nice-to-have; a failed PATCH shouldn't block the reading experience.
    }
  }

  return (
    <div className="container recommendation-page">
      <header className="recommendation-header">
        <span className="eyebrow">Results</span>
        <h1>Your next ten songs.</h1>
        <div className="recommendation-profile">
          <span className="mono">Mood: {recommendation.taste_profile.mood.join(", ") || "—"}</span>
          <span className="mono">Energy: {recommendation.taste_profile.energy}</span>
          <span className="mono">Genres: {recommendation.taste_profile.genres.join(", ") || "—"}</span>
        </div>
      </header>

      <div className="recommendation-list">
        {recommendation.items.map((item) => (
          <SongCard
            key={item.track_id}
            item={item}
            onExplain={() => setActiveItem(item)}
            onLike={(liked) => handleLike(item.track_id, liked)}
          />
        ))}
      </div>

      <div className="recommendation-footer">
        <SaveButton isSaved />
        <button className="btn btn-secondary" onClick={() => navigate("/dashboard")}>
          Try another playlist
        </button>
      </div>

      {activeItem && <ExplanationModal item={activeItem} onClose={() => setActiveItem(null)} />}
    </div>
  );
}
