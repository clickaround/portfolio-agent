"""Exercise the draft with independent sessions on an isolated local database."""
import re
import subprocess
import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTAINER = "supabase_db_portfolio_agent_v3_multidomain_plugin_de"
OWNER = "10000000-0000-4000-8000-000000000001"
OTHER = "10000000-0000-4000-8000-000000000002"
PROJECT = "20000000-0000-4000-8000-000000000001"
CONVERSATION = "30000000-0000-4000-8000-000000000001"


def command(args: list[str], sql: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", "exec", "-i", CONTAINER, *args], input=sql, encoding="utf-8", text=True, capture_output=True, check=False, timeout=30)


def main() -> int:
    db = "portfolio_check_" + uuid.uuid4().hex
    if not re.fullmatch(r"portfolio_check_[0-9a-f]{32}", db):
        raise ValueError("Invalid isolated database name")
    created = command(["createdb", "-U", "postgres", db])
    if created.returncode:
        print(created.stderr, file=sys.stderr)
        return 1
    try:
        draft = (ROOT / "supabase/drafts/portfolio_conversation_foundation.sql").read_text(encoding="utf-8")
        setup = f"""
create schema if not exists auth;
create table auth.users (id uuid primary key);
create function auth.uid() returns uuid language sql stable as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$;
grant usage on schema auth to authenticated;
grant execute on function auth.uid() to authenticated;
{draft}
insert into auth.users(id) values ('{OWNER}'), ('{OTHER}');
insert into public.projects(id,owner_id,slug,title) values ('{PROJECT}','{OWNER}','test','test');
insert into public.conversations(id,project_id,created_by) values ('{CONVERSATION}','{PROJECT}','{OWNER}');
"""
        base = ["psql", "-U", "postgres", "-d", db, "-v", "ON_ERROR_STOP=1", "-A", "-t", "-q"]
        result = command(base, setup)
        if result.returncode:
            raise RuntimeError(result.stderr)

        def request(user: str, request_id: str, text: str, barrier: threading.Barrier):
            barrier.wait(timeout=20)
            sql = (f"set role authenticated; set request.jwt.claim.sub = '{user}'; "
                   f"select public.append_user_message('{CONVERSATION}', '{request_id}', '{text}');")
            return command(base, sql)

        def pair(first: tuple[str, str, str], second: tuple[str, str, str]):
            barrier = threading.Barrier(2)
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda item: request(*item, barrier), (first, second)))
            if any(x.returncode for x in results):
                raise RuntimeError("Concurrent call failed: " + " ".join(x.stderr for x in results))
            return [x.stdout.strip().splitlines()[-1] for x in results]

        same = "40000000-0000-4000-8000-000000000001"
        ids = pair((OWNER, same, "same"), (OWNER, same, "same"))
        if ids[0] != ids[1]:
            raise AssertionError("The same request produced different messages")
        if command(base, "update public.agent_runs set status = 'succeeded';").returncode:
            raise RuntimeError("Could not complete fixture run")
        barrier = threading.Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            active = list(pool.map(lambda item: request(*item, barrier),
                                   ((OWNER, "40000000-0000-4000-8000-000000000002", "next"),
                                    (OWNER, "40000000-0000-4000-8000-000000000003", "another"))))
        if sorted(x.returncode == 0 for x in active) != [False, True]:
            raise AssertionError("Concurrent distinct requests did not enforce one active run")
        if command(base, "update public.agent_runs set status = 'succeeded';").returncode:
            raise RuntimeError("Could not complete fixture run")
        barrier = threading.Barrier(2)
        conflict_key = "40000000-0000-4000-8000-000000000005"
        with ThreadPoolExecutor(max_workers=2) as pool:
            conflicts = list(pool.map(lambda item: request(*item, barrier),
                                      ((OWNER, conflict_key, "alpha"), (OWNER, conflict_key, "beta"))))
        if sorted(x.returncode == 0 for x in conflicts) != [False, True]:
            raise AssertionError("Different content with the same concurrent request ID was not rejected")
        check = command(base, "select string_agg(sequence::text, ',' order by sequence) from public.messages;")
        if check.returncode or check.stdout.strip() != "1,2,3":
            raise AssertionError("Concurrent messages have missing or duplicate sequence numbers")
        count = command(base, "select count(*) from public.agent_runs r join public.run_outbox o on o.run_id = r.id;")
        if count.returncode or count.stdout.strip() != "3":
            raise AssertionError("Messages and outbox records are not consistent")
        bad = request(OTHER, "40000000-0000-4000-8000-000000000004", "blocked", threading.Barrier(1))
        if bad.returncode == 0:
            raise AssertionError("Another user was allowed to append")
        print("Local independent-session concurrency, idempotency and ownership checks passed.")
        return 0
    except (RuntimeError, AssertionError, threading.BrokenBarrierError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        dropped = command(["dropdb", "-U", "postgres", db])
        if dropped.returncode:
            raise RuntimeError(f"Could not remove isolated test database {db}: {dropped.stderr}")


if __name__ == "__main__":
    raise SystemExit(main())
