import { apiRequest } from "./client";
import type { TokenResponse, User } from "../types/auth";

export function register(email: string, password: string): Promise<User> {
  return apiRequest<User>("/api/auth/register", {
    method: "POST",
    body: { email, password },
  });
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/api/auth/login", {
    method: "POST",
    body: { email, password },
  });
}

export function getCurrentUser(): Promise<User> {
  return apiRequest<User>("/api/auth/me");
}
