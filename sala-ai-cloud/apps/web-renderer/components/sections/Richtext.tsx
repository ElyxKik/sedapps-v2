import { Section } from "../ui/Container";
import { renderMarkdown } from "@/lib/markdown";

export async function Richtext({ markdown }: { markdown: string }) {
  const html = await renderMarkdown(markdown);
  return (
    <Section>
      <div className="prose-renderer max-w-3xl mx-auto" dangerouslySetInnerHTML={{ __html: html }} />
    </Section>
  );
}
