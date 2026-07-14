import { getAllPages } from "@/lib/content";

export function Header() {
  const pages = getAllPages().map((p) => p.meta);
  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-bg/70 border-b border-white/10">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <a href="/" className="font-heading font-bold text-lg">{pages[0]?.title?.split(" — ")[0] || "Site"}</a>
        <nav className="hidden md:flex gap-6 text-sm">
          {pages.map((p) => (
            <a key={p.slug} href={p.slug === "home" ? "/" : `/${p.slug}/`} className="text-muted hover:text-text">
              {p.title}
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-white/10 mt-24 py-10 text-center text-sm text-muted">
      © {new Date().getFullYear()} — Site généré avec SedApps Cloud
    </footer>
  );
}
