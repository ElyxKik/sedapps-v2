/** @type {import('next').NextConfig} */
const nextConfig = {
  // SSG export — chaque déploiement produit un dossier `out/` statique
  // qui est uploadé vers OVH Object Storage + CDN.
  output: "export",
  reactStrictMode: true,
  trailingSlash: true,
  images: {
    unoptimized: true, // requis pour `output: 'export'`
  },
  // Le package partagé est consommé en source (workspace local).
  transpilePackages: ["@sedapps/page-schema"],
};

export default nextConfig;
