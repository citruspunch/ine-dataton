import type { Metadata } from "next";
import localFont from "next/font/local";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

import "./globals.css";

// Official Ubuntu Sans variable font shipped in the Datatón design kit.
const sans = localFont({
  src: "./fonts/UbuntuSans-Variable.woff2",
  variable: "--font-ubuntu-sans",
  display: "swap",
  weight: "100 800",
  style: "normal",
});

export const metadata: Metadata = {
  title: {
    default: "INE Data Trust · Validación de agregados estadísticos",
    template: "%s · INE Data Trust",
  },
  description:
    "Validación técnica de los agregados estadísticos del INE, con la decisión humana registrada.",
  applicationName: "INE Data Trust",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={sans.variable}>
      <body className="flex min-h-screen flex-col">
        <a
          href="#contenido"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-brand focus:px-4 focus:py-2 focus:text-[15px] focus:font-semibold focus:text-white"
        >
          Saltar al contenido
        </a>
        <SiteHeader />
        <main id="contenido" className="mx-auto w-full max-w-6xl flex-1 px-5 py-10 sm:px-6">
          {children}
        </main>
        <SiteFooter />
      </body>
    </html>
  );
}
