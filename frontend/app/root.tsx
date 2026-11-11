import { useState, type CSSProperties } from "react";
import { isRouteErrorResponse, Links, Meta, Outlet, Scripts, ScrollRestoration, useLocation, useNavigation } from "react-router";
import "@dk/dui/styles.css";
import { duiThemeStyle } from "@dk/dui";
import type { Route } from "./+types/root";
import stylesheet from "./app.css?url";
import Navigation from "./common/components/navigation";
import { LandingNavigation } from "./common/components/landing-navigation";
import { cn } from "./lib/utils";
import { SessionProvider } from "./lib/auth/session";
import { duiTheme } from "./lib/dui-theme";

export const links: Route.LinksFunction = () => [
  { rel: "preconnect", href: "https://fonts.googleapis.com" },
  { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
  { rel: "stylesheet", href: "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap" },
  { rel: "icon", href: "/favicon.ico" },
  { rel: "stylesheet", href: stylesheet },
];

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" className="dark" style={duiThemeStyle(duiTheme)}>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
      </head>
      <body>
        <main>{children}</main>
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  const navigation = useNavigation();
  const isLoading = navigation.state === "loading";
  const pathname = useLocation().pathname;
  const isAuth = pathname.startsWith("/auth/");
  const isHome = pathname === "/";
  const [collapsed, setCollapsed] = useState(false);
  return (
    <SessionProvider><div style={{ "--sidebar-width": collapsed ? "4rem" : "15rem" } as CSSProperties}>
      {isHome ? <LandingNavigation /> : !isAuth && <Navigation collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} />}
      <div className={cn(isHome ? "px-5 pb-10 pt-28 md:px-20 md:pt-40" : !isAuth && "px-5 pb-10 pt-20 md:pl-[calc(var(--sidebar-width)+2rem)] md:pr-8 md:pt-10", { "animate-pulse transition-opacity": isLoading })}>
        <Outlet />
      </div>
    </div></SessionProvider>
  );
}

export function HydrateFallback() {
  return <p className="p-6 text-muted-foreground">Loading…</p>;
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let message = "Oops!";
  let details = "An unexpected error occurred.";
  if (isRouteErrorResponse(error)) {
    message = error.status === 404 ? "404" : "Error";
    details = error.status === 404 ? "The requested page could not be found." : error.statusText || details;
  } else if (error instanceof Error) {
    details = error.message;
  }
  return (
    <main className="container mx-auto p-4 pt-16">
      <h1 className="text-2xl font-semibold">{message}</h1>
      <p role="alert" className="mt-2 text-red-400">{details}</p>
    </main>
  );
}
