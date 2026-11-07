import { describe, expect, it, vi } from "vitest";
import { clientAction } from "./book-page";

vi.mock("../mutations", () => ({ composeBook: vi.fn().mockResolvedValue({ job: "j" }), openDesignCraft: vi.fn().mockResolvedValue({}), importDesignCraft: vi.fn().mockResolvedValue({ job: "import-job" }), recoverLedger: vi.fn().mockResolvedValue({ job: "recover-job" }), suggestDesignCraft: vi.fn().mockResolvedValue({ job: "suggest-job" }) }));
import { composeBook, importDesignCraft, openDesignCraft, recoverLedger, suggestDesignCraft } from "../mutations";

describe("DesignCraft export", () => {
  it("sends the selected exporter to the compose API", async () => {
    const form = new FormData();
    form.set("designcraft", "on");
    await clientAction({ request: new Request("http://localhost/book", { method: "POST", body: form }), params: { projectId: "demo" } } as never);
    expect(composeBook).toHaveBeenCalledWith("demo", expect.objectContaining({ also: ["designcraft"] }));
  });
  it("opens the selected attempt in DesignCraft", async () => {
    const form = new FormData();
    form.set("intent", "open-designcraft");
    form.set("attempt", "02");
    await clientAction({ request: new Request("http://localhost/book", { method: "POST", body: form }), params: { projectId: "demo" } } as never);
    expect(openDesignCraft).toHaveBeenCalledWith("demo", "02");
  });
  it("submits the saved DesignCraft file to its source attempt", async () => {
    const form = new FormData();
    form.set("intent", "import-designcraft");
    form.set("attempt", "02");
    form.set("file", new File(["edited"], "edited.designcraft"));
    const out = await clientAction({ request: { formData: async () => form }, params: { projectId: "demo" } } as never);
    expect(importDesignCraft).toHaveBeenCalledWith("demo", "02", expect.objectContaining({ name: "edited.designcraft" }));
    expect(out).toEqual({ job: "import-job" });
  });
  it("retries a pending ledger for the chosen attempt", async () => {
    const form = new FormData();
    form.set("intent", "recover-ledger");
    form.set("attempt", "02");
    const out = await clientAction({ request: { formData: async () => form }, params: { projectId: "demo" } } as never);
    expect(recoverLedger).toHaveBeenCalledWith("demo", "02");
    expect(out).toEqual({ job: "recover-job" });
  });
  it("sends an explicit agent request for the selected edited attempt", async () => {
    const form = new FormData();
    form.set("intent", "suggest-designcraft");
    form.set("attempt", "02");
    form.set("instructions", "Improve hierarchy");
    form.set("source_kind", "synthetic");
    const out = await clientAction({ request: { formData: async () => form }, params: { projectId: "demo" } } as never);
    expect(suggestDesignCraft).toHaveBeenCalledWith("demo", "02", { instructions: "Improve hierarchy", source_kind: "synthetic" });
    expect(out).toEqual({ job: "suggest-job" });
  });
});
