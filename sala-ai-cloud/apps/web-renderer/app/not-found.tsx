export default function NotFound() {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-4">
      <h1 className="text-6xl font-bold text-primary">404</h1>
      <p className="mt-4 text-muted">Page introuvable.</p>
      <a href="/" className="mt-6 text-primary underline">Retour à l’accueil</a>
    </div>
  );
}
