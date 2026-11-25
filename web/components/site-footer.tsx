import Image from "next/image";
import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-white print:hidden">
      <div className="mx-auto grid max-w-6xl gap-8 px-5 py-10 sm:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)] sm:px-6">
        <div>
          <div className="flex items-center gap-3">
            <Image
              src="/ine-logo.png"
              alt=""
              width={7026}
              height={2273}
              className="h-8 w-auto opacity-90"
            />
            <span className="text-[12px] font-bold uppercase tracking-[0.16em] text-brand">
              Data Trust
            </span>
          </div>
          <p className="mt-4 max-w-2xl text-[12.5px] leading-relaxed text-muted">
            Validación técnica de los agregados estadísticos publicados por el Instituto
            Nacional de Estadística de Guatemala. Cada cifra conserva su fuente, su
            licencia y el registro de la decisión humana que la habilitó.
          </p>
          <p className="mt-3 max-w-2xl text-[12px] leading-relaxed text-muted">
            Este sistema no certifica, no corrige, no publica en CKAN y no constituye una
            aprobación del INE. Las cifras y los datos conservan su licencia original.
          </p>
        </div>
        <div className="text-[12.5px] text-muted">
          <p className="text-[11.5px] font-bold uppercase tracking-[0.14em] text-brand">
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
                Instituto Nacional de Estadística ↗
              </a>
            </li>
            <li>
              <a
                href="https://datos.ine.gob.gt"
                target="_blank"
                rel="noreferrer"
                className="hover:text-brand hover:underline"
              >
                Portal de datos abiertos ↗
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
        <p className="mx-auto max-w-6xl px-5 py-4 text-[11.5px] text-muted sm:px-6">
          INE Data Trust · Datatón INE 2026 · Documento de trabajo, no oficial.
        </p>
      </div>
    </footer>
  );
}
