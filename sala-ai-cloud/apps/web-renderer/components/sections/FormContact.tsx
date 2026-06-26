import { Section } from "../ui/Container";
import { getSitePayload } from "@/lib/content";

export function FormContact({
  title, subtitle, form_id, layout = "split",
}: { title?: string; subtitle?: string; form_id: string; layout?: "single" | "split" }) {
  // Charge le schéma du formulaire depuis le payload
  const form = getSitePayload().form || { fields: [], submit_label: "Envoyer" };
  const fields = (form as any).fields || [];
  const action =
    typeof process !== "undefined" && process.env.NEXT_PUBLIC_INBOX_URL
      ? `${process.env.NEXT_PUBLIC_INBOX_URL}/v1/forms/${form_id}/submit`
      : "#";

  return (
    <Section id="contact">
      <div className={layout === "split" ? "grid lg:grid-cols-2 gap-12" : "max-w-2xl mx-auto"}>
        <div>
          {title && <h2 className="text-3xl sm:text-4xl">{title}</h2>}
          {subtitle && <p className="mt-3 text-muted">{subtitle}</p>}
        </div>
        <form
          action={action}
          method="POST"
          className="bg-surface border border-white/10 rounded-lg p-6 space-y-4"
          data-track="contact"
        >
          {/* Honeypot anti-spam */}
          <input type="text" name="website_url" tabIndex={-1} autoComplete="off"
                 className="absolute -left-[10000px]" aria-hidden="true" />
          {fields.map((f: any) => (
            <div key={f.key}>
              <label className="block text-sm mb-1">{f.label}{f.required ? " *" : ""}</label>
              {f.type === "textarea" ? (
                <textarea
                  name={f.key}
                  required={!!f.required}
                  maxLength={f.max ?? undefined}
                  rows={5}
                  className="w-full bg-bg border border-white/10 rounded-md px-3 py-2 focus:border-primary outline-none"
                />
              ) : (
                <input
                  name={f.key}
                  type={f.type || "text"}
                  required={!!f.required}
                  maxLength={f.max ?? undefined}
                  className="w-full bg-bg border border-white/10 rounded-md px-3 py-2 focus:border-primary outline-none"
                />
              )}
            </div>
          ))}
          <button
            type="submit"
            className="bg-primary text-white px-5 py-2.5 rounded-md font-semibold w-full"
            data-event="cta"
          >
            {(form as any).submit_label || "Envoyer"}
          </button>
        </form>
      </div>
    </Section>
  );
}
