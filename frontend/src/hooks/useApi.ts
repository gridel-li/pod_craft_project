"use client";

/**
 * Helper that builds auth headers from localStorage token.
 * Used by dashboard components that still need raw fetch (e.g. pollTask, handleGenerate with 401 check).
 */
export function authHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}
