export interface User {
  id: string;
  email: string;
  display_name: string;
}

export interface LinkedAccount {
  provider: "spotify" | "apple_music";
  provider_user_id: string;
}

export interface Playlist {
  id: string;
  name: string;
  provider: string;
  provider_playlist_id: string;
}

export interface Track {
  id: string;
  name: string;
  artist_names: string[];
  provider_track_id: string;
}

export interface PlaylistDetail extends Playlist {
  tracks: Track[];
}

export type EnergyLevel = "low" | "medium" | "high";

export interface TasteProfile {
  genres: string[];
  mood: string[];
  energy: EnergyLevel;
  eras: string[];
  recommended_search_terms: string[];
}

export interface RecommendationItem {
  track_id: string;
  rank: number;
  confidence_score: number;
  explanation: string;
  liked: boolean | null;
  track: Track;
}

export interface RecommendationHistoryEntry {
  id: string;
  source_playlist_id: string;
  taste_profile: TasteProfile;
  created_at: string;
  items: RecommendationItem[];
}

export interface ApiError {
  detail: string;
}
