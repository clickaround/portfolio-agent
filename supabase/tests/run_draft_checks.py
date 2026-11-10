"""Run draft and RLS checks in one rollback-only transaction on the local DB.

Requires `supabase start`; never accepts a remote connection string. Test
identities are inserted only inside the transaction and are rolled back.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTAINER = "supabase_db_portfolio_agent_v3_multidomain_plugin_de"
DRAFT = ROOT / "supabase/drafts/portfolio_conversation_foundation.sql"
TEST = ROOT / "supabase/tests/portfolio_rls.sql"


def main() -> int:
    test = TEST.read_text(encoding="utf-8")
    if test.count("BEGIN;") != 1 or test.count("ROLLBACK;") != 1:
        raise ValueError("Expected exactly one test transaction")
    test = test.replace("BEGIN;", "", 1).replace("ROLLBACK;", "", 1)
    fixture = """
insert into auth.users (id, email) values
 ('10000000-0000-4000-8000-000000000001', 'portfolio-test-a@example.invalid'),
 ('10000000-0000-4000-8000-000000000002', 'portfolio-test-b@example.invalid');
select set_config('test.user_a', '10000000-0000-4000-8000-000000000001', true);
select set_config('test.user_b', '10000000-0000-4000-8000-000000000002', true);
"""
    sql = "BEGIN;\n" + DRAFT.read_text(encoding="utf-8") + "\n" + fixture + test + "\nROLLBACK;\n"
    result = subprocess.run(
        ["docker", "exec", "-i", CONTAINER, "psql", "-U", "postgres", "-d", "postgres", "-v", "ON_ERROR_STOP=1"],
        input=sql, text=True, encoding="utf-8", capture_output=True, check=False,
    )
    if result.returncode:
        print(result.stderr, file=sys.stderr)
        return result.returncode
    if "ROLLBACK" not in result.stdout:
        print("Expected transaction rollback was not observed", file=sys.stderr)
        return 1
    print("Local draft, two-user RLS and idempotency checks passed; transaction rolled back.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
