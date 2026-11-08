import { BookWorkspace } from "./book-page";
import { getAttempts } from "../queries";
import type { Route } from "./+types/editor-page";

export const meta: Route.MetaFunction = () => [{ title: "Portfolio editor | Pascal" }];

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  const attempts = await getAttempts(params.projectId);
  const attempt = attempts.find((item) => item.attempt === params.attempt && item.files?.["book.designcraft"]);
  if (!attempt) throw new Response("Editable attempt not found", { status: 404 });
  return { projectId: params.projectId, attempts, attempt: params.attempt };
}

export default function EditorPage({ loaderData }: Route.ComponentProps) {
  return <BookWorkspace key={`${loaderData.projectId}:${loaderData.attempt}`} loaderData={loaderData} actionData={undefined} initialAttempt={loaderData.attempt} />;
}
