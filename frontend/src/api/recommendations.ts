import { apiRequest } from "@/api/client";
import type { RecommendationHistoryEntry } from "@/types";

export function generateRecommendations(playlistId: string): Promise<RecommendationHistoryEntry> {
  return apiRequest<RecommendationHistoryEntry>("/recommendations/generate", {
    method: "POST",
    body: { playlist_id: playlistId },
  });
}

export function getRecommendationHistory(): Promise<RecommendationHistoryEntry[]> {
  return apiRequest<RecommendationHistoryEntry[]>("/recommendations/history");
}

export function deleteRecommendation(id: string): Promise<void> {
  return apiRequest<void>(`/recommendations/${id}`, { method: "DELETE" });
}

export function submitFeedback(
  recommendationId: string,
  itemId: string,
  liked: boolean
): Promise<void> {
  return apiRequest<void>(`/recommendations/${recommendationId}/items/${itemId}/feedback`, {
    method: "PATCH",
    body: { liked },
  });
}
