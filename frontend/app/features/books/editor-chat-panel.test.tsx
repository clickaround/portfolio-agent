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
  expect(insert).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "텍스트 상자로 넣기" }));
  await waitFor(() => expect(insert).toHaveBeenCalledWith("새 제목"));
  fireEvent.change(screen.getByLabelText("에이전트에게 메시지"), { target: { value: "한국어로 바꿔줘" } });
  fireEvent.click(screen.getByRole("button", { name: "보내기" }));
  await waitFor(() => expect(chatEditor).toHaveBeenLastCalledWith("demo", "02", [
    { role: "user", content: "제목을 제안해줘" }, { role: "assistant", content: "제안입니다" }, { role: "user", content: "한국어로 바꿔줘" },
  ]));
});
