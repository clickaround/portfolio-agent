import { authClient } from "~/lib/auth/client";

function client() {
  if (!authClient) throw new Error("로그인 연결 설정이 없습니다.");
  return authClient;
}

export async function signIn(email: string, password: string) {
  const result = await client().auth.signInWithPassword({ email, password });
  if (result.error) throw result.error;
  return result.data;
}

export async function signUp(name: string, email: string, password: string, emailRedirectTo: string) {
  const result = await client().auth.signUp({ email, password, options: { data: { name }, emailRedirectTo } });
  if (result.error) throw result.error;
  return result.data;
}

export async function signInSocial(provider: "github" | "kakao", redirectTo: string) {
  const result = await client().auth.signInWithOAuth({ provider, options: { redirectTo } });
  if (result.error) throw result.error;
}
