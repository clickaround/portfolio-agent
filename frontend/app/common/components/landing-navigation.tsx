import { DuiNavigation } from "@dk/dui";
import { Menu } from "lucide-react";
import { Link } from "react-router";
import { useSession } from "~/lib/auth/session";
import { Button } from "./ui/button";
import { Sheet, SheetClose, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "./ui/sheet";

/** The same navigation frame as MARK, with Portfolio's real routes. */
export function LandingNavigation() {
  const { user } = useSession();
  return <Sheet><DuiNavigation>
    <div className="w-full bg-primary py-2.5 text-center text-xs font-bold text-primary-foreground">자료와 대화로 만드는 포트폴리오</div>
    <div className="flex h-16 items-center justify-between bg-background/80 px-5 backdrop-blur md:px-20">
      <div className="flex items-center gap-8"><Link to="/" className="text-lg font-bold tracking-tight">Pascal</Link><Link to="/projects" className="hidden text-sm md:block">프로젝트</Link></div>
      <div className="hidden items-center gap-2 md:flex">{user ? <Button asChild><Link to="/projects">작업 공간</Link></Button> : <><Button variant="secondary" asChild><Link to="/auth/login">로그인</Link></Button><Button asChild><Link to="/auth/join">회원가입</Link></Button></>}</div>
      <SheetTrigger asChild><Button variant="ghost" size="icon" className="md:hidden" aria-label="메뉴 열기"><Menu /></Button></SheetTrigger>
    </div>
    <SheetContent side="right"><SheetHeader><SheetTitle>Pascal</SheetTitle></SheetHeader><div className="mt-6 flex flex-col gap-4"><SheetClose asChild><Link to="/">홈</Link></SheetClose><SheetClose asChild><Link to="/projects">프로젝트</Link></SheetClose>{!user && <><SheetClose asChild><Link to="/auth/login">로그인</Link></SheetClose><SheetClose asChild><Link to="/auth/join">회원가입</Link></SheetClose></>}</div></SheetContent>
  </DuiNavigation></Sheet>;
}
