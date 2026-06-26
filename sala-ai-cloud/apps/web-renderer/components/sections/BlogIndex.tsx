import { Section } from "../ui/Container";
import { getArticles } from "@/lib/content";

export function BlogIndex({
  title, style = "grid", per_page = 9,
}: { title?: string; style?: "grid" | "list" | "magazine"; per_page?: number }) {
  const articles = getArticles().slice(0, per_page);

  return (
    <Section id="blog">
      {title && <h2 className="text-3xl sm:text-4xl mb-10">{title}</h2>}

      {style === "list" && (
        <ul className="space-y-6">
          {articles.map((a) => (
            <li key={a.slug} className="flex gap-6 bg-surface border border-white/10 rounded-lg p-5">
              {a.cover_url && (
                <img src={a.cover_url} alt={a.title}
                     className="w-32 h-24 object-cover rounded-md flex-none" />
              )}
              <div>
                <a href={`/blog/${a.slug}/`} className="text-lg font-semibold hover:text-primary">{a.title}</a>
                {a.excerpt && <p className="text-muted text-sm mt-1">{a.excerpt}</p>}
              </div>
            </li>
          ))}
        </ul>
      )}

      {style === "grid" && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {articles.map((a) => (
            <a key={a.slug} href={`/blog/${a.slug}/`}
               className="bg-surface border border-white/10 rounded-lg overflow-hidden hover:border-white/20 transition">
              {a.cover_url && <img src={a.cover_url} alt={a.title} className="w-full h-44 object-cover" />}
              <div className="p-5">
                <h3 className="text-lg font-semibold">{a.title}</h3>
                {a.excerpt && <p className="text-muted text-sm mt-2 line-clamp-3">{a.excerpt}</p>}
                <p className="text-xs text-muted mt-3">{a.reading_time_min} min de lecture</p>
              </div>
            </a>
          ))}
        </div>
      )}

      {style === "magazine" && articles.length > 0 && (
        <div className="grid lg:grid-cols-3 gap-6">
          <a href={`/blog/${articles[0].slug}/`}
             className="lg:col-span-2 bg-surface border border-white/10 rounded-lg overflow-hidden">
            {articles[0].cover_url && (
              <img src={articles[0].cover_url} alt={articles[0].title} className="w-full h-72 object-cover" />
            )}
            <div className="p-6">
              <h3 className="text-2xl font-bold">{articles[0].title}</h3>
              {articles[0].excerpt && <p className="text-muted mt-2">{articles[0].excerpt}</p>}
            </div>
          </a>
          <div className="space-y-4">
            {articles.slice(1, 4).map((a) => (
              <a key={a.slug} href={`/blog/${a.slug}/`}
                 className="block bg-surface border border-white/10 rounded-lg p-4 hover:border-white/20">
                <h4 className="font-semibold">{a.title}</h4>
                {a.excerpt && <p className="text-muted text-sm mt-1 line-clamp-2">{a.excerpt}</p>}
              </a>
            ))}
          </div>
        </div>
      )}
    </Section>
  );
}
