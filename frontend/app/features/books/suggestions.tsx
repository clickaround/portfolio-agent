import { useCallback, useEffect, useState } from "react";
import { useRef } from "react";
import { Form } from "react-router";
import { Button } from "~/common/components/ui/button";

type Suggestion = { suggestion_id: string; created_at: string; status: "fresh" | "stale"; source_kind: string };
type Detail = { text_truncated: boolean; output: { summary: string; pages: { page: number; suggestions: { issue: string; recommendation: string; evidence: string }[] }[] } };

/** Explicit opt-in: only extracted text and source references are sent for agent analysis. */
export function AgentSuggestions({ projectId, attempt, busy }: { projectId: string; attempt: string; busy: boolean }) {
  const [items, setItems] = useState<Suggestion[]>([]);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState("");
  const requestVersion = useRef(0);
  const base = `${import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"}/projects/${encodeURIComponent(projectId)}/attempts/${encodeURIComponent(attempt)}/suggestions`;
  const refresh = useCallback(async () => {
    requestVersion.current++;
    setDetail(null);
    try {
      const response = await authenticatedFetch(base);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      setItems(await response.json() as Suggestion[]);
      setError("");
    } catch (e) { setError(e instanceof Error ? e.message : "제안을 불러오지 못했습니다."); }
  }, [base]);
  useEffect(() => {
    let cancelled = false;
    authenticatedFetch(base).then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json() as Promise<Suggestion[]>;
    }).then((data) => { if (!cancelled) { setItems(data); setError(""); } })
      .catch((e: unknown) => { if (!cancelled) setError(e instanceof Error ? e.message : "제안을 불러오지 못했습니다."); });
    return () => { cancelled = true; };
  }, [base]);
  async function openSuggestion(id: string) {
    const version = ++requestVersion.current;
    setDetail(null);
    try {
      const response = await authenticatedFetch(`${base}/${encodeURIComponent(id)}`);
      if (!response.ok) throw new Error(response.status === 409 ? "원본이 변경되어 이 제안은 만료되었습니다." : `HTTP ${response.status}`);
      const result = await response.json() as Detail;
      if (version === requestVersion.current) { setDetail(result); setError(""); }
    } catch (e) { if (version === requestVersion.current) { setDetail(null); setError(e instanceof Error ? e.message : "제안을 불러오지 못했습니다."); } }
  }
  return <section className="space-y-3 rounded-md border p-3">
    <h3 className="font-semibold">포트폴리오 에이전트 제안</h3>
    <p className="text-sm text-muted-foreground">요청하면 편집된 PDF의 추출 텍스트, 지시사항과 소스 경로·해시가 Claude 서비스로 전송됩니다. 이미지는 전송하지 않으므로 시각 품질이나 원본 일치 여부는 확인할 수 없습니다. 제안은 자동 적용되지 않습니다.</p>
    <Form method="post" className="space-y-2">
      <input type="hidden" name="intent" value="suggest-designcraft" /><input type="hidden" name="attempt" value={attempt} />
      <label className="block text-sm">요청사항 <textarea className="block w-full rounded border p-2" name="instructions" maxLength={4000} /></label>
      <label className="block text-sm">자료 구분 <select className="rounded border p-1" name="source_kind" defaultValue="unknown"><option value="unknown">미확인</option><option value="synthetic">합성 자료</option><option value="real">실제 자료</option></select></label>
      <Button type="submit" disabled={busy}>에이전트에 제안 요청</Button>
    </Form>
    <Button type="button" variant="outline" onClick={() => void refresh()}>제안 목록 새로고침</Button>
    {error && <p role="alert" className="text-sm text-red-500">{error}</p>}
    {items.map((item) => <div className="flex flex-wrap items-center gap-2 text-sm" key={item.suggestion_id}><span>{item.created_at} · {item.source_kind} · {item.status === "fresh" ? "현재" : "만료"}</span><Button type="button" variant="outline" disabled={item.status === "stale"} onClick={() => void openSuggestion(item.suggestion_id)}>보기</Button></div>)}
    {detail && <div className="space-y-2 text-sm">{detail.text_truncated && <p role="alert">문서가 길어 텍스트 일부만 분석했습니다. 뒤쪽 내용이 빠졌을 수 있습니다.</p>}<p>{detail.output.summary}</p>{detail.output.pages.map((page) => <div key={page.page}><strong>페이지 {page.page}</strong><ul className="list-disc pl-5">{page.suggestions.map((suggestion, i) => <li key={i}>{suggestion.issue} — {suggestion.recommendation} ({suggestion.evidence})</li>)}</ul></div>)}</div>}
  </section>;
}
import { authenticatedFetch } from "~/lib/auth/fetch";
