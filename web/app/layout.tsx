import type { Metadata } from "next";
import { Ubuntu_Sans, Ubuntu_Sans_Mono } from "next/font/google";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

import "./globals.css";

const sans = Ubuntu_Sans({
  subsets: ["latin"],
  variable: "--font-ubuntu-sans",
  display: "swap",
});

const mono = Ubuntu_Sans_Mono({
  subsets: ["latin"],
  variable: "--font-ubuntu-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "INE Data Trust · Validación de agregados estadísticos",
    template: "%s · INE Data Trust",
  },
  description:
    "Validación técnica, con trazabilidad y decisión humana, de los agregados estadísticos publicados por el INE.",
  applicationName: "INE Data Trust",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${sans.variable} ${mono.variable}`}>
      <body className="flex min-h-screen flex-col">
        <a
          href="#contenido"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-brand focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
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
