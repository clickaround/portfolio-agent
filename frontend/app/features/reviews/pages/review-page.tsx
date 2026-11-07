import { Form, useNavigation } from "react-router";
import { Badge } from "~/common/components/ui/badge";
import { Button } from "~/common/components/ui/button";
import { Input } from "~/common/components/ui/input";
import { ApiError } from "~/lib/api/client";
import { assetUrl, bookUrl, pageUrl } from "~/lib/api/urls";
import { bindReviewContext, finalizeBook, recordReview } from "../mutations";
import { buildReview, DIMENSIONS, pageNumber, REVIEWER_MODES, type ReviewContext } from "../schema";
import type { Route } from "./+types/review-page";

export const meta: Route.MetaFunction = () => [{ title: "Review | Pascal" }];

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return { projectId: params.projectId };
}

const lines = (v: FormDataEntryValue | null) => String(v ?? "").split("\n").map((s) => s.trim()).filter(Boolean);

type Outcome = { context?: ReviewContext; error?: string; message?: string; result?: unknown };

export async function clientAction({ request, params }: Route.ClientActionArgs): Promise<Outcome> {
  const form = await request.formData();
  const intent = String(form.get("intent"));
  const pid = params.projectId;
  const context = JSON.parse(String(form.get("context") ?? "null")) as ReviewContext | null; // echoed back so the forms survive errors
  try {
    if (intent === "context") return { context: (await bindReviewContext(pid)) as unknown as ReviewContext };
    if (intent === "finalize") return { context: context ?? undefined, message: "Finalize", result: await finalizeBook(pid) };
    if (!context) return { error: "Bind the review context first." };
    const reviewedFrames = form.getAll("reviewed_frame").map(String);
    const frames = Object.keys(context.frames);
    if (!frames.length || frames.some((frame) => !reviewedFrames.includes(frame)) || reviewedFrames.some((frame) => !frames.includes(frame))) {
      return { error: "Confirm every page before recording the review.", context };
    }
    const scores = Object.fromEntries(DIMENSIONS.map((d) => [d, Number(form.get(`score_${d}`))]));
    const confirmationKeys = ["reviewed_exported_pages", "content_and_source_fidelity_confirmed", "page_geometry_and_clipping_confirmed"];
    if (context.native_edit && (form.get("mode") !== "human" || confirmationKeys.some((key) => form.get(key) !== "on"))) {
      return { error: "편집본은 사람이 출력 페이지와 원본 정확성, 페이지 크기와 잘림을 모두 확인해야 합니다.", context };
    }
    const nativeConfirmation = context.native_edit ? Object.fromEntries(confirmationKeys.map((key) => [key, true])) : undefined;
    const review = buildReview(context, { mode: String(form.get("mode")), scores, blockers: lines(form.get("blockers")), issues: lines(form.get("issues")), reviewedFrames, nativeConfirmation });
    return { context, message: "Review recorded", result: await recordReview(pid, review) };
  } catch (e) {
    if (e instanceof ApiError) return { error: e.message, context: context ?? undefined };
    throw e;
  }
}

export default function ReviewPage({ loaderData, actionData }: Route.ComponentProps) {
  const busy = useNavigation().state !== "idle";
  const ctx = actionData?.context;
  return (
    <section className="space-y-6">
      <p className="text-sm text-muted-foreground">
        1. Bind the latest attempt. 2. An independent reviewer scores every page. 3. Finalize requires a passing review. Edited DesignCraft files also require explicit human checks; all other blocking issues still prevent finalization.
      </p>
      <Form method="post">
        <Button type="submit" name="intent" value="context" variant="outline" disabled={busy}>1. Bind review context</Button>
      </Form>

      {actionData?.error && <p role="alert" className="text-red-400">{actionData.error}</p>}

      {ctx && (
        <>
          <Form method="post" className="space-y-4" key={ctx.review_context_sha256}>
            <input type="hidden" name="intent" value="record" />
            <input type="hidden" name="context" value={JSON.stringify(ctx)} />
          <div className="space-y-3">
            <div className="flex items-center gap-2"><h2 className="text-xl font-semibold">Attempt {ctx.attempt}</h2><Badge variant="outline">{Object.keys(ctx.frames).length} frames</Badge></div>
            {ctx.native_edit && <div className="space-y-2 rounded-md border p-3 text-sm">
              <p>기준 시도: {ctx.native_edit.parent_attempt ?? "알 수 없음"}. 편집 파일이 해당 시도에서 파생됐는지는 자동으로 증명되지 않으므로 원본과 직접 대조하세요.</p>
              <a className="mr-4 underline" target="_blank" rel="noreferrer" href={bookUrl(loaderData.projectId, ctx.attempt, "pdf")}>편집된 PDF 열기</a>
              {ctx.native_edit.parent_attempt && <a className="underline" target="_blank" rel="noreferrer" href={bookUrl(loaderData.projectId, ctx.native_edit.parent_attempt, "pdf")}>기준 시도의 PDF 열기</a>}
              <p>원본 해시 상태: {ctx.native_edit.source_evidence?.status ?? "unverified"}</p>
              {(ctx.native_edit.source_evidence?.assets ?? []).length > 0 && <details><summary>원본 파일과 기록된 해시</summary><ul className="space-y-1">{ctx.native_edit.source_evidence?.assets?.map((asset) => <li key={asset.path}><a className="underline" target="_blank" rel="noreferrer" href={assetUrl(loaderData.projectId, asset.path)}>{asset.path}</a> <span className="break-all font-mono text-xs">{asset.sha256}</span></li>)}</ul></details>}
            </div>}
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {Object.keys(ctx.frames).map((f) => (
                <div key={f} className="space-y-2 text-sm">
                  <a href={pageUrl(loaderData.projectId, ctx.attempt, pageNumber(f))} target="_blank" rel="noreferrer"><img src={pageUrl(loaderData.projectId, ctx.attempt, pageNumber(f))} alt={f} loading="lazy" className="w-full rounded border bg-white" /></a>
                  <label className="flex items-center gap-2"><input type="checkbox" name="reviewed_frame" value={f} required /> I reviewed {f}</label>
                </div>
              ))}
            </div>
          </div>

            <h2 className="text-xl font-semibold">2. Score (0 to 1)</h2>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {DIMENSIONS.map((d) => (
                <label key={d} className="space-y-1 text-sm">
                  <span>{d.replaceAll("_", " ")}</span>
                  <Input type="number" name={`score_${d}`} min={0} max={1} step={0.05} defaultValue={0.7} required />
                </label>
              ))}
            </div>
            <label className="block space-y-1 text-sm">
              <span>Reviewer</span>
              <select name="mode" className="h-9 rounded-md border bg-background px-2 text-sm">{(ctx.native_edit ? ["human"] : REVIEWER_MODES).map((m) => <option key={m} value={m}>{m}</option>)}</select>
            </label>
            {ctx.native_edit && <fieldset className="space-y-2 rounded-md border p-3 text-sm">
              <legend>편집본 직접 확인</legend>
              <label className="flex gap-2"><input type="checkbox" name="reviewed_exported_pages" required /> 편집된 PDF의 모든 페이지를 확인했습니다.</label>
              <label className="flex gap-2"><input type="checkbox" name="content_and_source_fidelity_confirmed" required /> 원본 자료와 대조해 내용과 출처가 정확한지 확인했습니다.</label>
              <label className="flex gap-2"><input type="checkbox" name="page_geometry_and_clipping_confirmed" required /> 페이지 크기와 잘림·겹침을 확인했습니다.</label>
            </fieldset>}
            <label className="block space-y-1 text-sm">
              <span>Blockers (one per line; any blocker fails the review)</span>
              <textarea name="blockers" rows={3} className="w-full rounded-md border bg-background p-2 text-sm" />
            </label>
            <label className="block space-y-1 text-sm">
              <span>Issues (one per line)</span>
              <textarea name="issues" rows={3} className="w-full rounded-md border bg-background p-2 text-sm" />
            </label>
            <Button type="submit" variant="outline" disabled={busy}>Record review</Button>
          </Form>

          <Form method="post">
            <input type="hidden" name="intent" value="finalize" />
            <input type="hidden" name="context" value={JSON.stringify(ctx)} />
            <Button type="submit" disabled={busy}>3. Finalize</Button>
          </Form>
        </>
      )}

      {actionData?.message && (
        <div className="space-y-1">
          <h2 className="font-semibold">{actionData.message}</h2>
          <pre className="max-h-96 overflow-auto rounded-md border p-3 text-xs">{JSON.stringify(actionData.result, null, 1)}</pre>
        </div>
      )}
    </section>
  );
}
