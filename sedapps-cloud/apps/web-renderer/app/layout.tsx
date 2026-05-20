import "./globals.css";
import type { ReactNode } from "react";
import { getSitePayload } from "@/lib/content";
import { tokensToCss, googleFontsHref } from "@/lib/tokens";
import { Header, Footer } from "@/components/Header";

export default function RootLayout({ children }: { children: ReactNode }) {
  const payload = getSitePayload();
  const css = tokensToCss(payload.design_tokens);
  const fonts = googleFontsHref(payload.design_tokens);
  const tracker = payload.analytics?.tracker_id;

  return (
    <html lang="fr">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link rel="stylesheet" href={fonts} />
        <style id="design-tokens" dangerouslySetInnerHTML={{ __html: css }} />
      </head>
      <body>
        <Header />
        <main>{children}</main>
        <Footer />
        {tracker && (
          <script
            async
            defer
            src={`${process.env.NEXT_PUBLIC_ANALYTICS_URL || ""}/tracker.js`}
            data-site={tracker}
          />
        )}
      </body>
    </html>
  );
}
