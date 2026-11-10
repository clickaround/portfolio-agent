import { useEffect, useState, type ImgHTMLAttributes, type ReactNode } from "react";
import { authenticatedFetch } from "~/lib/auth/fetch";

export function AuthenticatedImage({ src, ...props }: Omit<ImgHTMLAttributes<HTMLImageElement>, "src"> & { src: string }) {
  const [resource, setResource] = useState<{ src: string; url: string }>();
  useEffect(() => {
    let active = true;
    let objectUrl: string | undefined;
    void authenticatedFetch(src).then((response) => {
      if (!response.ok) throw new Error("Image unavailable");
      return response.blob();
    }).then((blob) => {
      if (active) { objectUrl = URL.createObjectURL(blob); setResource({ src, url: objectUrl }); }
    }).catch(() => {});
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [src]);
  return <img {...props} src={resource?.src === src ? resource.url : undefined} />;
}

export function AuthenticatedLink({ href, children, className }: { href: string; children: ReactNode; className?: string }) {
  const [error, setError] = useState("");
  async function open() {
    try {
      const response = await authenticatedFetch(href);
      if (!response.ok) throw new Error("파일을 가져오지 못했습니다.");
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a"); link.href = url; link.download = href.split("/").pop() ?? "download"; link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch { setError("파일을 가져오지 못했습니다."); }
  }
  return <><button type="button" className={className} onClick={() => void open()}>{children}</button>{error && <span role="alert">{error}</span>}</>;
}
