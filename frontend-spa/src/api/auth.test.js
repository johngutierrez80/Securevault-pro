import { afterEach, describe, expect, it, vi } from "vitest";
import { loginUser, registerUser } from "./auth";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("auth api", () => {
  it("sends login requests with JSON credentials", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: "abc123" }),
    });

    const result = await loginUser("alice", "secret");

    expect(fetchMock).toHaveBeenCalledWith("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "alice", password: "secret" }),
    });
    expect(result).toEqual({ ok: true, data: { access_token: "abc123" } });
  });

  it("sends registration requests with JSON credentials", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => ({ message: "created" }),
    });

    const result = await registerUser("alice", "secret");

    expect(fetchMock).toHaveBeenCalledWith("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: "alice", password: "secret" }),
    });
    expect(result).toEqual({ ok: true, data: { message: "created" } });
  });
});
