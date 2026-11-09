import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider, useLocation } from "react-router";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { GenerationWorkspace } from "./workspace-page";
import { generatePortfolio } from "../mutations";
import { getAttempts } from "../queries";
import { uploadProjectAsset } from "~/lib/api/assets";
import { executeEditorCommand } from "../editor-command";

vi.mock("../mutations", () => ({ generatePortfolio: vi.fn() }));
vi.mock("../queries", () => ({ getAttempts: vi.fn() }));
vi.mock("~/lib/api/assets", () => ({ uploadProjectAsset: vi.fn() }));
vi.mock("../editor-command", () => ({ executeEditorCommand: vi.fn() }));
vi.mock("~/common/components/job-progress", () => ({
  JobProgress: ({ onDone }: { onDone: (job: unknown) => void }) => <button onClick={() => onDone({ status: "succeeded", result: { compose: { attempt: "05" } } })}>작업 완료</button>,
}));

function Destination() {
  const location = useLocation();
  return <p>편집기 도착: {location.pathname}</p>;
}

function renderWorkspace() {
  const router = createMemoryRouter([
    { path: "/", element: <GenerationWorkspace projectId="demo" title="Demo" /> },
    { path: "/projects/:projectId/editor/:attempt", element: <Destination /> },
  ], { initialEntries: ["/"] });
  return render(<RouterProvider router={router} />);
}

beforeEach(() => { vi.clearAllMocks(); sessionStorage.clear(); vi.mocked(executeEditorCommand).mockRejectedValue(new Error("command `document.inspect` is not available right now: no document open")); });
afterEach(() => vi.restoreAllMocks());

it("opens the exact newly generated editable attempt after checking it exists", async () => {
  vi.mocked(generatePortfolio).mockResolvedValue({ job: "job-1", poll: "/jobs/job-1", status: "queued" });
  vi.mocked(getAttempts).mockResolvedValue([{ attempt: "05", files: { "book.designcraft": true } }] as never);
  renderWorkspace();
  expect(screen.getByTitle("DesignCraft")).toHaveAttribute("src", "/pascal-editor/index.html");
  fireEvent.change(screen.getByLabelText("포트폴리오 요청"), { target: { value: "도면 중심으로 만들어 줘" } });
  fireEvent.click(screen.getByRole("button", { name: "포트폴리오 만들기" }));
  await waitFor(() => expect(generatePortfolio).toHaveBeenCalledWith("demo", expect.objectContaining({ instructions: "도면 중심으로 만들어 줘", width_mm: 297, height_mm: 210 })));
  fireEvent.click(await screen.findByRole("button", { name: "작업 완료" }));
  expect(await screen.findByText("편집기 도착: /projects/demo/editor/05")).toBeInTheDocument();
});

it("keeps an open document when generation finishes until the user opens the result", async () => {
  vi.mocked(generatePortfolio).mockResolvedValue({ job: "job-3", poll: "/jobs/job-3", status: "queued" });
  vi.mocked(getAttempts).mockResolvedValue([{ attempt: "05", files: { "book.designcraft": true } }] as never);
  vi.mocked(executeEditorCommand).mockResolvedValue({ dirty: true });
  renderWorkspace();
  fireEvent.change(screen.getByLabelText("포트폴리오 요청"), { target: { value: "만들어 줘" } });
  fireEvent.click(screen.getByRole("button", { name: "포트폴리오 만들기" }));
  fireEvent.click(await screen.findByRole("button", { name: "작업 완료" }));
  expect(await screen.findByRole("button", { name: "생성 결과 열기" })).toBeInTheDocument();
  vi.spyOn(window, "confirm").mockReturnValue(false);
  fireEvent.click(screen.getByRole("button", { name: "생성 결과 열기" }));
  expect(screen.getByTitle("DesignCraft")).toBeInTheDocument();
});

it("does not open a different attempt when the generated editable file is missing", async () => {
  vi.mocked(generatePortfolio).mockResolvedValue({ job: "job-2", poll: "/jobs/job-2", status: "queued" });
  vi.mocked(getAttempts).mockResolvedValue([{ attempt: "04", files: { "book.designcraft": true } }, { attempt: "05", files: { "book.designcraft": false } }] as never);
  renderWorkspace();
  fireEvent.change(screen.getByLabelText("포트폴리오 요청"), { target: { value: "만들어 줘" } });
  fireEvent.click(screen.getByRole("button", { name: "포트폴리오 만들기" }));
  fireEvent.click(await screen.findByRole("button", { name: "작업 완료" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("편집 가능한 결과 파일을 확인하지 못했습니다");
});

it("uploads selected sources into the chosen project category", async () => {
  vi.mocked(uploadProjectAsset).mockResolvedValue({ id: "sheet", file: "sheet.pdf", kind: "drawings" } as never);
  renderWorkspace();
  fireEvent.change(screen.getByLabelText("자료 종류"), { target: { value: "drawings" } });
  const file = new File(["synthetic"], "sheet.pdf", { type: "application/pdf" });
  fireEvent.change(screen.getByLabelText("자료 선택"), { target: { files: [file] } });
  fireEvent.change(screen.getByLabelText("포트폴리오 요청"), { target: { value: "도면으로 만들어 줘" } });
  expect(screen.getByRole("button", { name: "포트폴리오 만들기" })).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "자료 추가" }));
  await waitFor(() => expect(uploadProjectAsset).toHaveBeenCalledWith("demo", "drawings", file));
  expect(await screen.findByText("1개 자료를 프로젝트에 추가했습니다.")).toBeInTheDocument();
});
