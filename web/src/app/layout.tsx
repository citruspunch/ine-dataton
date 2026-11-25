import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";
import { TooltipProvider } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: {
    default: "Canasta Básica Alimentaria · Simulador de costo mensual",
    template: "%s · CBA INE",
  },
  description:
    "Simulador del costo mensual de la Canasta Básica Alimentaria urbana y rural de Guatemala (2024–2026), costo por 1.000 kcal y variaciones del IPC con el empalme oficial del INE.",
  applicationName: "CBA · Simulador INE",
  authors: [{ name: "Equipo Datatón INE 2026" }],
  keywords: [
    "canasta básica alimentaria",
    "CBA",
    "INE Guatemala",
    "IPC",
    "costo de vida",
    "seguridad alimentaria",
  ],
};

export const viewport: Viewport = {
  themeColor: "#0055b8",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={cn("font-sans", geist.variable)}>
      <body className="min-h-dvh bg-background text-foreground">
        <TooltipProvider>{children}</TooltipProvider>
      </body>
    </html>
  );
}
