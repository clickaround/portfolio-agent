import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";

function clamp(value: number, low: number, high: number) {
  return Math.min(high, Math.max(low, value));
}

function limits(width: number): [number, number] {
  if (width <= 0) return [20, 70];
  if (width >= 560) return [Math.max(20, 24000 / width), Math.min(70, 100 - 32000 / width)];
  const minimum = Math.min(45, Math.max(20, 16000 / width));
  return [minimum, Math.max(minimum, Math.min(70, 100 - 16000 / width))];
}

/** The chat remains mounted when collapsed, so its conversation and pending job survive. */
export function ResizableEditorSplit({ panel, editor, isOpen }: { panel: ReactNode; editor: ReactNode; isOpen: boolean }) {
  const container = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);
  const [width, setWidth] = useState(() => typeof window !== "undefined" && window.innerWidth < 600 ? 45 : 30);
  const [isDragging, setIsDragging] = useState(false);
  const [mobileView, setMobileView] = useState<"chat" | "editor">("chat");
  useEffect(() => {
    const element = container.current;
    if (!element || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver((entries) => {
      const measured = entries[0]?.contentRect.width ?? 0;
      if (measured <= 0) return;
      const [minimum, maximum] = limits(measured);
      setWidth((current) => clamp(current, minimum, maximum));
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  function resizeAt(clientX: number) {
    const rect = container.current?.getBoundingClientRect();
    if (!rect || rect.width <= 0) return;
    const [minimum, maximum] = limits(rect.width);
    setWidth(Math.round(clamp((clientX - rect.left) / rect.width * 100, minimum, maximum)));
  }
  function keyResize(event: React.KeyboardEvent<HTMLDivElement>) {
    const delta = event.key === "ArrowRight" ? 2 : event.key === "ArrowLeft" ? -2 : 0;
    const [minimum, maximum] = limits(container.current?.getBoundingClientRect().width ?? 0);
    if (delta) { event.preventDefault(); setWidth((current) => Math.round(clamp(current + delta, minimum, maximum))); }
    else if (event.key === "Home" || event.key === "End") { event.preventDefault(); setWidth(Math.round(event.key === "Home" ? minimum : maximum)); }
  }
  return <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-md border">
    {isOpen && <div className="flex gap-1 border-b bg-card p-1 md:hidden">
      <button type="button" aria-pressed={mobileView === "chat"} onClick={() => setMobileView("chat")} className="flex-1 rounded-md px-3 py-2 text-sm aria-pressed:bg-muted">대화</button>
      <button type="button" aria-pressed={mobileView === "editor"} onClick={() => setMobileView("editor")} className="flex-1 rounded-md px-3 py-2 text-sm aria-pressed:bg-muted">편집기</button>
    </div>}
    <div ref={container} className={`relative flex min-h-0 min-w-0 flex-1 overflow-hidden ${isDragging ? "select-none" : ""}`}>
    <div style={{ "--panel-width": `${width}%`, display: isOpen ? undefined : "none" } as CSSProperties} className={`min-w-0 w-full shrink-0 overflow-hidden md:block md:w-[var(--panel-width)] ${mobileView === "chat" ? "block" : "hidden"}`}>{panel}</div>
    {isOpen && <div role="separator" aria-label="대화 패널 크기 조절" aria-orientation="vertical" aria-valuemin={20} aria-valuemax={70} aria-valuenow={width} tabIndex={0}
      title="드래그하여 패널 크기 조절" className="group hidden w-4 shrink-0 touch-none cursor-col-resize items-center justify-center bg-border hover:bg-primary/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary md:flex"
      onKeyDown={keyResize} onPointerDown={(event) => { event.preventDefault(); dragging.current = true; event.currentTarget.setPointerCapture?.(event.pointerId); setIsDragging(true); }}
      onPointerMove={(event) => { if (dragging.current) resizeAt(event.clientX); }} onPointerUp={() => { dragging.current = false; setIsDragging(false); }} onPointerCancel={() => { dragging.current = false; setIsDragging(false); }} onLostPointerCapture={() => { dragging.current = false; setIsDragging(false); }}>
      <span className="h-12 w-1 rounded-full bg-muted-foreground group-hover:bg-primary" />
    </div>}
    <div className={`min-w-0 flex-1 md:relative md:block ${mobileView === "editor" || !isOpen ? "relative block" : "invisible pointer-events-none absolute inset-0 md:visible md:pointer-events-auto"}`}>{editor}{isDragging && <div aria-hidden="true" className="absolute inset-0 z-10 cursor-col-resize" />}</div>
    </div>
  </div>;
}
