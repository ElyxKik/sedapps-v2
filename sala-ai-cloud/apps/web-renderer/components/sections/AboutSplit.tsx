import { Section } from "../ui/Container";

export function AboutSplit({
  title, body, image,
}: { title: string; body: string; image?: { url?: string; alt?: string } }) {
  return (
    <Section id="about">
      <div className="grid lg:grid-cols-2 gap-12 items-center">
        <div>
          <h2 className="text-3xl sm:text-4xl">{title}</h2>
          <p className="mt-4 text-muted leading-relaxed whitespace-pre-line">{body}</p>
        </div>
        {image?.url && (
          <div className="rounded-lg overflow-hidden border border-white/10">
            <img src={image.url} alt={image.alt || ""} className="w-full h-auto" />
          </div>
        )}
      </div>
    </Section>
  );
}
