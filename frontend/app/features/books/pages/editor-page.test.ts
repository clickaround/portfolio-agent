import { describe, expect, it, vi } from "vitest";
import { clientLoader } from "./editor-page";

vi.mock("../queries", () => ({ getAttempts: vi.fn().mockResolvedValue([{ attempt: "01", files: { "book.designcraft": true } }, { attempt: "02", files: {} }]) }));

describe("editor route", () => {
  it("loads the selected editable attempt", async () => {
    const result = await clientLoader({ params: { projectId: "demo", attempt: "01" } } as never);
    expect(result.attempt).toBe("01");
    expect(result.projectId).toBe("demo");
  });
  it("rejects attempts without an editable document", async () => {
    await expect(clientLoader({ params: { projectId: "demo", attempt: "02" } } as never)).rejects.toMatchObject({ status: 404 });
  });
});
