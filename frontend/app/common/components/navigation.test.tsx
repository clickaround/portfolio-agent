import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { expect, it, vi } from "vitest";
import Navigation from "./navigation";

it("provides real home and project navigation and a sidebar toggle", () => {
  const toggle = vi.fn();
  render(<MemoryRouter initialEntries={["/projects/demo/editor/02"]}><Navigation collapsed={false} onToggle={toggle} /></MemoryRouter>);
  const sidebar = screen.getByLabelText("사이드바");
  expect(sidebar.querySelector('a[href="/"]')).toBeTruthy();
  expect(sidebar.querySelector('a[href="/projects"]')).toBeTruthy();
  expect(sidebar.querySelector('a[href="/projects/demo"]')).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "사이드바 닫기" }));
  expect(toggle).toHaveBeenCalledOnce();
});
