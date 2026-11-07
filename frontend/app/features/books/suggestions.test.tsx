import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createRoutesStub } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AgentSuggestions } from "./suggestions";

afterEach(() => vi.unstubAllGlobals());

describe("agent suggestions", () => {
  it("warns when text was truncated and hides a detail after it becomes stale", async () => {
    const record = { suggestion_id: "one", created_at: "today", source_kind: "synthetic", status: "fresh" };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify([record])))
      .mockResolvedValueOnce(new Response(JSON.stringify({ text_truncated: true, output: { summary: "old analysis", pages: [] } })))
      .mockResolvedValueOnce(new Response(JSON.stringify([{ ...record, status: "stale" }])));
    vi.stubGlobal("fetch", fetchMock);
    const Router = createRoutesStub([{ path: "/", Component: () => <AgentSuggestions projectId="demo" attempt="02" busy={false} /> }]);
    render(<Router initialEntries={["/"]} />);
    fireEvent.click(await screen.findByText("보기"));
    expect(await screen.findByText("old analysis")).toBeInTheDocument();
    expect(screen.getByText(/일부만 분석/)).toBeInTheDocument();
    fireEvent.click(screen.getByText("제안 목록 새로고침"));
    await waitFor(() => expect(screen.queryByText("old analysis")).not.toBeInTheDocument());
    expect(screen.getByText(/만료/)).toBeInTheDocument();
  });
});
