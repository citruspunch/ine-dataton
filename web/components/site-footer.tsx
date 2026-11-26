import Link from "next/link";
import { ArrowUpRight } from "@phosphor-icons/react/dist/ssr";

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-white print:hidden">
      <div className="mx-auto grid max-w-6xl gap-8 px-5 py-10 sm:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)] sm:px-6">
        <div>
          <div className="flex items-center gap-3">
            <img
              src="/ine-isologo.svg"
              alt=""
              width={540}
              height={540}
              className="h-9 w-9"
            />
            <span className="text-[13px] font-bold text-brand">
              Data Trust
            </span>
          </div>
          <p className="mt-4 max-w-2xl text-[13.5px] leading-relaxed text-muted">
            Validación técnica de agregados publicados por el Instituto Nacional de
            Estadística de Guatemala.
          </p>
          <p className="mt-3 max-w-2xl text-[13px] leading-relaxed text-muted">
            El sistema no certifica ni corrige los datos, no publica en CKAN y no implica
            aprobación del INE. Los datos mantienen su licencia original.
          </p>
        </div>
        <div className="text-[13.5px] text-muted">
          <p className="text-[12.5px] font-bold text-brand">
            Enlaces
          </p>
          <ul className="mt-3 space-y-2">
            <li>
              <a
                href="https://www.ine.gob.gt"
                target="_blank"
                rel="noreferrer"
                className="hover:text-brand hover:underline"
              >
                Instituto Nacional de Estadística
                <ArrowUpRight className="ml-1 inline h-3 w-3" aria-hidden />
              </a>
            </li>
            <li>
              <a
                href="https://datos.ine.gob.gt"
                target="_blank"
                rel="noreferrer"
                className="hover:text-brand hover:underline"
              >
                Portal de datos abiertos
                <ArrowUpRight className="ml-1 inline h-3 w-3" aria-hidden />
              </a>
            </li>
            <li>
              <Link href="/review" className="hover:text-brand hover:underline">
                Revisión técnica
              </Link>
            </li>
          </ul>
        </div>
      </div>
      <div className="border-t border-line">
        <p className="mx-auto max-w-6xl px-5 py-4 text-[12.5px] text-muted sm:px-6">
          INE Data Trust · Datatón INE 2026 · Documento de trabajo, no oficial.
        </p>
      </div>
    </footer>
  );
}
