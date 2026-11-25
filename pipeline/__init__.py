"""Local growth pressure monitor data pipeline.

The package turns official INE, MINEDUC and SEGEPLAN files into a single,
auditable municipal indicator table. It is intentionally small and linear:
download/cache -> normalise codes -> aggregate -> indicators -> suppression ->
Parquet + JSON + provenance manifest.
"""

__version__ = "0.1.0"
