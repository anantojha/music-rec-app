import type { Playlist } from "@/types";
import "@/components/PlaylistSelector.css";

interface PlaylistSelectorProps {
  playlists: Playlist[];
  selectedId: string | null;
  onSelect: (playlistId: string) => void;
}

export function PlaylistSelector({ playlists, selectedId, onSelect }: PlaylistSelectorProps) {
  if (playlists.length === 0) {
    return (
      <div className="card playlist-empty">
        <p>No playlists found yet. Once your Spotify account is connected, they'll show up here.</p>
      </div>
    );
  }

  return (
    <div className="playlist-grid" role="radiogroup" aria-label="Select a playlist">
      {playlists.map((playlist) => {
        const isSelected = playlist.id === selectedId;
        return (
          <button
            key={playlist.id}
            role="radio"
            aria-checked={isSelected}
            className={`playlist-tile${isSelected ? " playlist-tile-selected" : ""}`}
            onClick={() => onSelect(playlist.id)}
          >
            <span className="playlist-tile-index mono">
              {isSelected ? "●" : "○"}
            </span>
            <span className="playlist-tile-name">{playlist.name}</span>
          </button>
        );
      })}
    </div>
  );
}
