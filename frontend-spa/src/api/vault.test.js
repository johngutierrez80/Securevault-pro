import { afterEach, describe, expect, it, vi } from "vitest";
import { deleteSecret, getSecrets, saveSecret, updateSecret } from "./vault";

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("vault api", () => {
  it("loads secrets with the bearer token", async () => {
    localStorage.setItem("token", "vault-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => [{ id: 1, site: "example.com", password: "secret" }],
    });

    const secrets = await getSecrets();

    expect(fetchMock).toHaveBeenCalledWith("/vault/secret", {
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer vault-token",
      },
    });
    expect(secrets).toEqual([
      { id: 1, site: "example.com", password: "secret" },
    ]);
  });

  it("persists and updates secrets with authenticated JSON requests", async () => {
    localStorage.setItem("token", "vault-token");
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue({ ok: true });

    await saveSecret("example.com", "secret");
    await updateSecret(7, "mail.example.com", "new-secret");
    await deleteSecret(7);

    expect(fetchMock).toHaveBeenNthCalledWith(1, "/vault/secret", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer vault-token",
      },
      body: JSON.stringify({ site: "example.com", password: "secret" }),
    });
    expect(fetchMock).toHaveBeenNthCalledWith(2, "/vault/secret/7", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer vault-token",
      },
      body: JSON.stringify({
        site: "mail.example.com",
        password: "new-secret",
      }),
    });
    expect(fetchMock).toHaveBeenNthCalledWith(3, "/vault/secret/7", {
      method: "DELETE",
      headers: {
        Authorization: "Bearer vault-token",
      },
    });
  });
});
