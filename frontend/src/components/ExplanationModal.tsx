import { useEffect, useRef } from "react";
import type { RecommendationItem } from "@/types";
import "@/components/ExplanationModal.css";

interface ExplanationModalProps {
  item: RecommendationItem;
  onClose: () => void;
}

export function ExplanationModal({ item, onClose }: ExplanationModalProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    closeButtonRef.current?.focus();
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onClose]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="explanation-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <span className="eyebrow">Why this recommendation</span>
          <button ref={closeButtonRef} className="btn-ghost" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <h3 id="explanation-title">{item.track.name}</h3>
        <p className="modal-artist">{item.track.artist_names.join(", ")}</p>

        <p className="modal-explanation">{item.explanation}</p>

        <div className="modal-confidence mono">
          Confidence score: {Math.round(item.confidence_score * 100)}%
        </div>
      </div>
    </div>
  );
}
