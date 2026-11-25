# Web app — Perfil de demanda municipal

Interfaz Next.js + shadcn/ui para la ficha municipal. La documentación
completa, el pipeline de datos y las instrucciones desde cero están en el
[`README.md`](../README.md) de la raíz.

## Comandos

```bash
# desde web/, con los JSON ya generados en public/data/
pnpm install
pnpm dev        # http://localhost:3000
pnpm build
pnpm start
pnpm lint
pnpm exec tsc --noEmit
```

Para regenerar los datos desde la raíz del repositorio:

```bash
uv run municipal-profile all
```

La aplicación no usa variables de entorno, servicios en la nube ni llaves de
acceso. Sirve JSON estáticos desde `public/data/`.
