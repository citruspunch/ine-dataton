import Link from "next/link";
import { FileDashed } from "@phosphor-icons/react/dist/ssr";

import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center gap-4 py-20 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-soft text-brand">
        <FileDashed className="h-6 w-6" aria-hidden weight="duotone" />
      </span>
      <h1 className="text-2xl font-semibold tracking-tight">No encontramos ese recurso</h1>
      <p className="text-[14px] leading-relaxed text-muted">
        El agregado no está publicado, el caso no existe en la bandeja o el enlace dejó de ser
        válido. Solo los agregados habilitados están disponibles en la consulta pública.
      </p>
      <div className="flex gap-2">
        <Link href="/" className={buttonVariants({ variant: "default" })}>
          Ir a la consulta
        </Link>
        <Link href="/review" className={buttonVariants({ variant: "secondary" })}>
          Ir a la bandeja
        </Link>
      </div>
    </div>
  );
}
