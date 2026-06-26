import { Section } from "../ui/Container";

export function GalleryGrid({
  title, items = [],
}: { title?: string; items?: { url?: string; alt?: string }[] }) {
  return (
    <Section>
      {title && <h2 className="text-3xl sm:text-4xl text-center mb-10">{title}</h2>}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {items.filter((i) => i.url).map((i, idx) => (
          <div key={idx} className="aspect-square rounded-md overflow-hidden border border-white/10">
            <img src={i.url} alt={i.alt || ""} className="w-full h-full object-cover" />
          </div>
        ))}
      </div>
    </Section>
  );
}
