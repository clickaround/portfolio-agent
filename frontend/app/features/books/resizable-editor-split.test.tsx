import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { ResizableEditorSplit } from "./resizable-editor-split";

it("places chat first and changes both panel sizes with the keyboard", () => {
  const { container } = render(<ResizableEditorSplit isOpen panel={<div>Chat</div>} editor={<div>Editor</div>} />);
  const split = screen.getByRole("separator", { name: "대화 패널 크기 조절" });
  expect(container.textContent).toBe("ChatEditor");
  expect(split).toHaveAttribute("aria-valuenow", "30");
  fireEvent.keyDown(split, { key: "ArrowRight" });
  expect(split).toHaveAttribute("aria-valuenow", "32");
  expect(screen.getByText("Chat").parentElement).toHaveStyle({ width: "32%" });
});
