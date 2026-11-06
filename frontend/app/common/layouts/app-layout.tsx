import { Link, Outlet } from "react-router";

export default function AppLayout() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-rule bg-white">
        <nav className="mx-auto flex max-w-5xl items-center gap-4 p-4">
          <Link to="/" className="font-serif text-xl">Pascal</Link>
          <span className="text-sm text-ink/60">portfolio workbench</span>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
