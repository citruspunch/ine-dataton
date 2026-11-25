import { geoArea } from "d3-geo";

import type { TerritoryGeo } from "./types";

type Position = number[];

/**
 * d3-geo treats polygons as spherical and expects clockwise exterior rings.
 * geoBoundaries follows RFC 7946 (counter-clockwise exteriors), so the
 * unmodified polygons cover the whole sphere except the intended territory.
 * We flip every ring of a polygon that d3 sees as inverted, which is the
 * standard fix for rendering GeoJSON with d3-geo.
 */
function reverseGeometry(geometry: TerritoryGeo["features"][number]["geometry"]) {
  if (geometry.type === "Polygon") {
    return {
      ...geometry,
      coordinates: (geometry.coordinates as Position[][]).map((ring) =>
        [...ring].reverse(),
      ),
    };
  }
  if (geometry.type === "MultiPolygon") {
    return {
      ...geometry,
      coordinates: (geometry.coordinates as Position[][][]).map((polygon) =>
        polygon.map((ring) => [...ring].reverse()),
      ),
    };
  }
  return geometry;
}

export function rewindForD3(collection: TerritoryGeo): TerritoryGeo {
  return {
    ...collection,
    features: collection.features.map((feature) => {
      if (geoArea(feature as never) <= 2 * Math.PI) return feature;
      return { ...feature, geometry: reverseGeometry(feature.geometry) };
    }),
  };
}
