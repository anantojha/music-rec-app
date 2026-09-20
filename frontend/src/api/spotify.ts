import { apiRequest } from "@/api/client";
import type { LinkedAccount, Playlist, PlaylistDetail } from "@/types";

export async function getSpotifyAuthorizationUrl(): Promise<string> {
  const { authorization_url } = await apiRequest<{ authorization_url: string }>("/spotify/connect");
  return authorization_url;
}

export function getLinkedAccounts(): Promise<LinkedAccount[]> {
  return apiRequest<LinkedAccount[]>("/users/me/linked-accounts");
}

export function getPlaylists(): Promise<Playlist[]> {
  return apiRequest<Playlist[]>("/spotify/playlists");
}

export function getPlaylistDetail(playlistId: string): Promise<PlaylistDetail> {
  return apiRequest<PlaylistDetail>(`/spotify/playlists/${playlistId}`);
}
