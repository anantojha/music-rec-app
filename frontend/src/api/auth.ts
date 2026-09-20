import { apiRequest } from "@/api/client";
import type { User } from "@/types";

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: { email, password },
    auth: false,
  });
}

export function register(email: string, displayName: string, password: string): Promise<User> {
  return apiRequest<User>("/users", {
    method: "POST",
    body: { email, display_name: displayName, password },
    auth: false,
  });
}

export function getCurrentUser(): Promise<User> {
  return apiRequest<User>("/auth/me");
}

export function logout(): Promise<void> {
  return apiRequest<void>("/auth/logout", { method: "POST" });
}
