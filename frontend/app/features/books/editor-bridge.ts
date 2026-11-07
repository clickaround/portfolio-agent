/** Observe the pinned editor's native downloads without modifying or cancelling them.
 * This is a best-effort compatibility bridge, not an official DesignCraft API.
 */
export function observeDesignCraftSaves(frame: Window & typeof globalThis, onSave: (blob: Blob, name: string) => void): () => void {
  const urls = new Map<string, Blob>();
  const create = frame.URL.createObjectURL;
  const revoke = frame.URL.revokeObjectURL;
  const click = frame.HTMLAnchorElement.prototype.click;
  function createUrl(value: Blob | MediaSource): string {
    const url = create.call(frame.URL, value);
    if (value instanceof frame.Blob) urls.set(url, value);
    return url;
  }
  function revokeUrl(url: string): void {
    urls.delete(url);
    revoke.call(frame.URL, url);
  }
  function anchorClick(this: HTMLAnchorElement): void {
    try {
      const blob = urls.get(this.href);
      if (blob && this.download.toLowerCase().endsWith(".designcraft")) onSave(blob, this.download);
    } catch {
      // Capture is optional; the vendor's normal download must still work.
    }
    click.call(this);
  }
  frame.URL.createObjectURL = createUrl;
  frame.URL.revokeObjectURL = revokeUrl;
  frame.HTMLAnchorElement.prototype.click = anchorClick;
  return () => {
    if (frame.URL.createObjectURL === createUrl) frame.URL.createObjectURL = create;
    if (frame.URL.revokeObjectURL === revokeUrl) frame.URL.revokeObjectURL = revoke;
    if (frame.HTMLAnchorElement.prototype.click === anchorClick) frame.HTMLAnchorElement.prototype.click = click;
    urls.clear();
  };
}
