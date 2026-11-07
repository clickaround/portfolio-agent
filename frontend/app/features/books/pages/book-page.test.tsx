import { describe, expect, it, vi } from "vitest";
import { clientAction } from "./book-page";

vi.mock("../mutations", () => ({ composeBook: vi.fn().mockResolvedValue({ job: "j" }), openDesignCraft: vi.fn().mockResolvedValue({}) }));
import { composeBook, openDesignCraft } from "../mutations";

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
});
