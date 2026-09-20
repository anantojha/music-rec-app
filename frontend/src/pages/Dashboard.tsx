import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AccountCard } from "@/components/AccountCard";
import { PlaylistSelector } from "@/components/PlaylistSelector";
import { GenerateButton } from "@/components/GenerateButton";
import { Waveform } from "@/components/Waveform";
import { getLinkedAccounts, getPlaylists, getSpotifyAuthorizationUrl } from "@/api/spotify";
import { generateRecommendations } from "@/api/recommendations";
import { ApiRequestError } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import type { Playlist } from "@/types";
import "@/pages/Dashboard.css";

export function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [isLoadingPlaylists, setIsLoadingPlaylists] = useState(false);
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getLinkedAccounts()
      .then((accounts) => {
        const connected = accounts.some((a) => a.provider === "spotify");
        setIsConnected(connected);
        if (connected) loadPlaylists();
      })
      .catch(() => setIsConnected(false));
  }, []);

  async function loadPlaylists() {
    setIsLoadingPlaylists(true);
    try {
      const data = await getPlaylists();
      setPlaylists(data);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not load playlists.");
    } finally {
      setIsLoadingPlaylists(false);
    }
  }

  async function handleConnect() {
    setIsConnecting(true);
    try {
      const url = await getSpotifyAuthorizationUrl();
      window.location.href = url;
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : "Could not start Spotify connection.");
      setIsConnecting(false);
    }
  }

  async function handleGenerate() {
    if (!selectedPlaylistId) return;
    setIsGenerating(true);
    setError(null);
    try {
      const result = await generateRecommendations(selectedPlaylistId);
      navigate("/recommendations", { state: { recommendation: result } });
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.message
          : "Recommendation generation failed. Try a different playlist."
      );
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="container dashboard">
      <header className="dashboard-header">
        <span className="eyebrow">Deck</span>
        <h1>Welcome back, {user?.display_name.split(" ")[0]}.</h1>
        <p>Pick a playlist and we'll build a taste profile, then hand it to GPT to find your next ten songs.</p>
      </header>

      <AccountCard isConnected={!!isConnected} onConnect={handleConnect} isConnecting={isConnecting} />

      {isConnected && (
        <section className="dashboard-section">
          <span className="eyebrow">Select a playlist</span>
          {isLoadingPlaylists ? (
            <Waveform label="Loading playlists" />
          ) : (
            <PlaylistSelector
              playlists={playlists}
              selectedId={selectedPlaylistId}
              onSelect={setSelectedPlaylistId}
            />
          )}
        </section>
      )}

      {error && (
        <p className="dashboard-error" role="alert">
          {error}
        </p>
      )}

      {isConnected && playlists.length > 0 && (
        <div className="dashboard-generate">
          <GenerateButton
            onGenerate={handleGenerate}
            isGenerating={isGenerating}
            disabled={!selectedPlaylistId || isGenerating}
          />
        </div>
      )}
    </div>
  );
}
