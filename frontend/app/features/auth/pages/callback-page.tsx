import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";
import { authClient } from "~/lib/auth/client";

export default function CallbackPage() {
  const navigate = useNavigate();
  const [error, setError] = useState(authClient ? "" : "로그인 연결 설정이 없습니다.");
  useEffect(() => {
    let active = true;
    if (!authClient) return;
    void authClient.auth.getSession().then(({ data, error: cause }) => {
      if (!active) return;
      if (cause || !data.session) setError(cause?.message ?? "로그인 세션을 확인하지 못했습니다.");
      else void navigate("/projects", { replace: true });
    }).catch(() => { if (active) setError("로그인을 완료하지 못했습니다."); });
    return () => { active = false; };
  }, [navigate]);
  return <div className="mx-auto max-w-md py-20">{error ? <><p role="alert">{error}</p><Link className="text-primary" to="/auth/login">로그인으로 돌아가기</Link></> : <p>로그인을 확인하고 있습니다…</p>}</div>;
}
