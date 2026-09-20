import type { RecommendationItem } from "@/types";
import "@/components/SongCard.css";

interface SongCardProps {
  item: RecommendationItem;
  onExplain: () => void;
  onLike: (liked: boolean) => void;
}

export function SongCard({ item, onExplain, onLike }: SongCardProps) {
  const confidencePercent = Math.round(item.confidence_score * 100);

  return (
    <div className="card song-card">
      <span className="song-card-rank mono">{String(item.rank).padStart(2, "0")}</span>

      <div className="song-card-body">
        <h4 className="song-card-title">{item.track.name}</h4>
        <p className="song-card-artist">{item.track.artist_names.join(", ")}</p>

        <div className="song-card-meter">
          <div className="song-card-meter-track">
            <div className="song-card-meter-fill" style={{ width: `${confidencePercent}%` }} />
          </div>
          <span className="mono song-card-meter-label">{confidencePercent}% match</span>
        </div>
      </div>

      <div className="song-card-actions">
        <button className="btn-ghost song-card-why" onClick={onExplain}>
          Why this?
        </button>
        <div className="song-card-feedback">
          <button
            aria-label="Like this recommendation"
            className={`song-card-feedback-btn${item.liked === true ? " song-card-feedback-active-like" : ""}`}
            onClick={() => onLike(true)}
          >
            ▲
          </button>
          <button
            aria-label="Dislike this recommendation"
            className={`song-card-feedback-btn${item.liked === false ? " song-card-feedback-active-dislike" : ""}`}
            onClick={() => onLike(false)}
          >
            ▼
          </button>
        </div>
      </div>
    </div>
  );
}
