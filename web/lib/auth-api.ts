import { apiRequest } from "./api";

const ACCESS_TOKEN_KEY = "rag_platform_access_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
}

export type AuthWorkspace = {
  id: string;
  name: string;
  role: string;
};

export type AuthUser = {
  id: string;
  email: string;
  display_name: string | null;
  workspaces: AuthWorkspace[];
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
  default_workspace_id: string | null;
};

export async function registerUser(input: {
  email: string;
  password: string;
  display_name?: string;
  workspace_name?: string;
}): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/auth/register", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });
}

export async function loginUser(input: {
  email: string;
  password: string;
}): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });
}

export async function getMe(): Promise<AuthUser> {
  return apiRequest<AuthUser>("/auth/me");
}
