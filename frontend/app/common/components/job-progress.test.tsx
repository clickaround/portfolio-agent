import { act, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { JobProgress } from "./job-progress";

vi.mock("~/lib/api/jobs", () => ({ getJob: vi.fn() }));
import { getJob } from "~/lib/api/jobs";

afterEach(() => { vi.useRealTimers(); vi.clearAllMocks(); });

it("retries a transient lookup failure and reports completion", async () => {
  vi.useFakeTimers();
  vi.mocked(getJob).mockRejectedValueOnce(new Error("offline")).mockResolvedValueOnce({ id: "1", kind: "plan", project: "p", status: "succeeded", created: "today" });
  const onDone = vi.fn();
  render(<JobProgress jobId="1" onDone={onDone} />);
  await act(async () => { await Promise.resolve(); });
  expect(screen.getByRole("alert")).toHaveTextContent("offline");
  await act(async () => { await vi.advanceTimersByTimeAsync(1500); });
  expect(getJob).toHaveBeenCalledTimes(2);
  expect(onDone).toHaveBeenCalledTimes(1);
  expect(screen.queryByRole("alert")).toBeNull();
});
