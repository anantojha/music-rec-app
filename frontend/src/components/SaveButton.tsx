import { Link } from "react-router-dom";

interface SaveButtonProps {
  isSaved: boolean;
}

/**
 * Recommendations are persisted server-side the moment /recommendations/generate
 * succeeds (see backend RecommendationRepository.create), so there's no separate
 * "save" network call here -- this communicates that fact and links to where the
 * saved run now lives, rather than asking the user to take a redundant action.
 */
export function SaveButton({ isSaved }: SaveButtonProps) {
  if (!isSaved) return null;

  return (
    <Link to="/history" className="btn btn-secondary">
      <span aria-hidden="true">✓</span> Saved to history
    </Link>
  );
}
