import type { Metadata } from "next";
import "@fontsource-variable/inter";
import "@fontsource-variable/fraunces";
import "./globals.css";

export const metadata: Metadata = {
  title: "Radar territorial · Seguridad vial y salud · Guatemala 2025",
  description:
    "Explorador territorial de nacimientos, defunciones y siniestralidad vial en Guatemala, con tasas por 10,000 habitantes y secreto estadístico.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
