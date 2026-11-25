import type {
  DeathCauses,
  Indicators,
  Meta,
  Points,
  Territories,
  TerritoryGeo,
} from "./types";

export type Dataset = {
  meta: Meta;
  territories: Territories;
  indicators: Indicators;
  deathCauses: DeathCauses;
  points: Points;
  municipios: TerritoryGeo;
  departamentos: TerritoryGeo;
};

async function loadJson<T>(name: string): Promise<T> {
  // `no-store` is deliberate: the pipeline rewrites these files when the INE
  // cache is rebuilt. A stale cached meta.json used to crash the dashboard
  // because it predated the pointLayer field.
  const response = await fetch(`/data/${name}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`No se pudo cargar ${name} (${response.status}).`);
  }
  return (await response.json()) as T;
}

function staleDataError(): never {
  throw new Error(
    "Los archivos de datos locales no coinciden con esta versión del frontend. " +
      "Ejecute `uv run radar build` en la raíz del proyecto y recargue la página.",
  );
}

function validateDataset(dataset: Dataset): void {
  const {
    meta,
    territories,
    indicators,
    deathCauses,
    points,
    municipios,
    departamentos,
  } = dataset;
  if (
    !meta ||
    meta.schemaVersion !== 1 ||
    !meta.pointLayer ||
    typeof meta.pointLayer.included !== "number" ||
    !meta.topics ||
    !meta.criteria ||
    !meta.criterionNotes ||
    !meta.thresholds ||
    !meta.suppression ||
    !meta.population ||
    !meta.coverage ||
    !Array.isArray(meta.provenance) ||
    !Array.isArray(meta.limits) ||
    !Array.isArray(meta.licenses) ||
    !meta.aiDisclosure ||
    !meta.methodology
  ) {
    staleDataError();
  }
  if (
    !territories ||
    !Array.isArray(territories.municipalities) ||
    territories.municipalities.length !== 340 ||
    !Array.isArray(territories.departments) ||
    territories.departments.length !== 22 ||
    !indicators?.topics ||
    !deathCauses?.residence ||
    !deathCauses?.occurrence ||
    !Array.isArray(points?.points) ||
    municipios?.features?.length !== 340 ||
    departamentos?.features?.length !== 22
  ) {
    staleDataError();
  }
}

export async function loadDataset(): Promise<Dataset> {
  const [
    meta,
    territories,
    indicators,
    deathCauses,
    points,
    municipios,
    departamentos,
  ] = await Promise.all([
    loadJson<Meta>("meta.json"),
    loadJson<Territories>("territories.json"),
    loadJson<Indicators>("indicators.json"),
    loadJson<DeathCauses>("death-causes.json"),
    loadJson<Points>("points.json"),
    loadJson<TerritoryGeo>("municipios.geojson"),
    loadJson<TerritoryGeo>("departamentos.geojson"),
  ]);
  const dataset = {
    meta,
    territories,
    indicators,
    deathCauses,
    points,
    municipios,
    departamentos,
  };
  validateDataset(dataset);
  return dataset;
}
