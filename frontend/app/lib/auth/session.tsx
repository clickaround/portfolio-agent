import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { User } from "@supabase/supabase-js";
import { authClient } from "./client";

const SessionContext = createContext<{ user: User | null; loading: boolean }>({ user: null, loading: false });

export function SessionProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(Boolean(authClient));
  useEffect(() => {
    if (!authClient) return;
    let active = true;
    void authClient.auth.getSession().then(({ data }) => {
      if (active) { setUser(data.session?.user ?? null); setLoading(false); }
    }).catch(() => { if (active) setLoading(false); });
    const { data: { subscription } } = authClient.auth.onAuthStateChange((_event, session) => {
      if (active) { setUser(session?.user ?? null); setLoading(false); }
    });
    return () => { active = false; subscription.unsubscribe(); };
  }, []);
  return <SessionContext.Provider value={{ user, loading }}>{children}</SessionContext.Provider>;
}

export function useSession() { return useContext(SessionContext); }
