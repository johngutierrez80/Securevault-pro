import { afterEach, describe, expect, it, vi } from "vitest";
import {
  getCurrentUser,
  loginUser,
  registerUser,
  requestPasswordReset,
  resetPassword,
} from "./auth";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("auth api", () => {
  it("sends login requests with JSON credentials", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ access_token: "abc123" }),
    });

    const result = await loginUser("alice@example.com", "secret");

    expect(fetchMock).toHaveBeenCalledWith("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "alice@example.com", password: "secret" }),
    });
    expect(result).toEqual({ ok: true, status: 200, data: { access_token: "abc123" } });
  });

  it("sends registration requests with JSON credentials", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ message: "created" }),
    });

    const result = await registerUser("alice@example.com", "secret");

    expect(fetchMock).toHaveBeenCalledWith("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "alice@example.com", password: "secret" }),
    });
    expect(result).toEqual({ ok: true, status: 200, data: { message: "created" } });
  });

  it("sends password reset request with email payload", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ reset_token: "abc" }),
    });

    const result = await requestPasswordReset("alice@example.com");

    expect(fetchMock).toHaveBeenCalledWith("/auth/password-reset/request", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "alice@example.com" }),
    });
    expect(result).toEqual({ ok: true, status: 200, data: { reset_token: "abc" } });
  });

  it("sends password reset confirmation with token and new password", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ msg: "Password updated" }),
    });

    const result = await resetPassword(
      "alice@example.com",
      "reset-token",
      "NewPass123!",
    );

    expect(fetchMock).toHaveBeenCalledWith("/auth/password-reset/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: "alice@example.com",
        reset_token: "reset-token",
        new_password: "NewPass123!",
      }),
    });
    expect(result).toEqual({ ok: true, status: 200, data: { msg: "Password updated" } });
  });

  it("sends bearer token to fetch the current user", async () => {
    localStorage.setItem("token", "jwt-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ email: "alice@example.com", role: "user" }),
    });

    const result = await getCurrentUser();

    expect(fetchMock).toHaveBeenCalledWith("/auth/me", {
      headers: { Authorization: "Bearer jwt-token" },
    });
    expect(result).toEqual({
      ok: true,
      status: 200,
      data: { email: "alice@example.com", role: "user" },
    });
  });
});
