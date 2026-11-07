import { describe, expect, it, vi } from "vitest";
import { observeDesignCraftSaves } from "./editor-bridge";

describe("DesignCraft save bridge", () => {
  it("captures native saves without suppressing the original download and restores methods", () => {
    const oldCreate = URL.createObjectURL;
    const oldRevoke = URL.revokeObjectURL;
    const oldClick = HTMLAnchorElement.prototype.click;
    const nativeClick = vi.fn();
    URL.createObjectURL = vi.fn(() => "blob:test");
    URL.revokeObjectURL = vi.fn();
    HTMLAnchorElement.prototype.click = nativeClick;
    const nativeCreate = URL.createObjectURL;
    const capture = vi.fn();
    try {
      const restore = observeDesignCraftSaves(window, capture);
      const blob = new Blob(["data"]);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "book.designcraft";
      anchor.click();
      expect(capture).toHaveBeenCalledWith(blob, "book.designcraft");
      expect(nativeClick).toHaveBeenCalledOnce();
      restore();
      expect(URL.createObjectURL).toBe(nativeCreate);
      expect(HTMLAnchorElement.prototype.click).toBe(nativeClick);
    } finally {
      URL.createObjectURL = oldCreate;
      URL.revokeObjectURL = oldRevoke;
      HTMLAnchorElement.prototype.click = oldClick;
    }
  });
  it("preserves download even if the capture callback fails", () => {
    const oldCreate = URL.createObjectURL;
    const oldRevoke = URL.revokeObjectURL;
    const oldClick = HTMLAnchorElement.prototype.click;
    const nativeClick = vi.fn();
    URL.createObjectURL = vi.fn(() => "blob:test");
    URL.revokeObjectURL = vi.fn();
    HTMLAnchorElement.prototype.click = nativeClick;
    try {
      const restore = observeDesignCraftSaves(window, () => { throw new Error("capture failed"); });
      const anchor = document.createElement("a");
      anchor.href = URL.createObjectURL(new Blob(["data"]));
      anchor.download = "book.designcraft";
      expect(() => anchor.click()).not.toThrow();
      expect(nativeClick).toHaveBeenCalledOnce();
      restore();
    } finally {
      URL.createObjectURL = oldCreate;
      URL.revokeObjectURL = oldRevoke;
      HTMLAnchorElement.prototype.click = oldClick;
    }
  });
});
