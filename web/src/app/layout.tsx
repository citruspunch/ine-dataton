import type { Metadata } from "next";
import { TooltipProvider } from "@/components/ui/tooltip";
import "./globals.css";

export const metadata: Metadata = {
  title: "Presión local · Monitor municipal de Guatemala",
  description:
    "Compare municipios de Guatemala: crecimiento poblacional, nacimientos por escuela, oferta educativa, pobreza y asignación constitucional. Datos INE, MINEDUC y SEGEPLAN.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body>
        <TooltipProvider delayDuration={150}>{children}</TooltipProvider>
      </body>
    </html>
  );
}
