"use client";

import { geoArea, geoCentroid, geoMercator, geoPath } from "d3-geo";
import { Minus, Plus, RotateCcw } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import { rewindForD3 } from "@/lib/geo";
import { formatNumber, formatRate } from "@/lib/format";
import type { ColorScale } from "@/lib/scale";
import type { Cell, LevelId, Mode, PointTuple, TerritoryGeo } from "@/lib/types";
import { cn } from "@/lib/utils";

const WIDTH = 720;
const HEIGHT = 760;

type Props = {
  level: LevelId;
  geo: TerritoryGeo;
  selected: string | null;
  onSelect: (code: string) => void;
  cellFor: (code: string) => Cell | undefined;
  nameFor: (code: string) => string;
  scale: ColorScale | null;
  mode: Mode;
  points: PointTuple[];
  showPoints: boolean;
  available: boolean;
  unavailableTitle?: string;
  unavailableMessage?: string;
  onUseOccurrence?: () => void;
  className?: string;
};

type HoverState = {
  code: string;
  x: number;
  y: number;
} | null;

export function TerritoryMap({
  level,
  geo,
  selected,
  onSelect,
  cellFor,
  nameFor,
  scale,
  mode,
  points,
  showPoints,
  available,
  unavailableTitle,
  unavailableMessage,
  onUseOccurrence,
  className,
}: Props) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const svgRef = React.useRef<SVGSVGElement>(null);
  const [hover, setHover] = React.useState<HoverState>(null);
  const [transform, setTransform] = React.useState({ k: 1, x: 0, y: 0 });
  const drag = React.useRef<{
    pointerId: number;
    startX: number;
    startY: number;
    originX: number;
    originY: number;
  } | null>(null);

  const projection = React.useMemo(() => {
    const rewound = rewindForD3(geo);
    return geoMercator()
      .fitExtent(
        [
          [24, 24],
          [WIDTH - 24, HEIGHT - 24],
        ],
        rewound as never,
      );
  }, [geo]);

  const rewoundGeo = React.useMemo(() => rewindForD3(geo), [geo]);

  const pathGenerator = React.useMemo(() => geoPath(projection), [projection]);

  const paths = React.useMemo(() => {
    const map = new Map<string, string>();
    for (const feature of rewoundGeo.features) {
      map.set(feature.properties.code, pathGenerator(feature as never) ?? "");
    }
    return map;
  }, [rewoundGeo, pathGenerator]);

  const pointPath = React.useMemo(() => {
    if (!showPoints) return "";
    const chunks: string[] = [];
    for (const point of points) {
      const projected = projection([point[4], point[5]]);
      if (!projected) continue;
      const x = projected[0].toFixed(1);
      const y = projected[1].toFixed(1);
      chunks.push(`M${x},${y}h0.7v0.7h-0.7z`);
    }
    return chunks.join("");
  }, [points, projection, showPoints]);

  const labels = React.useMemo(() => {
    if (level !== "department") return [];
    const showAllLabels = transform.k > 1.4;
    const candidates = rewoundGeo.features
      .filter(
        (feature) => showAllLabels || feature.properties.code === selected,
      )
      .map((feature) => ({
        feature,
        area: geoArea(feature as never),
        centroid: geoCentroid(feature as never),
      }))
      .sort((a, b) => {
        const selectedFirst =
          Number(b.feature.properties.code === selected) -
          Number(a.feature.properties.code === selected);
        return selectedFirst || b.area - a.area;
      });
    const placed: { x: number; y: number; width: number }[] = [];
    const result: { code: string; name: string; x: number; y: number }[] = [];
    for (const candidate of candidates) {
      const projected = projection(candidate.centroid);
      if (!projected) continue;
      const [x, y] = projected;
      const width = candidate.feature.properties.name.length * 4.3;
      const collides = placed.some(
        (label) =>
          Math.abs(label.x - x) < (label.width + width) / 2 + 3 &&
          Math.abs(label.y - y) < 12,
      );
      if (collides) continue;
      placed.push({ x, y, width });
      result.push({
        code: candidate.feature.properties.code,
        name: candidate.feature.properties.name,
        x,
        y,
      });
    }
    return result;
  }, [rewoundGeo, level, projection, selected, transform.k]);

  React.useEffect(() => {
    setTransform({ k: 1, x: 0, y: 0 });
  }, [level]);

  const clamp = (value: number, min: number, max: number) =>
    Math.min(max, Math.max(min, value));

  const clampTransform = (k: number, x: number, y: number) => ({
    k,
    x: clamp(x, WIDTH * (1 - k), 0),
    y: clamp(y, HEIGHT * (1 - k), 0),
  });

  const zoomAt = (factor: number, cx = WIDTH / 2, cy = HEIGHT / 2) => {
    setTransform((current) => {
      const nextK = clamp(current.k * factor, 1, 7);
      if (nextK === current.k) return current;
      const nextX = cx - (cx - current.x) * (nextK / current.k);
      const nextY = cy - (cy - current.y) * (nextK / current.k);
      return clampTransform(nextK, nextX, nextY);
    });
  };

  React.useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const listener = (event: WheelEvent) => {
      event.preventDefault();
      const rect = svg.getBoundingClientRect();
      const cx = ((event.clientX - rect.left) / rect.width) * WIDTH;
      const cy = ((event.clientY - rect.top) / rect.height) * HEIGHT;
      zoomAt(event.deltaY < 0 ? 1.18 : 0.85, cx, cy);
    };
    svg.addEventListener("wheel", listener, { passive: false });
    return () => svg.removeEventListener("wheel", listener);
  }, []);

  const pointerPoint = (event: React.PointerEvent<SVGSVGElement>) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return { x: 0, y: 0 };
    return {
      x: ((event.clientX - rect.left) / rect.width) * WIDTH,
      y: ((event.clientY - rect.top) / rect.height) * HEIGHT,
    };
  };

  const onPointerDown = (event: React.PointerEvent<SVGSVGElement>) => {
    if (event.button !== 0) return;
    const point = pointerPoint(event);
    drag.current = {
      pointerId: event.pointerId,
      startX: point.x,
      startY: point.y,
      originX: transform.x,
      originY: transform.y,
    };
    event.currentTarget.setPointerCapture(event.pointerId);
  };

  const onPointerMove = (event: React.PointerEvent<SVGSVGElement>) => {
    const dragState = drag.current;
    if (!dragState) return;
    const point = pointerPoint(event);
    const dx = point.x - dragState.startX;
    const dy = point.y - dragState.startY;
    // Capture the origin before scheduling the state update. React can run the
    // updater after `endDrag()` has set drag.current to null, which is what
    // caused "null is not an object (evaluating 'drag.current.originX')".
    const originX = dragState.originX;
    const originY = dragState.originY;
    setTransform((current) =>
      clampTransform(current.k, originX + dx, originY + dy),
    );
  };

  const endDrag = () => {
    drag.current = null;
  };

  const handleMove = (
    code: string,
    event: React.MouseEvent<SVGPathElement>,
  ) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    setHover({ code, x, y });
  };

  const hoveredCell = hover ? cellFor(hover.code) : undefined;
  const hoveredName = hover ? nameFor(hover.code) : "";
  const hoveredValue =
    hoveredCell && !hoveredCell.suppressed
      ? mode === "rate"
        ? `${formatRate(hoveredCell.rate)} por 10 mil`
        : `${formatNumber(hoveredCell.count)} casos`
      : "Celda suprimida";

  return (
    <div
      ref={containerRef}
      className={cn("relative isolate h-full min-h-[420px] w-full", className)}
    >
      <svg
        ref={svgRef}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className={cn(
          "h-full w-full touch-none select-none",
          transform.k > 1 ? "cursor-grab active:cursor-grabbing" : "cursor-default",
        )}
        role="img"
        aria-label={`Mapa de Guatemala por ${level === "department" ? "departamento" : "municipio"}`}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={endDrag}
        onPointerLeave={() => {
          endDrag();
          setHover(null);
        }}
        onDoubleClick={(event) => {
          const rect = svgRef.current?.getBoundingClientRect();
          if (!rect) return;
          zoomAt(
            1.5,
            ((event.clientX - rect.left) / rect.width) * WIDTH,
            ((event.clientY - rect.top) / rect.height) * HEIGHT,
          );
        }}
      >
        <defs>
          <pattern
            id="suppressed-pattern"
            width="7"
            height="7"
            patternUnits="userSpaceOnUse"
            patternTransform="rotate(45)"
          >
            <rect width="7" height="7" fill="#f1eee8" />
            <line x1="0" y1="0" x2="0" y2="7" stroke="#d8d2c7" strokeWidth="1" />
          </pattern>
          <filter id="map-shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.12" />
          </filter>
        </defs>

        <g
          transform={`translate(${transform.x},${transform.y}) scale(${transform.k})`}
        >
          {pointPath ? (
            <path
              d={pointPath}
              fill="#173f3a"
              opacity={0.26}
              pointerEvents="none"
            />
          ) : null}

          {rewoundGeo.features.map((feature) => {
            const code = feature.properties.code;
            const cell = cellFor(code);
            const isSelected = code === selected;
            const isHovered = hover?.code === code;
            const value =
              cell && !cell.suppressed
                ? mode === "rate"
                  ? cell.rate
                  : cell.count
                : null;
            const fill = !available
              ? "#eceae4"
              : !cell || cell.suppressed || !scale || value === null
                ? "url(#suppressed-pattern)"
                : scale.color(value);
            return (
              <path
                key={code}
                d={paths.get(code)}
                fill={fill}
                stroke={isSelected ? "#122a27" : isHovered ? "#122a27" : "#fbfaf7"}
                strokeWidth={isSelected ? 2.4 : isHovered ? 1.6 : 0.8}
                vectorEffect="non-scaling-stroke"
                className="transition-[fill,stroke,opacity] duration-150"
                style={{ opacity: isSelected || isHovered ? 1 : 0.97 }}
                onMouseEnter={(event) => handleMove(code, event)}
                onMouseMove={(event) => handleMove(code, event)}
                onMouseLeave={() => setHover(null)}
                onClick={() => onSelect(code)}
                role="button"
                tabIndex={level === "department" ? 0 : -1}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onSelect(code);
                  }
                }}
                aria-label={`${nameFor(code)}${cell && !cell.suppressed ? `, ${mode === "rate" ? `${formatRate(cell.rate)} por 10 mil` : `${cell.count} casos`}` : ", suprimido"}`}
              >
                <title>{nameFor(code)}</title>
              </path>
            );
          })}

          {labels.map((label) => (
            <text
              key={label.code}
              x={label.x}
              y={label.y}
              textAnchor="middle"
              className="pointer-events-none hidden select-none sm:block"
              style={{
                fill: "#20302d",
                fontSize: 11,
                fontWeight: 600,
                letterSpacing: "0.02em",
                paintOrder: "stroke",
                stroke: "#fbfaf7",
                strokeWidth: 3.2,
                strokeLinejoin: "round",
              }}
            >
              {label.name}
            </text>
          ))}
        </g>
      </svg>

      <div className="absolute right-3 top-3 flex flex-col gap-1.5">
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="size-8 bg-card/90 shadow-sm backdrop-blur"
          onClick={() => zoomAt(1.35)}
          aria-label="Acercar"
        >
          <Plus className="size-4" />
        </Button>
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="size-8 bg-card/90 shadow-sm backdrop-blur"
          onClick={() => zoomAt(0.74)}
          aria-label="Alejar"
        >
          <Minus className="size-4" />
        </Button>
        <Button
          type="button"
          variant={transform.k > 1 ? "secondary" : "outline"}
          size="icon"
          className="size-8 bg-card/90 shadow-sm backdrop-blur"
          onClick={() => setTransform({ k: 1, x: 0, y: 0 })}
          aria-label="Restablecer zoom"
        >
          <RotateCcw className="size-3.5" />
        </Button>
      </div>

      {!available ? (
        <div className="absolute inset-0 flex items-center justify-center p-6">
          <div className="max-w-sm rounded-2xl border border-border/80 bg-card/95 p-5 text-center shadow-xl backdrop-blur">
            <p className="font-display text-lg font-semibold">
              {unavailableTitle ?? "Sin datos para este criterio"}
            </p>
            <p className="mt-2 text-xs leading-relaxed text-muted-foreground">
              {unavailableMessage ??
                "La fuente oficial no contiene la variable necesaria para este cruce."}
            </p>
            {onUseOccurrence ? (
              <Button
                type="button"
                size="sm"
                className="mt-4"
                onClick={onUseOccurrence}
              >
                Ver por lugar de ocurrencia
              </Button>
            ) : null}
          </div>
        </div>
      ) : null}

      {hover && available ? (
        <div
          className="pointer-events-none absolute z-20 w-56 rounded-xl border border-border/80 bg-card/95 p-3 shadow-xl backdrop-blur"
          style={{
            left: Math.min(hover.x + 14, (containerRef.current?.clientWidth ?? 300) - 216),
            top: Math.min(hover.y + 14, (containerRef.current?.clientHeight ?? 300) - 104),
          }}
        >
          <p className="text-sm font-semibold leading-tight">{hoveredName}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {hoveredCell && !hoveredCell.suppressed ? (
              <span className="tabular font-medium text-foreground">{hoveredValue}</span>
            ) : (
              <span className="inline-flex items-center gap-1 text-amber-800">
                <span className="inline-block size-2 rounded-full bg-amber-500" />
                {hoveredValue}
              </span>
            )}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {level === "department" ? "Departamento" : "Municipio"}
          </p>
        </div>
      ) : null}
    </div>
  );
}
