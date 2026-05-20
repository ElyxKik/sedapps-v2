import DOMPurify from "isomorphic-dompurify";
import { remark } from "remark";
import remarkHtml from "remark-html";

export async function renderMarkdown(md: string): Promise<string> {
  const file = await remark().use(remarkHtml).process(md);
  return DOMPurify.sanitize(String(file));
}
