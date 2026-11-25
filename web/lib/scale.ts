export type ColorScale = {
  breaks: number[];
  colors: string[];
  min: number;
  max: number;
  color: (value: number) => string;
  bucket: (value: number) => number;
};

function quantile(sorted: number[], p: number): number {
  if (sorted.length === 0) return 0;
  const index = (sorted.length - 1) * p;
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  if (lower === upper) return sorted[lower];
  const weight = index - lower;
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

export function makeQuantileScale(
  values: number[],
  colors: string[],
  classes = colors.length,
): ColorScale {
  const sorted = [...values].filter((value) => Number.isFinite(value)).sort((a, b) => a - b);
  const min = sorted[0] ?? 0;
  const max = sorted[sorted.length - 1] ?? 0;
  if (sorted.length === 0) {
    return {
      breaks: [],
      colors,
      min: 0,
      max: 0,
      color: () => colors[0],
      bucket: () => 0,
    };
  }
  const breaks: number[] = [];
  for (let i = 1; i < classes; i += 1) {
    breaks.push(quantile(sorted, i / classes));
  }
  const bucket = (value: number) => {
    for (let i = 0; i < breaks.length; i += 1) {
      if (value <= breaks[i]) return i;
    }
    return colors.length - 1;
  };
  return {
    breaks,
    colors,
    min,
    max,
    bucket,
    color: (value: number) => colors[bucket(value)],
  };
}

