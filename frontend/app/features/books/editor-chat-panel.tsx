import { useEffect, useRef, useState } from "react";
import { JobProgress } from "~/common/components/job-progress";
import { Button } from "~/common/components/ui/button";
import { chatEditor } from "./mutations";

interface Message { role: "user" | "assistant"; content: string; proposedText?: string; truncated?: boolean }
interface ChatResult { reply?: unknown; proposed_text?: unknown; text_truncated?: unknown }

export function EditorChatPanel({ projectId, attempt, canEdit, onInsert, isOpen = true }: { projectId: string; attempt: string; canEdit: boolean; onInsert: (text: string) => Promise<void>; isOpen?: boolean }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [job, setJob] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const pending = useRef(false);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView?.({ block: "nearest" }); }, [messages, job]);

  async function send() {
    const content = input.trim();
    if (!content || pending.current || job) return;
    pending.current = true;
    setIsSending(true);
    setError("");
    const next: Message[] = [...messages, { role: "user", content }];
    setMessages(next);
    setInput("");
    try {
      const response = await chatEditor(projectId, attempt, next.slice(-20).map(({ role, content }) => ({ role, content })));
      setJob(response.job);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "메시지를 보내지 못했습니다.");
    } finally { pending.current = false; setIsSending(false); }
  }
  async function insert(text: string) {
    setIsApplying(true);
    setError("");
    try { await onInsert(text); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "텍스트를 넣지 못했습니다."); }
    finally { setIsApplying(false); }
  }
  return <aside aria-label="에이전트 대화" hidden={!isOpen} style={{ display: isOpen ? undefined : "none" }} className="flex h-full min-h-0 w-full flex-col bg-background">
    <header className="border-b p-4"><h2 className="font-semibold">포트폴리오 에이전트</h2><p className="mt-1 text-xs text-muted-foreground">Claude · 시도 {attempt}</p></header>
    <div className="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
      <p className="text-xs text-muted-foreground">대화와 이 시도의 저장된 PDF 텍스트가 Claude로 전송됩니다. 저장하지 않은 변경과 이미지·배치는 볼 수 없습니다.</p>
      {messages.length === 0 && <p className="text-sm text-muted-foreground">포트폴리오 문구나 구성에 대해 물어보세요.</p>}
      {messages.map((message, index) => <div key={index} className={`rounded-lg p-3 text-sm ${message.role === "user" ? "ml-6 bg-primary text-primary-foreground" : "mr-6 bg-muted"}`}>
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        {message.truncated && <p className="mt-2 text-xs">저장된 문서의 텍스트 일부만 전달됐습니다.</p>}
        {message.proposedText && <div className="mt-3 space-y-2 border-t pt-2"><p className="whitespace-pre-wrap break-words">{message.proposedText}</p><Button type="button" size="sm" variant="outline" disabled={!canEdit || isApplying} onClick={() => void insert(message.proposedText!)}>텍스트 상자로 넣기</Button></div>}
      </div>)}
      {job && <JobProgress compact key={job} jobId={job} onError={(message) => { setError(message); setJob(null); }} onDone={(finished) => {
        const result = finished.result as ChatResult | null;
        if (finished.status === "succeeded" && typeof result?.reply === "string") {
          setMessages((previous) => [...previous, { role: "assistant", content: result.reply as string, proposedText: typeof result.proposed_text === "string" ? result.proposed_text : undefined, truncated: result.text_truncated === true }]);
        } else setError(finished.error ?? "답변을 받지 못했습니다.");
        setJob(null);
      }} />}
      {error && <p role="alert" className="text-sm text-red-500">{error}</p>}
      <div ref={end} />
    </div>
    <form className="space-y-2 border-t p-3" onSubmit={(event) => { event.preventDefault(); void send(); }}>
      <label htmlFor="editor-chat-input" className="sr-only">에이전트에게 메시지</label>
      <textarea id="editor-chat-input" className="min-h-20 w-full resize-y rounded-md border bg-background p-2 text-sm" placeholder="메시지를 입력하세요" maxLength={4000} value={input} onChange={(event) => setInput(event.target.value)} />
      <Button type="submit" className="w-full" disabled={!input.trim() || isSending || Boolean(job)}>보내기</Button>
    </form>
  </aside>;
}
