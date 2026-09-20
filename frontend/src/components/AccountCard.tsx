import "@/components/AccountCard.css";

interface AccountCardProps {
  isConnected: boolean;
  onConnect: () => void;
  isConnecting: boolean;
}

export function AccountCard({ isConnected, onConnect, isConnecting }: AccountCardProps) {
  return (
    <div className="card account-card">
      <div>
        <span className="eyebrow">Source</span>
        <h3>Spotify</h3>
        <p>
          {isConnected
            ? "Your library is linked. Pick a playlist below to analyze."
            : "Connect your account so we can read your playlists and audio features."}
        </p>
      </div>

      <div className={`account-status ${isConnected ? "account-status-on" : "account-status-off"}`}>
        <span className="account-status-dot" aria-hidden="true" />
        {isConnected ? "Connected" : "Not connected"}
      </div>

      {!isConnected && (
        <button className="btn btn-primary" onClick={onConnect} disabled={isConnecting}>
          {isConnecting ? "Redirecting…" : "Connect Spotify"}
        </button>
      )}
    </div>
  );
}
