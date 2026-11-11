import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { expect, it, vi } from "vitest";
import { LandingNavigation } from "./landing-navigation";

vi.mock("~/lib/auth/session", () => ({ useSession: () => ({ user: null, loading: false }) }));

it("links the shared home navigation to real project and authentication routes", () => {
  render(<MemoryRouter><LandingNavigation /></MemoryRouter>);
  expect(screen.getByRole("navigation", { name: "주 메뉴" })).toHaveClass("dui-navigation");
  expect(screen.getByRole("link", { name: "프로젝트" })).toHaveAttribute("href", "/projects");
  expect(screen.getByRole("link", { name: "로그인" })).toHaveAttribute("href", "/auth/login");
  expect(screen.getByRole("link", { name: "회원가입" })).toHaveAttribute("href", "/auth/join");
});
