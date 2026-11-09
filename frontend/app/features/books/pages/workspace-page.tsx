import { useCallback, useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { Link, useBeforeUnload, useBlocker, useNavigate, type BlockerFunction } from "react-router";
import { JobProgress } from "~/common/components/job-progress";
import { Button } from "~/common/components/ui/button";
import { uploadProjectAsset, type AssetKind } from "~/lib/api/assets";
import { generatePortfolio } from "../mutations";
import { getAttempts, getWorkspaceProject } from "../queries";
import { ResizableEditorSplit } from "../resizable-editor-split";
import { executeEditorCommand } from "../editor-command";
import type { Route } from "./+types/workspace-page";

export const meta: Route.MetaFunction = () => [{ title: "에이전트 작업 공간 | Pascal" }];

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  const [project, attempts] = await Promise.all([getWorkspaceProject(params.projectId), getAttempts(params.projectId)]);
  const existingAttempt = [...attempts].reverse().find((item) => item.files?.["book.designcraft"])?.attempt;
  return { projectId: params.projectId, title: project.title || project.id, existingAttempt };
}

const formats = {
  a4_landscape: { label: "A4 가로", width_mm: 297, height_mm: 210 },
  a4_portrait: { label: "A4 세로", width_mm: 210, height_mm: 297 },
  a3_landscape: { label: "A3 가로", width_mm: 420, height_mm: 297 },
} as const;

export function GenerationWorkspace({ projectId, title, existingAttempt }: { projectId: string; title: string; existingAttempt?: string }) {
  const navigate = useNavigate();
  const editor = useRef<HTMLIFrameElement>(null);
  const allowNavigation = useRef(false);
  const blocker = useBlocker(useCallback<BlockerFunction>(({ currentLocation, nextLocation }) =>
    !allowNavigation.current && currentLocation.pathname !== nextLocation.pathname, []));
  useBeforeUnload(useCallback((event) => { if (!allowNavigation.current) { event.preventDefault(); event.returnValue = ""; } }, []));
  useEffect(() => {
    if (blocker.state === "blocked") {
      if (window.confirm("편집기에 저장하지 않은 내용이 있다면 사라질 수 있습니다. 이동할까요?")) blocker.proceed();
      else blocker.reset();
    }
  }, [blocker]);
  const storageKey = `pascal:portfolio-job:${projectId}`;
  const readyKey = `pascal:portfolio-ready:${projectId}`;
  const requestKey = `pascal:portfolio-request:${projectId}`;
  const [instructions, setInstructions] = useState("");
  const [submitted, setSubmitted] = useState(() => {
    try { return window.sessionStorage.getItem(requestKey) || ""; } catch { return ""; }
  });
  const [format, setFormat] = useState<keyof typeof formats>("a4_landscape");
  const [assetKind, setAssetKind] = useState<AssetKind>("images");
  const [files, setFiles] = useState<File[]>([]);
  const [fileKey, setFileKey] = useState(0);
  const [uploaded, setUploaded] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isStarting, setIsStarting] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState("");
  const [ready, setReady] = useState<{ attempt: string; confirm: boolean } | null>(() => {
    try {
      const attempt = window.sessionStorage.getItem(readyKey);
      return attempt && /^\d{2}$/.test(attempt) ? { attempt, confirm: true } : null;
    } catch { return null; }
  });
  const [job, setJob] = useState<string | null>(() => {
    try { return window.sessionStorage.getItem(storageKey); } catch { return null; }
  });
  const starting = useRef(false);
  const uploading = useRef(false);
  const busy = isStarting || isUploading || isChecking || Boolean(job);

  function pickFiles(event: ChangeEvent<HTMLInputElement>) {
    setFiles(Array.from(event.target.files ?? []));
    setUploaded("");
  }

  async function uploadFiles() {
    if (!files.length || uploading.current || busy) return;
    uploading.current = true; setIsUploading(true); setError(""); setUploaded("");
    let count = 0;
    try {
      for (const file of files) { await uploadProjectAsset(projectId, assetKind, file); count += 1; }
      setFiles([]); setFileKey((value) => value + 1);
      setUploaded(`${count}개 자료를 프로젝트에 추가했습니다.`);
    } catch (cause) {
      setFiles((current) => current.slice(count));
      setUploaded(count ? `${count}개 자료는 업로드됐습니다.` : "");
      setError(cause instanceof Error ? cause.message : "자료를 업로드하지 못했습니다.");
    } finally { uploading.current = false; setIsUploading(false); }
  }

  async function start(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = instructions.trim();
    if (!text || starting.current || busy) return;
    starting.current = true; setIsStarting(true); setError("");
    try {
      const result = await generatePortfolio(projectId, { instructions: text, ...formats[format] });
      setSubmitted(text);
      setJob(result.job);
      try { window.sessionStorage.setItem(storageKey, result.job); window.sessionStorage.setItem(requestKey, text); } catch { /* job still runs */ }
    } catch (cause) { setError(cause instanceof Error ? cause.message : "포트폴리오 작업을 시작하지 못했습니다."); }
    finally { starting.current = false; setIsStarting(false); }
  }

  async function complete(finished: { status: string; result?: unknown; error?: string | null }) {
    if (finished.status !== "succeeded") {
      setJob(null);
      try { window.sessionStorage.removeItem(storageKey); } catch { /* storage unavailable */ }
      setError(finished.error || "포트폴리오 생성에 실패했습니다.");
      return;
    }
    setIsChecking(true);
    try {
      const result = finished.result as { compose?: { attempt?: unknown } } | null;
      const attempt = result?.compose?.attempt;
      if (typeof attempt !== "string" || !/^\d{2}$/.test(attempt)) throw new Error("생성된 시도를 확인하지 못했습니다. 책 화면에서 작업 결과를 확인하세요.");
      const attempts = await getAttempts(projectId);
      if (!attempts.some((item) => item.attempt === attempt && item.files?.["book.designcraft"])) {
        throw new Error("편집 가능한 결과 파일을 확인하지 못했습니다. 책 화면에서 생성 결과와 오류를 확인하세요.");
      }
      let opened = true;
      let dirty = true;
      try {
        if (!editor.current) throw new Error("편집기 상태를 확인할 수 없습니다.");
        const snapshot = await executeEditorCommand(editor.current, "document.inspect", {});
        if (!snapshot || typeof snapshot !== "object" || typeof (snapshot as { dirty?: unknown }).dirty !== "boolean") throw new Error("편집기 상태를 확인할 수 없습니다.");
        dirty = (snapshot as { dirty: boolean }).dirty;
      } catch (cause) {
        if (cause instanceof Error && (cause.message === "no document open" || cause.message.endsWith(": no document open") || cause.message === "no active document")) { opened = false; dirty = false; }
      }
      try { window.sessionStorage.removeItem(storageKey); } catch { /* storage unavailable */ }
      try { window.sessionStorage.removeItem(readyKey); } catch { /* storage unavailable */ }
      setJob(null);
      if (opened) {
        try { window.sessionStorage.setItem(readyKey, attempt); } catch { /* result is still in the book */ }
        setReady({ attempt, confirm: dirty });
      }
      else {
        try { window.sessionStorage.removeItem(requestKey); } catch { /* storage unavailable */ }
        allowNavigation.current = true;
        void navigate(`/projects/${encodeURIComponent(projectId)}/editor/${attempt}`, { state: { generationPrompt: submitted } });
      }
    } catch (cause) {
      setJob(null);
      try { window.sessionStorage.removeItem(storageKey); } catch { /* storage unavailable */ }
      setError(cause instanceof Error ? cause.message : "생성 결과를 확인하지 못했습니다.");
    } finally { setIsChecking(false); }
  }

  function openReady() {
    if (!ready) return;
    if (ready.confirm && !window.confirm("편집기의 현재 문서에 저장하지 않은 내용이 있을 수 있습니다. 생성된 결과를 열까요?")) return;
    try { window.sessionStorage.removeItem(readyKey); window.sessionStorage.removeItem(requestKey); } catch { /* storage unavailable */ }
    allowNavigation.current = true;
    void navigate(`/projects/${encodeURIComponent(projectId)}/editor/${ready.attempt}`, { state: { generationPrompt: submitted } });
  }

  return <section className="fixed inset-0 top-14 z-50 flex flex-col bg-background md:left-[var(--sidebar-width)] md:top-0" aria-label="에이전트 작업 공간">
    <ResizableEditorSplit isOpen flush panel={<aside className="flex h-full min-h-0 flex-col bg-background" aria-label="포트폴리오 만들기">
      <header className="border-b px-5 py-4"><h1 className="font-semibold">{title}</h1><p className="mt-1 text-xs text-muted-foreground">에이전트와 포트폴리오 만들기</p></header>
      <div className="flex-1 space-y-4 overflow-auto p-4">
        <p className="text-sm text-muted-foreground">자료를 추가하고 포트폴리오의 용도, 강조할 내용과 원하는 분위기를 알려 주세요.</p>
        <div className="space-y-2 rounded-lg border p-3">
          <label htmlFor="asset-kind" className="text-sm">자료 종류</label>
          <select id="asset-kind" className="w-full rounded-md border bg-background p-2 text-sm" value={assetKind} disabled={busy} onChange={(event) => setAssetKind(event.target.value as AssetKind)}>
            <option value="images">사진·이미지</option><option value="drawings">도면</option><option value="diagrams">다이어그램</option>
          </select>
          <input key={fileKey} type="file" multiple accept=".png,.jpg,.jpeg,.tif,.tiff,.webp,.svg,.pdf" aria-label="자료 선택" disabled={busy} onChange={pickFiles} className="w-full text-xs" />
          <Button type="button" size="sm" variant="outline" disabled={busy || files.length === 0} onClick={() => void uploadFiles()}>자료 추가</Button>
        {files.length > 0 && <p className="text-xs text-muted-foreground">선택한 자료 {files.length}개를 먼저 추가해 주세요.</p>}
          {uploaded && <p role="status" className="text-xs text-muted-foreground">{uploaded}</p>}
          <Link to={`/projects/${encodeURIComponent(projectId)}/sources`} className="block text-xs text-primary">프로젝트 자료 전체 보기</Link>
        </div>
        {submitted && <div className="ml-6 rounded-2xl bg-muted p-3 text-sm whitespace-pre-wrap">{submitted}</div>}
        {job && <JobProgress key={job} jobId={job} onError={(message) => { setJob(null); try { window.sessionStorage.removeItem(storageKey); } catch { /* storage unavailable */ } setError(message); }} onDone={(finished) => { void complete(finished); }} />}
        {isChecking && <p role="status" className="text-sm text-muted-foreground">편집 가능한 결과를 확인하고 있습니다…</p>}
        {ready && <div className="space-y-2 rounded-lg border p-3"><p className="text-sm">생성 결과가 준비됐습니다. 현재 편집기를 확인한 후 열어 주세요.</p><Button type="button" size="sm" onClick={openReady}>생성 결과 열기</Button></div>}
        {!ready && existingAttempt && <Link to={`/projects/${encodeURIComponent(projectId)}/editor/${encodeURIComponent(existingAttempt)}`} className="inline-block text-sm text-primary">기존 편집본 {existingAttempt} 열기</Link>}
        {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
      </div>
      <form className="space-y-3 border-t p-3" onSubmit={(event) => void start(event)}>
        <label htmlFor="portfolio-format" className="text-xs text-muted-foreground">페이지 크기</label>
        <select id="portfolio-format" value={format} disabled={busy} className="ml-2 rounded-md border bg-background p-1 text-sm" onChange={(event) => setFormat(event.target.value as keyof typeof formats)}>
          {Object.entries(formats).map(([id, value]) => <option key={id} value={id}>{value.label}</option>)}
        </select>
        <label htmlFor="portfolio-instructions" className="sr-only">포트폴리오 요청</label>
        <textarea id="portfolio-instructions" className="min-h-24 w-full resize-y rounded-xl border bg-card p-3 text-sm" maxLength={4000} value={instructions} disabled={busy} onChange={(event) => setInstructions(event.target.value)} placeholder="예: 건축 취업용으로 도면과 사진을 균형 있게 구성해 줘" />
        <p className="text-xs text-muted-foreground">요청과 프로젝트 자료는 계획 생성을 위해 Claude에 전달될 수 있습니다. 결과는 검토가 필요합니다.</p>
        <Button type="submit" className="w-full" disabled={busy || files.length > 0 || !instructions.trim()}>포트폴리오 만들기</Button>
      </form>
    </aside>} editor={<iframe ref={editor} title="DesignCraft" src="/pascal-editor/index.html" className="h-full w-full bg-background" sandbox="allow-scripts allow-same-origin allow-downloads allow-popups" />} />
  </section>;
}

export default function WorkspacePage({ loaderData }: Route.ComponentProps) {
  return <GenerationWorkspace projectId={loaderData.projectId} title={loaderData.title} existingAttempt={loaderData.existingAttempt} />;
}
