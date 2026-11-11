import { AuthSplit, duiThemeStyle, DuiTheme } from "@dk/dui";
import { render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

it("shares the auth shell while applying each application's theme, including changes", () => {
  const ctx = { clearRect: vi.fn(), fillRect: vi.fn(), fillStyle: "", globalAlpha: 1 };
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue(ctx as unknown as CanvasRenderingContext2D);
  vi.stubGlobal("matchMedia", () => ({ matches: true }));
  const { container, rerender } = render(<DuiTheme theme={{ accent: "#123456", background: "#eeeeee" }}><AuthSplit><p>Login form</p></AuthSplit></DuiTheme>);
  expect(screen.getByText("Login form")).toBeVisible();
  expect(container.querySelector(".dui-theme")).toHaveStyle({ "--dui-accent": "#123456", "--dui-background": "#eeeeee" });
  expect(ctx.fillStyle).toBe("#123456");
  rerender(<DuiTheme theme={{ accent: "#abcdef" }}><AuthSplit><p>Login form</p></AuthSplit></DuiTheme>);
  expect(ctx.fillStyle).toBe("#abcdef");
});

it("maps one theme to both Tailwind 3 HSL channels and Tailwind 4 CSS colors", () => {
  const palette = { accent: "#ff0000", background: "#000000", border: "#fff" };
  expect(duiThemeStyle(palette)).toMatchObject({ "--primary": "#ff0000", "--background": "#000000", "--border": "#fff" });
  expect(duiThemeStyle(palette, "hsl-channels")).toMatchObject({ "--primary": "0.00 100.00% 50.00%", "--background": "0.00 0.00% 0.00%", "--border": "0.00 0.00% 100.00%" });
});
