import { ArrowRight, FileImage, MessageSquare, PanelsTopLeft } from "lucide-react";
import { Link } from "react-router";
import { buttonVariants } from "~/common/components/ui/button";
import type { Route } from "./+types/home-page";

export const meta: Route.MetaFunction = () => [{ title: "Pascal" }, { name: "description", content: "Put in your sources; the agents arrange them into a portfolio." }];

export default function HomePage() {
  return (
    <div className="mx-auto max-w-5xl py-10">
      <div className="max-w-2xl space-y-6 py-10 md:py-16">
        <p className="text-sm font-medium text-primary">PORTFOLIO WORKSPACE</p>
        <h1 className="text-4xl font-semibold leading-tight tracking-tight md:text-6xl">아이디어부터 완성까지,<br />나만의 포트폴리오</h1>
        <p className="max-w-xl text-base leading-7 text-muted-foreground">사진, 도면, 작업물을 모아보세요. 에이전트와 대화하며 구성하고 편집기에서 직접 다듬을 수 있습니다.</p>
        <div className="flex flex-wrap gap-3">
          <Link to="/projects" className={buttonVariants({ size: "lg" })}>프로젝트 열기 <ArrowRight className="size-4" /></Link>
          <Link to="/auth/login" className={buttonVariants({ variant: "outline", size: "lg" })}>로그인</Link>
        </div>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        {[{ Icon: FileImage, title: "자료 모으기", text: "사진과 도면 등 원본 자료를 프로젝트에 정리합니다." },
          { Icon: MessageSquare, title: "에이전트와 대화", text: "포트폴리오에 들어갈 구성과 문구를 함께 고민합니다." },
          { Icon: PanelsTopLeft, title: "직접 편집하기", text: "편집기에서 페이지를 열고 내용을 다듬습니다." }].map(({ Icon, title, text }) =>
          <div key={title} className="rounded-xl border bg-card p-5"><Icon className="mb-5 size-5 text-primary" /><h2 className="font-semibold">{title}</h2><p className="mt-2 text-sm leading-6 text-muted-foreground">{text}</p></div>)}
      </div>
    </div>
  );
}
