import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { ResizableEditorSplit } from "./resizable-editor-split";

it("places chat first and changes both panel sizes with the keyboard", () => {
  const { container } = render(<ResizableEditorSplit isOpen panel={<div>Chat</div>} editor={<div>Editor</div>} />);
  const split = screen.getByRole("separator", { name: "대화 패널 크기 조절" });
  expect(container.textContent).toContain("ChatEditor");
  expect(split).toHaveAttribute("aria-valuenow", "30");
  fireEvent.keyDown(split, { key: "ArrowRight" });
  expect(split).toHaveAttribute("aria-valuenow", "32");
  expect(screen.getByText("Chat").parentElement).toHaveStyle({ "--panel-width": "32%" });
});

it("provides mobile controls to switch between chat and the editor", () => {
  render(<ResizableEditorSplit isOpen panel={<div>Chat</div>} editor={<div>Editor</div>} />);
  const chat = screen.getByRole("button", { name: "대화" });
  const editor = screen.getByRole("button", { name: "편집기" });
  expect(chat).toHaveAttribute("aria-pressed", "true");
  fireEvent.click(editor);
  expect(editor).toHaveAttribute("aria-pressed", "true");
  expect(chat).toHaveAttribute("aria-pressed", "false");
});
