/** Send a bounded editing command to our same-origin Rust editor fork. */
export function executeEditorCommand(frame: HTMLIFrameElement, command: "frame.create" | "text.insert" | "edit.undo" | "edit.redo" | "document.inspect", params: Record<string, unknown>): Promise<unknown> {
  const target = frame.contentWindow;
  if (!target) return Promise.reject(new Error("편집기가 열리지 않았습니다."));
  const id = crypto.randomUUID();
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => {
      window.removeEventListener("message", onMessage);
      reject(new Error("우리 편집기와 연결하지 못했습니다. Rust 웹 빌드를 확인하세요."));
    }, 5000);
    function onMessage(event: MessageEvent) {
      if (event.origin !== window.location.origin || event.source !== target || event.data?.type !== "pascal-editor-result" || event.data.id !== id) return;
      window.clearTimeout(timer);
      window.removeEventListener("message", onMessage);
      if (event.data.ok === true) resolve(event.data.result);
      else reject(new Error(typeof event.data.error === "string" ? event.data.error : "편집 명령 실패"));
    }
    window.addEventListener("message", onMessage);
    target.postMessage({ type: "pascal-editor-command", id, command, params }, window.location.origin);
  });
}
