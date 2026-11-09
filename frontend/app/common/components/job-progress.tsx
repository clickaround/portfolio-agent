import { useEffect, useState } from "react";
import { getJob } from "~/lib/api/jobs";
import { ApiError } from "~/lib/api/client";
import { Badge } from "./ui/badge";

type Job = Awaited<ReturnType<typeof getJob>>;

/** Polls a backend job until it finishes, shows its status and log, then calls onDone once (pages use it to revalidate their loaders). */
export function JobProgress({ jobId, onDone, onError, compact = false, progressLabel = "답변을 작성하고 있습니다…" }: { jobId: string; onDone?: (job: Job) => void; onError?: (message: string) => void; compact?: boolean; progressLabel?: string }) {
  const [job, setJob] = useState<Job | null>(null);
  const [failure, setFailure] = useState<string | null>(null);

  useEffect(() => {
    let stop = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      try {
        const j = await getJob(jobId);
        if (stop) return;
        setJob(j);
        setFailure(null);
        if (j.status === "succeeded" || j.status === "failed") {
          onDone?.(j);
          return;
        }
      } catch (e) {
        if (!stop) setFailure(e instanceof Error ? e.message : "job lookup failed");
        if (stop) return;
        if (e instanceof ApiError && e.status >= 400 && e.status < 500) { onError?.(e.message); return; }
      }
      timer = setTimeout(tick, 1500);
    };
    void tick();
    return () => {
      stop = true;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- poll once per job id
  }, [jobId]);

  if (failure) return <p role="alert" className="text-sm text-red-400">{failure}</p>;
  if (compact) return <p className="text-sm text-muted-foreground" role="status">{progressLabel}</p>;
  return (
    <div className="space-y-2 rounded-md border p-3 text-sm" aria-live="polite">
      <div className="flex items-center gap-2">
        <Badge variant={job?.status === "failed" ? "destructive" : "secondary"}>{job?.status ?? "queued"}</Badge>
        <span className="text-muted-foreground">{job?.kind ?? "job"} · {jobId}</span>
      </div>
      {job?.error && <p role="alert" className="text-red-400">{job.error}</p>}
      {job?.log?.length ? <pre className="max-h-40 overflow-auto text-xs text-muted-foreground">{job.log.join("\n")}</pre> : null}
    </div>
  );
}
