import { FolderOpen, Home, Menu, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { Link, useLocation } from "react-router";
import { Button } from "./ui/button";
import { Sheet, SheetClose, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "./ui/sheet";

function Links({ close }: { close?: boolean }) {
  const { pathname } = useLocation();
  const project = pathname.match(/^\/projects\/([^/]+)/)?.[1];
  const links = [
    { to: "/", label: "홈", Icon: Home },
    { to: "/projects", label: "프로젝트", Icon: FolderOpen },
    ...(project ? [{ to: `/projects/${project}`, label: "현재 프로젝트", Icon: FolderOpen }] : []),
  ];
  return <nav aria-label="주 메뉴" className="space-y-1">
    {links.map(({ to, label, Icon }) => {
      const link = <Link to={to} className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm hover:bg-accent"><Icon className="size-4 shrink-0" /><span>{label}</span></Link>;
      return close ? <SheetClose asChild key={to}>{link}</SheetClose> : <div key={to}>{link}</div>;
    })}
  </nav>;
}

export default function Navigation({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  return <>
    <aside aria-label="사이드바" className="fixed inset-y-0 left-0 z-[60] hidden w-[var(--sidebar-width)] flex-col border-r bg-card md:flex">
      <div className="flex h-16 items-center justify-between px-3">
        {!collapsed && <Link to="/" className="px-2 text-lg font-bold tracking-tight">Pascal</Link>}
        <Button variant="ghost" size="icon" aria-label={collapsed ? "사이드바 열기" : "사이드바 닫기"} onClick={onToggle}>
          {collapsed ? <PanelLeftOpen className="size-5" /> : <PanelLeftClose className="size-5" />}
        </Button>
      </div>
      {collapsed ? <nav aria-label="주 메뉴" className="flex flex-col items-center gap-1">
        <Link to="/" aria-label="홈" className="rounded-lg p-3 hover:bg-accent"><Home className="size-4" /></Link>
        <Link to="/projects" aria-label="프로젝트" className="rounded-lg p-3 hover:bg-accent"><FolderOpen className="size-4" /></Link>
      </nav> : <div className="px-2"><Links /><p className="px-3 pt-6 text-xs text-muted-foreground">대화 기록은 아직 저장되지 않습니다</p></div>}
    </aside>
    <div className="fixed inset-x-0 top-0 z-[60] flex h-14 items-center border-b bg-background px-3 md:hidden">
      <Sheet><SheetTrigger asChild><Button variant="ghost" size="icon" aria-label="사이드바 열기"><Menu className="size-5" /></Button></SheetTrigger>
        <SheetContent side="left"><SheetHeader><SheetTitle>Pascal</SheetTitle></SheetHeader><div className="mt-6"><Links close /></div></SheetContent>
      </Sheet>
      <Link to="/" className="ml-2 font-semibold">Pascal</Link>
    </div>
  </>;
}
