import { useState, type FormEvent } from "react";
import { AuthPageTemplate, DuiField } from "@dk/dui";
import { GitBranch, MessageCircle } from "lucide-react";
import { Link, useNavigate } from "react-router";
import { Button } from "~/common/components/ui/button";
import { Input } from "~/common/components/ui/input";
import { authClient } from "~/lib/auth/client";
import { duiTheme } from "~/lib/dui-theme";
import { signIn, signInSocial, signUp } from "../mutations";

export default function AuthPage({ mode }: { mode: "login" | "join" }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const navigate = useNavigate();
  const joining = mode === "join";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!authClient || pending) return;
    setPending(true); setError(""); setMessage("");
    try {
      if (joining) {
        const result = await signUp(name.trim(), email.trim(), password, `${window.location.origin}/auth/callback`);
        if (result.session) void navigate("/projects");
        else setMessage("가입 확인 이메일을 보냈습니다. 이메일의 링크를 확인하세요.");
      } else {
        await signIn(email.trim(), password);
        void navigate("/projects");
      }
    } catch (cause) { setError(cause instanceof Error ? cause.message : "인증 요청에 실패했습니다."); }
    finally { setPending(false); }
  }

  async function social(provider: "github" | "kakao") {
    if (!authClient || pending) return;
    setPending(true); setError("");
    try {
      await signInSocial(provider, `${window.location.origin}/auth/callback`);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "소셜 로그인을 시작하지 못했습니다."); setPending(false); }
  }

  return <AuthPageTemplate theme={duiTheme}><section className="mx-auto flex w-full max-w-sm flex-col justify-center gap-6">
    <div><h1 className="text-3xl font-semibold tracking-tight">{joining ? "계정 만들기" : "다시 만나서 반가워요"}</h1><p className="mt-2 text-sm text-muted-foreground">Pascal에서 나만의 포트폴리오를 만들어 보세요.</p></div>
    {!authClient && <p role="status" className="rounded-lg border p-3 text-sm text-muted-foreground">로그인 연결 설정이 아직 준비되지 않았습니다.</p>}
    <form className="space-y-4" onSubmit={(event) => void submit(event)}>
      {joining && <DuiField id="name" label="이름"><Input id="name" autoComplete="name" required value={name} onChange={(event) => setName(event.target.value)} /></DuiField>}
      <DuiField id="email" label="이메일"><Input id="email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></DuiField>
      <DuiField id="password" label="비밀번호"><Input id="password" type="password" autoComplete={joining ? "new-password" : "current-password"} minLength={joining ? 8 : undefined} required value={password} onChange={(event) => setPassword(event.target.value)} /></DuiField>
      {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
      {message && <p role="status" className="text-sm text-muted-foreground">{message}</p>}
      <Button className="w-full" disabled={!authClient || pending} type="submit">{joining ? "회원가입" : "로그인"}</Button>
    </form>
    <div className="space-y-2"><p className="py-1 text-center text-xs text-muted-foreground">또는 계속하기</p>
      <Button type="button" variant="outline" className="w-full" disabled={!authClient || pending} onClick={() => void social("github")}><GitBranch className="size-4" /> GitHub</Button>
      <Button type="button" variant="outline" className="w-full" disabled={!authClient || pending} onClick={() => void social("kakao")}><MessageCircle className="size-4" /> Kakao</Button>
    </div>
    <p className="text-center text-sm text-muted-foreground">{joining ? "이미 계정이 있나요?" : "처음이신가요?"} <Link className="text-primary hover:underline" to={joining ? "/auth/login" : "/auth/join"}>{joining ? "로그인" : "회원가입"}</Link></p>
    <p className="text-xs text-muted-foreground">프로젝트 접근 보호는 연결된 서버의 인증 설정에 따라 적용됩니다.</p>
  </section></AuthPageTemplate>;
}
