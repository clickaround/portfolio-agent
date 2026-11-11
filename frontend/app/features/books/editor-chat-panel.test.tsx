import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { EditorChatPanel } from "./editor-chat-panel";
import { chatEditor } from "./mutations";

vi.mock("./mutations", () => ({ chatEditor: vi.fn().mockResolvedValue({ job: "chat-job" }) }));
vi.mock("~/common/components/job-progress", () => ({ JobProgress: ({ onDone }: { onDone: (job: unknown) => void }) => <button type="button" onClick={() => onDone({ status: "succeeded", result: { reply: "제안입니다", proposed_text: "새 제목" } })}>답변 완료</button> }));

it("sends the conversation and applies a suggested text only after a click", async () => {
  const insert = vi.fn().mockResolvedValue(undefined);
  render(<EditorChatPanel projectId="demo" attempt="02" canEdit onInsert={insert} />);
  fireEvent.change(screen.getByLabelText("에이전트에게 메시지"), { target: { value: "제목을 제안해줘" } });
  fireEvent.click(screen.getByRole("button", { name: "보내기" }));
  await waitFor(() => expect(chatEditor).toHaveBeenCalledWith("demo", "02", [{ role: "user", content: "제목을 제안해줘" }]));
  fireEvent.click(await screen.findByRole("button", { name: "답변 완료" }));
  expect(await screen.findByText("제안입니다")).toBeInTheDocument();
  expect(screen.getByText("제목을 제안해줘").closest('[data-role="user"]')).toBeTruthy();
  expect(screen.getByText("제안입니다").closest('[data-role="assistant"]')).toBeTruthy();
  expect(insert).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "텍스트 상자로 넣기" }));
  await waitFor(() => expect(insert).toHaveBeenCalledWith("새 제목"));
  fireEvent.change(screen.getByLabelText("에이전트에게 메시지"), { target: { value: "한국어로 바꿔줘" } });
  fireEvent.click(screen.getByRole("button", { name: "보내기" }));
  await waitFor(() => expect(chatEditor).toHaveBeenLastCalledWith("demo", "02", [
    { role: "user", content: "제목을 제안해줘" }, { role: "assistant", content: "제안입니다" }, { role: "user", content: "한국어로 바꿔줘" },
  ]));
});

it("sends the current editor structure only when explicitly selected", async () => {
  const snapshot = vi.fn().mockResolvedValue({ pageCount: 2, dirty: true, selection: { items: [7] } });
  render(<EditorChatPanel projectId="demo" attempt="02" canEdit onInsert={vi.fn()} onSnapshot={snapshot} />);
  fireEvent.click(screen.getByLabelText("현재 편집 상태 포함"));
  fireEvent.change(screen.getByLabelText("에이전트에게 메시지"), { target: { value: "선택된 항목은?" } });
  fireEvent.click(screen.getByRole("button", { name: "보내기" }));
  await waitFor(() => expect(chatEditor).toHaveBeenLastCalledWith("demo", "02", [{ role: "user", content: "선택된 항목은?" }], JSON.stringify({ pageCount: 2, dirty: true, selection: { items: [7] } })));
});

it("does not send a request if the requested live snapshot fails", async () => {
  vi.mocked(chatEditor).mockClear();
  render(<EditorChatPanel projectId="demo" attempt="02" canEdit onInsert={vi.fn()} onSnapshot={vi.fn().mockRejectedValue(new Error("편집기 상태를 읽지 못했습니다."))} />);
  fireEvent.click(screen.getByLabelText("현재 편집 상태 포함"));
  fireEvent.change(screen.getByLabelText("에이전트에게 메시지"), { target: { value: "선택된 항목은?" } });
  fireEvent.click(screen.getByRole("button", { name: "보내기" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("편집기 상태를 읽지 못했습니다.");
  expect(chatEditor).not.toHaveBeenCalled();
});

it("keeps the user's generation request visible when the editor opens", () => {
  render(<EditorChatPanel projectId="demo" attempt="05" canEdit onInsert={vi.fn()} generationPrompt="도면을 중심으로 구성해 줘" />);
  expect(screen.getByText("도면을 중심으로 구성해 줘")).toBeInTheDocument();
  expect(screen.getByText(/포트폴리오가 생성됐습니다/)).toBeInTheDocument();
});
