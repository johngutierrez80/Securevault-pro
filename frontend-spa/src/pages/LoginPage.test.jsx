import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LoginPage from "./LoginPage";

const navigateMock = vi.fn();
const loginUserMock = vi.fn();
const registerUserMock = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("../api/auth", () => ({
  loginUser: (...args) => loginUserMock(...args),
  registerUser: (...args) => registerUserMock(...args),
}));

function renderLoginPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  loginUserMock.mockReset();
  registerUserMock.mockReset();
  navigateMock.mockReset();
  localStorage.clear();
});

describe("LoginPage", () => {
  it("shows a validation error when credentials are empty", async () => {
    const user = userEvent.setup();

    renderLoginPage();

    await user.click(
      screen.getByRole("button", { name: /iniciar sesi[óo]n/i }),
    );

    expect(
      await screen.findByText("Credenciales incorrectas"),
    ).toBeInTheDocument();
    expect(loginUserMock).not.toHaveBeenCalled();
  });

  it("stores the token and redirects after a successful login", async () => {
    const user = userEvent.setup();
    loginUserMock.mockResolvedValue({
      ok: true,
      data: { access_token: "token-de-prueba" },
    });

    renderLoginPage();

    await user.type(screen.getByPlaceholderText(/usuario/i), "alice");
    await user.type(
      screen.getByPlaceholderText(/••••••••••••/i),
      "super-secret",
    );
    await user.click(
      screen.getByRole("button", { name: /iniciar sesi[óo]n/i }),
    );

    await waitFor(() => {
      expect(loginUserMock).toHaveBeenCalledWith("alice", "super-secret");
      expect(localStorage.getItem("token")).toBe("token-de-prueba");
      expect(navigateMock).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("shows a success message after a successful registration", async () => {
    const user = userEvent.setup();
    registerUserMock.mockResolvedValue({ ok: true, data: {} });

    renderLoginPage();

    await user.type(screen.getByPlaceholderText(/usuario/i), "alice");
    await user.type(
      screen.getByPlaceholderText(/••••••••••••/i),
      "super-secret",
    );
    await user.click(
      screen.getByRole("button", { name: /crear cuenta gratuita/i }),
    );

    expect(await screen.findByText(/usuario creado/i)).toBeInTheDocument();
  });
});
