import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { beforeEach, expect, it, vi } from "vitest";
import AuthPage from "./auth-page";
import { authClient } from "~/lib/auth/client";

vi.mock("~/lib/auth/client", () => ({
  authClient: {
    auth: {
      signInWithPassword: vi.fn(),
      signUp: vi.fn(),
      signInWithOAuth: vi.fn(),
    },
  },
}));

beforeEach(() => vi.clearAllMocks());

it("submits email and password to the configured authentication service", async () => {
  vi.mocked(authClient!.auth.signInWithPassword).mockResolvedValue({ data: {} as never, error: null });
  render(<MemoryRouter initialEntries={["/auth/login"]}><AuthPage mode="login" /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText("이메일"), { target: { value: "test@example.com" } });
  fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "password123" } });
  fireEvent.click(screen.getByRole("button", { name: "로그인" }));
  await waitFor(() => expect(authClient!.auth.signInWithPassword).toHaveBeenCalledWith({ email: "test@example.com", password: "password123" }));
});

it("starts sign up with the email confirmation callback", async () => {
  vi.mocked(authClient!.auth.signUp).mockResolvedValue({ data: { user: null, session: null }, error: null });
  render(<MemoryRouter initialEntries={["/auth/join"]}><AuthPage mode="join" /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText("이름"), { target: { value: "Example" } });
  fireEvent.change(screen.getByLabelText("이메일"), { target: { value: "test@example.com" } });
  fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "password123" } });
  fireEvent.click(screen.getByRole("button", { name: "회원가입" }));
  await waitFor(() => expect(authClient!.auth.signUp).toHaveBeenCalledWith(expect.objectContaining({ email: "test@example.com", password: "password123", options: expect.objectContaining({ emailRedirectTo: expect.stringContaining("/auth/callback") }) })));
});

it("shows authentication failures instead of treating them as a login", async () => {
  vi.mocked(authClient!.auth.signInWithPassword).mockResolvedValue({ data: { user: null, session: null }, error: new Error("Invalid credentials") as never });
  render(<MemoryRouter initialEntries={["/auth/login"]}><AuthPage mode="login" /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText("이메일"), { target: { value: "test@example.com" } });
  fireEvent.change(screen.getByLabelText("비밀번호"), { target: { value: "password123" } });
  fireEvent.click(screen.getByRole("button", { name: "로그인" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Invalid credentials");
});
