import { Form, useNavigation, useRevalidator } from "react-router";
import { JobProgress } from "~/common/components/job-progress";
import { Badge } from "~/common/components/ui/badge";
import { Button } from "~/common/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "~/common/components/ui/card";
import { Input } from "~/common/components/ui/input";
import { ApiError } from "~/lib/api/client";
import { bookUrl, pageUrl } from "~/lib/api/urls";
import { composeBook } from "../mutations";
import { getAttempts } from "../queries";
import type { Route } from "./+types/book-page";

export const meta: Route.MetaFunction = () => [{ title: "Book | Pascal" }];

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return { projectId: params.projectId, attempts: await getAttempts(params.projectId) };
}

export async function clientAction({ request, params }: Route.ClientActionArgs) {
  const f = await request.formData();
  const num = (k: string, d: number) => (Number.isFinite(Number(f.get(k))) && f.get(k) !== "" ? Number(f.get(k)) : d);
  try {
    const out = await composeBook(params.projectId, {
      width_mm: num("width_mm", 297),
      height_mm: num("height_mm", 210),
      margin_mm: num("margin_mm", 12),
      bleed_mm: num("bleed_mm", 0),
      header: f.get("header") === "on",
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

export default function BookPage({ loaderData, actionData }: Route.ComponentProps) {
  const { revalidate } = useRevalidator();
  const busy = useNavigation().state !== "idle";
  const attempts = [...loaderData.attempts].reverse();
  return (
    <section className="space-y-8">
      <Form method="post" className="space-y-3">
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
        <Button type="submit" disabled={busy}>Compose book</Button>
      </Form>

      {actionData && "error" in actionData && <p role="alert" className="text-red-400">{actionData.error}</p>}
      {actionData?.job && <JobProgress key={actionData.job} jobId={actionData.job} onDone={() => revalidate()} />}

      {attempts.length === 0 && <p className="text-muted-foreground">No attempts yet. Save a plan, then compose.</p>}
      {attempts.map((a) => (
        <Card key={a.attempt}>
          <CardHeader className="flex-row flex-wrap items-center gap-3 space-y-0">
            <CardTitle>Attempt {a.attempt}</CardTitle>
            <Badge variant={a.gate_pass ? "default" : "destructive"}>{a.gate_pass == null ? "no gate result" : a.gate_pass ? "gates pass" : "gates fail"}</Badge>
            <Badge variant="outline">{(a.blocking ?? []).length} blocking</Badge>
            <Badge variant="outline">{(a.advisory ?? []).length} advisory</Badge>
            {a.files?.["book.pdf"] && <a className="text-sm text-primary underline" href={bookUrl(loaderData.projectId, a.attempt, "pdf")}>PDF</a>}
            {a.files?.["book.pptx"] && <a className="text-sm text-primary underline" href={bookUrl(loaderData.projectId, a.attempt, "pptx")}>PPTX</a>}
          </CardHeader>
          <CardContent className="space-y-4">
            <GateList label="Blocking" tone="text-red-400" items={a.blocking} />
            <GateList label="Advisory" tone="text-muted-foreground" items={a.advisory} />
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {(a.pages ?? []).map((_, i) => (
                <img key={i} src={pageUrl(loaderData.projectId, a.attempt, i + 1)} alt={`attempt ${a.attempt} page ${i + 1}`} loading="lazy" className="w-full rounded border bg-white" />
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </section>
  );
}
