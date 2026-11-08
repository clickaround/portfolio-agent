import { useCallback, useEffect, useRef, useState } from "react";
import { Form, Link, useBeforeUnload, useBlocker, useNavigation, useRevalidator, type BlockerFunction } from "react-router";
import { JobProgress } from "~/common/components/job-progress";
import { Badge } from "~/common/components/ui/badge";
import { Button } from "~/common/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "~/common/components/ui/card";
import { Input } from "~/common/components/ui/input";
import { ApiError } from "~/lib/api/client";
import { bookUrl, pageUrl } from "~/lib/api/urls";
import { observeDesignCraftSaves } from "../editor-bridge";
import { executeEditorCommand } from "../editor-command";
import { EditorChatPanel } from "../editor-chat-panel";
import { composeBook, importDesignCraft, openDesignCraft, recoverLedger, rewriteEditorText, suggestDesignCraft } from "../mutations";
import { getAttempts } from "../queries";
import { AgentSuggestions } from "../suggestions";
import type { Route } from "./+types/book-page";

export const meta: Route.MetaFunction = () => [{ title: "Book | Pascal" }];

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return { projectId: params.projectId, attempts: await getAttempts(params.projectId) };
}

export async function clientAction({ request, params }: Route.ClientActionArgs) {
  const f = await request.formData();
  const num = (k: string, d: number) => (Number.isFinite(Number(f.get(k))) && f.get(k) !== "" ? Number(f.get(k)) : d);
  try {
    if (f.get("intent") === "suggest-designcraft") {
      const kind = String(f.get("source_kind"));
      if (!["synthetic", "real", "unknown"].includes(kind)) return { error: "자료 종류를 선택하세요." };
      const result = await suggestDesignCraft(params.projectId, String(f.get("attempt")), { instructions: String(f.get("instructions") ?? ""), source_kind: kind as "synthetic" | "real" | "unknown" });
      return { job: result.job };
    }
    if (f.get("intent") === "recover-ledger") {
      const result = await recoverLedger(params.projectId, String(f.get("attempt")));
      return { job: result.job };
    }
    if (f.get("intent") === "import-designcraft") {
      const file = f.get("file");
      if (!(file instanceof File) || file.size === 0 || !file.name.toLowerCase().endsWith(".designcraft")) return { error: "저장한 .designcraft 파일을 선택하세요." };
      const result = await importDesignCraft(params.projectId, String(f.get("attempt")), file);
      return { job: result.job };
    }
    if (f.get("intent") === "open-designcraft") {
      const opened = await openDesignCraft(params.projectId, String(f.get("attempt")));
      return { message: `DesignCraft 편집기를 열었습니다. 수정본 위치: ${opened.edit_path}. 원본 시도와 별도이며 다시 검토해야 합니다.` };
    }
    const out = await composeBook(params.projectId, {
      width_mm: num("width_mm", 297),
      height_mm: num("height_mm", 210),
      margin_mm: num("margin_mm", 12),
      bleed_mm: num("bleed_mm", 0),
      header: f.get("header") === "on",
      also: f.get("designcraft") === "on" ? ["designcraft"] : [],
    });
    return { job: out.job };
  } catch (e) {
    if (e instanceof ApiError) return { error: e.message };
    throw e;
  }
}

type GateItem = { code?: string; page?: string; details?: string };

/** One line per gate finding: code, page, details. Blocking findings stop the book; advisory ones are for the reviewer. */
function GateList({ label, tone, items }: { label: string; tone: string; items?: unknown[] }) {
  if (!items?.length) return null;
  return (
    <details>
      <summary className={`cursor-pointer text-sm font-medium ${tone}`}>{label} ({items.length})</summary>
      <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
        {(items as GateItem[]).map((g, i) => (
          <li key={i}><span className="font-mono">{g.code ?? "?"}</span>{g.page ? ` · ${g.page}` : ""}{g.details ? ` · ${g.details}` : ""}</li>
        ))}
      </ul>
    </details>
  );
}

export function BookWorkspace({ loaderData, actionData, initialAttempt }: Pick<Route.ComponentProps, "loaderData" | "actionData"> & { initialAttempt?: string }) {
  const { revalidate } = useRevalidator();
  const editor = useRef<HTMLIFrameElement>(null);
  const editorBridge = useRef<(() => void) | null>(null);
  const activeAttempt = useRef<string | null>(null);
  const submittedFile = useRef<File | null>(null);
  const sending = useRef(false);
  const requestingText = useRef(false);
  const autoTimer = useRef<number | null>(null);
  const autoSent = useRef(false);
  const [editorOpen, setEditorOpen] = useState(Boolean(initialAttempt));
  const [editorMessage, setEditorMessage] = useState("");
  const [pendingAttempt, setPendingAttempt] = useState<string | null>(initialAttempt ?? null);
  const [editorHasDocument, setEditorHasDocument] = useState(false);
  const [savedFile, setSavedFile] = useState<{ file: File; attempt: string } | null>(null);
  const [importJob, setImportJob] = useState<string | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [editorText, setEditorText] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [textJob, setTextJob] = useState<string | null>(null);
  const [isRequestingText, setIsRequestingText] = useState(false);
  const [textProposal, setTextProposal] = useState("");
  const [isChatOpen, setIsChatOpen] = useState(true);
  useEffect(() => () => { editorBridge.current?.(); if (autoTimer.current !== null) window.clearTimeout(autoTimer.current); }, []);
  useEffect(() => {
    if (!initialAttempt) return;
    let cancelled = false;
    fetch("/pascal-editor/index.html").then(async (response) => {
      if (!response.ok || !(await response.text()).includes("designcraft_canvas")) throw new Error("우리 웹 편집기가 설치되지 않았습니다. editor/README.md의 빌드 절차를 실행하세요.");
    }).catch((error: unknown) => { if (!cancelled) setEditorMessage(error instanceof Error ? error.message : "웹 편집기를 불러오지 못했습니다."); });
    return () => { cancelled = true; };
  }, [initialAttempt]);
  const blocker = useBlocker(useCallback<BlockerFunction>(({ currentLocation, nextLocation }) => editorOpen && currentLocation.pathname !== nextLocation.pathname, [editorOpen]));
  useBeforeUnload(useCallback((event) => {
    if (editorOpen) { event.preventDefault(); event.returnValue = ""; }
  }, [editorOpen]));
  useEffect(() => {
    if (blocker.state === "blocked") {
      if (window.confirm("편집기의 변경사항을 다운로드로 저장했나요? 이동하면 저장하지 않은 내용이 사라질 수 있습니다.")) blocker.proceed();
      else blocker.reset();
    }
  }, [blocker]);
  async function openWebEditor(attempt: string) {
    setPendingAttempt(attempt);
    setEditorOpen(true);
    try {
      const response = await fetch("/pascal-editor/index.html");
      if (!response.ok || !(await response.text()).includes("designcraft_canvas")) throw new Error("우리 웹 편집기가 설치되지 않았습니다. editor/README.md의 빌드 절차를 실행하세요.");
      setEditorMessage("편집기 로딩이 끝나면 아래 보내기 버튼을 누르세요.");
    } catch (error) {
      setEditorMessage(error instanceof Error ? error.message : "웹 편집기를 불러오지 못했습니다.");
    }
  }
  async function sendToEditor(attempt: string) {
    if (sending.current) return;
    sending.current = true;
    setIsSending(true);
    try {
      if (editorHasDocument && !window.confirm("다른 파일을 열기 전에 편집 내용을 다운로드로 저장했나요? 저장하지 않은 내용이 사라질 수 있습니다.")) return;
      const doc = editor.current?.contentDocument;
      const canvas = doc?.querySelector("#designcraft_canvas");
      const loading = doc?.querySelector<HTMLElement>("#designcraft_loading");
      if (!canvas || (loading && getComputedStyle(loading).display !== "none")) throw new Error("편집기를 먼저 열고 로딩이 끝날 때까지 기다려 주세요.");
      const res = await fetch(bookUrl(loaderData.projectId, attempt, "designcraft"));
      if (!res.ok) throw new Error(`편집 파일을 가져오지 못했습니다 (HTTP ${res.status}).`);
      const data = new DataTransfer();
      data.items.add(new File([await res.blob()], `attempt-${attempt}.designcraft`, { type: "application/octet-stream" }));
      for (const type of ["dragenter", "dragover", "drop"]) canvas.dispatchEvent(new DragEvent(type, { bubbles: true, cancelable: true, dataTransfer: data, clientX: 400, clientY: 300 }));
      activeAttempt.current = attempt;
      setEditorHasDocument(true);
      setEditorMessage(`시도 ${attempt} 파일을 편집기에 전달했습니다. 편집기에서 파일이 열렸는지 확인해 주세요.`);
    } catch (error) {
      setEditorMessage(error instanceof Error ? error.message : "편집기에 파일을 전달하지 못했습니다.");
    } finally {
      sending.current = false;
      setIsSending(false);
    }
  }
  function connectEditorSave() {
    const frame = editor.current?.contentWindow as (Window & typeof globalThis) | null | undefined;
    try {
      editorBridge.current?.();
      if (!frame || frame.location.origin !== window.location.origin) return;
      editorBridge.current = observeDesignCraftSaves(frame, (blob, name) => {
        const attempt = activeAttempt.current;
        if (!attempt) return;
        setSavedFile({ file: new File([blob], name, { type: "application/octet-stream" }), attempt });
        setEditorMessage(`시도 ${attempt}의 저장본을 받았습니다. 프로젝트로 가져오기를 누르면 새 검토 시도를 만듭니다.`);
      });
      if (initialAttempt && !autoSent.current) {
        if (autoTimer.current !== null) window.clearTimeout(autoTimer.current);
        let retries = 0;
        const waitForEditor = () => {
          if (autoSent.current) return;
          const doc = editor.current?.contentDocument;
          const canvas = doc?.querySelector("#designcraft_canvas");
          const loading = doc?.querySelector<HTMLElement>("#designcraft_loading");
          if (canvas && (!loading || getComputedStyle(loading).display === "none")) {
            autoSent.current = true;
            void sendToEditor(initialAttempt);
          } else if (++retries < 60) {
            autoTimer.current = window.setTimeout(waitForEditor, 500);
          } else {
            setEditorMessage("편집기가 열리지 않았습니다. 빌드 상태를 확인하고 다시 시도하세요.");
          }
        };
        waitForEditor();
      }
    } catch {
      setEditorMessage("자동 저장 연결을 사용할 수 없습니다. 다운로드한 파일을 직접 가져오세요.");
    }
  }
  async function importSavedFile() {
    if (!savedFile) return;
    setIsImporting(true);
    try {
      const result = await importDesignCraft(loaderData.projectId, savedFile.attempt, savedFile.file);
      submittedFile.current = savedFile.file;
      setImportJob(result.job);
      setEditorMessage("편집본을 처리하고 있습니다. 완료 후 새 시도를 다시 검토하세요.");
    } catch (error) {
      setEditorMessage(error instanceof Error ? error.message : "편집본을 가져오지 못했습니다. 다운로드한 파일은 보존됩니다.");
    } finally {
      setIsImporting(false);
    }
  }
  async function insertTextFrame() {
    if (!editor.current || !editorText.trim()) return;
    setIsEditing(true);
    try {
      await executeEditorCommand(editor.current, "frame.create", { rect: [72, 72, 300, 150], content: "text", text: editorText });
      setEditorMessage("편집기에 텍스트 상자를 추가했습니다. 위치와 내용을 확인한 뒤 저장하세요.");
      setEditorText("");
    } catch (error) {
      setEditorMessage(error instanceof Error ? error.message : "텍스트 상자를 추가하지 못했습니다.");
    } finally { setIsEditing(false); }
  }
  async function insertChatText(text: string) {
    if (!editor.current || !editorHasDocument) throw new Error("먼저 문서를 여세요.");
    await executeEditorCommand(editor.current, "frame.create", { rect: [72, 72, 300, 150], content: "text", text });
    setEditorMessage("제안한 텍스트 상자를 추가했습니다. 위치와 내용을 확인한 뒤 저장하세요.");
  }
  async function requestTextRewrite() {
    if (!editorText.trim() || requestingText.current) return;
    requestingText.current = true;
    setIsRequestingText(true);
    try {
      setTextProposal("");
      const job = await rewriteEditorText(loaderData.projectId, editorText);
      setTextJob(job.job);
    } catch (error) {
      setEditorMessage(error instanceof Error ? error.message : "문구 제안을 요청하지 못했습니다.");
    } finally { requestingText.current = false; setIsRequestingText(false); }
  }
  const busy = useNavigation().state !== "idle";
  const attempts = [...loaderData.attempts].reverse();
  return (
    <section className="space-y-8">
      <Form method="post" className={initialAttempt ? "hidden" : "space-y-3"}>
        <h2 className="text-xl font-semibold">Compose</h2>
        <p className="text-sm text-muted-foreground">Each run makes a new numbered attempt from the saved plan. Sizes are in millimetres.</p>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {([["width_mm", "Width", 297], ["height_mm", "Height", 210], ["margin_mm", "Margin", 12], ["bleed_mm", "Bleed", 0]] as const).map(([name, label, v]) => (
            <label key={name} className="space-y-1 text-sm">
              <span>{label} (mm)</span>
              <Input type="number" step="any" name={name} defaultValue={v} />
            </label>
          ))}
        </div>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="header" defaultChecked /> running header</label>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="designcraft" /> DesignCraft 편집 파일 생성</label>
        <Button type="submit" disabled={busy}>Compose book</Button>
      </Form>

      {actionData && "error" in actionData && <p role="alert" className="text-red-400">{actionData.error}</p>}
      {actionData && "message" in actionData && <p role="status" className="text-sm">{actionData.message}</p>}
      {!editorOpen && editorMessage && <p role="status" className="text-sm">{editorMessage}</p>}
      {actionData?.job && <JobProgress key={actionData.job} jobId={actionData.job} onDone={() => revalidate()} />}
      {importJob && <JobProgress key={importJob} jobId={importJob} onDone={(job) => { if (job.status === "succeeded") { setSavedFile((current) => current?.file === submittedFile.current ? null : current); setEditorMessage("편집본을 새 시도로 가져왔습니다. Review에서 원본과 대조해 확인하세요."); } else setEditorMessage(`편집본을 가져오지 못했습니다: ${job.error ?? "작업 실패"}. 다운로드한 파일은 보존됩니다.`); revalidate(); setImportJob(null); }} />}

      {attempts.length === 0 && <p className="text-muted-foreground">No attempts yet. Save a plan, then compose.</p>}
      {!initialAttempt && attempts.map((a) => (
        <Card key={a.attempt}>
          <CardHeader className="flex-row flex-wrap items-center gap-3 space-y-0">
            <CardTitle>Attempt {a.attempt}</CardTitle>
            <Badge variant={a.gate_pass ? "default" : "destructive"}>{a.gate_pass == null ? "no gate result" : a.gate_pass ? "gates pass" : (a.blocking ?? []).some((issue) => (issue as GateItem)?.code === "NATIVE_EDIT_UNVERIFIED") ? "사람 검토 필요" : "gates fail"}</Badge>
            <Badge variant="outline">{(a.blocking ?? []).length} blocking</Badge>
            <Badge variant="outline">{(a.advisory ?? []).length} advisory</Badge>
            {a.ledger_pending && <Form method="post"><input type="hidden" name="intent" value="recover-ledger" /><input type="hidden" name="attempt" value={a.attempt} /><Button type="submit" variant="outline" disabled={busy}>저장 이력 복구</Button></Form>}
            {a.files?.["book.pdf"] && <a className="text-sm text-primary underline" href={bookUrl(loaderData.projectId, a.attempt, "pdf")}>PDF</a>}
            {a.files?.["book.pptx"] && <a className="text-sm text-primary underline" href={bookUrl(loaderData.projectId, a.attempt, "pptx")}>PPTX</a>}
            {a.files?.["book.designcraft"] && <a className="text-sm text-primary underline" href={bookUrl(loaderData.projectId, a.attempt, "designcraft")}>DesignCraft 파일 받기</a>}
            {a.files?.["book.designcraft"] && <Link className="rounded-md border px-3 py-2 text-sm" to={`/projects/${loaderData.projectId}/editor/${a.attempt}`}>웹 편집기 열기</Link>}
            {a.files?.["book.designcraft"] && <Button type="button" aria-label={`Open web editor for attempt ${a.attempt}`} variant="outline" disabled={isSending} onClick={() => void openWebEditor(a.attempt)}>인라인 편집</Button>}
            {a.files?.["book.designcraft"] && <Form method="post"><input type="hidden" name="intent" value="open-designcraft" /><input type="hidden" name="attempt" value={a.attempt} /><Button type="submit" variant="outline" disabled={busy}>DesignCraft에서 편집</Button></Form>}
          </CardHeader>
          <CardContent className="space-y-4">
            {a.native_edit && <AgentSuggestions projectId={loaderData.projectId} attempt={a.attempt} busy={busy} />}
            <GateList label="Blocking" tone="text-red-400" items={a.blocking} />
            <GateList label="Advisory" tone="text-muted-foreground" items={a.advisory} />
            {a.designcraft && <div className="rounded-md border p-3 text-sm" role="note">
              <p>DesignCraft 결과는 별도 검증되지 않았습니다. 위 게이트 결과는 기본 PDF 기준입니다.</p>
              {(a.designcraft.notes ?? []).length > 0 && <ul className="mt-2 list-disc pl-5">{a.designcraft.notes?.map((note, i) => <li key={i}>{note}</li>)}</ul>}
            </div>}
            {a.files?.["book.designcraft"] && <Form method="post" encType="multipart/form-data" className="flex flex-wrap items-center gap-2">
              <input type="hidden" name="intent" value="import-designcraft" />
              <input type="hidden" name="attempt" value={a.attempt} />
              <label className="text-sm">편집기에서 저장한 파일 <Input type="file" name="file" accept=".designcraft" required /></label>
              <Button type="submit" variant="outline" disabled={busy}>편집본을 프로젝트로 가져오기</Button>
            </Form>}
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {(a.pages ?? []).map((_, i) => (
                <img key={i} src={pageUrl(loaderData.projectId, a.attempt, i + 1)} alt={`attempt ${a.attempt} page ${i + 1}`} loading="lazy" className="w-full rounded border bg-white" />
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
      {editorOpen && <section className={initialAttempt ? "fixed inset-0 z-50 flex flex-col gap-2 bg-background p-3" : "space-y-3"} aria-label="DesignCraft 웹 편집기">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-xl font-semibold">DesignCraft 웹 편집기</h2>
          {initialAttempt && <Link className="rounded-md border px-3 py-2 text-sm" to={`/projects/${loaderData.projectId}/book`}>책으로 돌아가기</Link>}
          {initialAttempt && <Button type="button" variant="outline" onClick={() => setIsChatOpen((open) => !open)}>{isChatOpen ? "대화 닫기" : "대화 열기"}</Button>}
          <Button type="button" aria-label="Send file to web editor" variant="outline" disabled={isSending} onClick={() => pendingAttempt && void sendToEditor(pendingAttempt)}>시도 {pendingAttempt} 보내기</Button>
          {!initialAttempt && <><label className="text-sm">새 텍스트 <Input aria-label="새 텍스트" value={editorText} onChange={(event) => setEditorText(event.target.value)} /></label>
          <Button type="button" variant="outline" disabled={!editorText.trim() || isRequestingText || Boolean(textJob)} onClick={() => void requestTextRewrite()}>에이전트에 문구 제안 요청</Button>
          <Button type="button" variant="outline" disabled={!editorHasDocument || !editorText.trim() || isEditing} onClick={() => void insertTextFrame()}>텍스트 상자 추가</Button></>}
          {savedFile && <Button type="button" aria-label="Import saved DesignCraft" variant="outline" disabled={isImporting || Boolean(importJob)} onClick={() => void importSavedFile()}>시도 {savedFile.attempt} 저장본 가져오기</Button>}
          {!initialAttempt && <Button type="button" variant="outline" onClick={() => { if (window.confirm("편집 내용을 다운로드로 저장했나요? 닫으면 저장하지 않은 내용이 사라질 수 있습니다.")) { editorBridge.current?.(); editorBridge.current = null; activeAttempt.current = null; setEditorOpen(false); setEditorHasDocument(false); } }}>편집기 닫기</Button>}
        </div>
        <p role="status" className="text-sm">{editorMessage} 편집기에서 다른 파일을 직접 연 경우 저장본이 표시된 원본 시도에 속하는지 직접 확인하세요. 글꼴이 대체될 수 있습니다.</p>
        {!initialAttempt && <p className="text-sm text-muted-foreground">문구 제안을 요청하면 입력한 텍스트가 Claude 서비스로 전송됩니다. 제안은 확인 후 직접 적용합니다.</p>}
        {textJob && <JobProgress key={textJob} jobId={textJob} onDone={(job) => { const result = job.result as { text?: unknown } | null; if (job.status === "succeeded" && typeof result?.text === "string") setTextProposal(result.text); else setEditorMessage(job.error ?? "문구 제안을 받지 못했습니다."); setTextJob(null); }} />}
        {textProposal && <div className="space-y-2 rounded-md border p-3 text-sm"><p>에이전트 제안: {textProposal}</p><Button type="button" variant="outline" onClick={() => { setEditorText(textProposal); setTextProposal(""); }}>제안 사용</Button></div>}
        <div className={initialAttempt ? "flex min-h-0 flex-1 flex-col overflow-hidden rounded-md border md:flex-row" : ""}>
          <iframe ref={editor} onLoad={connectEditorSave} title="DesignCraft" src="/pascal-editor/index.html" className={initialAttempt ? "min-h-[35vh] w-full flex-1 bg-white md:min-h-0" : "h-[75vh] min-h-[600px] w-full rounded-md border bg-white"} sandbox="allow-scripts allow-same-origin allow-downloads allow-popups" />
          {initialAttempt && <EditorChatPanel projectId={loaderData.projectId} attempt={initialAttempt} canEdit={editorHasDocument} onInsert={insertChatText} isOpen={isChatOpen} />}
        </div>
      </section>}
    </section>
  );
}

export default BookWorkspace;
