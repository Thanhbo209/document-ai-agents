import { apiRequest } from "./api-client";

export { clearAccessToken, getAccessToken, setAccessToken } from "./auth-token";

export type AuthWorkspace = {
  id: string;
  name: string;
  role: string;
};

export type AuthUser = {
  id: string;
  email: string;
  display_name: string | null;
  is_platform_admin: boolean;
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
