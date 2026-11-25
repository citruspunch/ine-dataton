import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mesa de Precios | Compras municipales con datos del INE",
  description:
    "Consulta y auditoría de precios de referencia, índices de construcción y canastas básicas del INE Guatemala antes de cotizar.",
  applicationName: "Mesa de Precios",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
