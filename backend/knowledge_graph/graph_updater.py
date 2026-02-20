"""
knowledge_graph/graph_updater.py
Incremental world model — maintained as a Pathway Table.

This IS the knowledge graph. Pathway's differential dataflow ensures:
  - Every new tile updates ONLY the affected region
  - No full recompute — O(change) not O(total)
  - Queryable at any point in time (temporal queries)
  - Consistent snapshot even during live updates

World model structure:
  Region node → list of change events + current spectral state
"""
import pathway as pw
from datetime import datetime, timezone
from .region_baseline import get_baseline, compute_ndvi_delta, compute_ndwi_delta


class WorldModelSchema(pw.Schema):
    """One row per region — the current known state of the world."""
    region: str
    last_tile_id: str
    last_updated: int
    current_ndvi: float
    current_ndwi: float
    current_swir: float
    ndvi_delta: float
    ndwi_delta: float
    active_events: int         # count of unresolved events
    highest_severity: str      # worst active severity
    total_tiles_received: int
    last_event_type: str
    last_event_confidence: float


def build_world_model(tiles_table: pw.Table) -> pw.Table:
    """
    Aggregate the tile stream into a per-region world model.

    Uses Pathway's groupby + reduce to maintain a live,
    incrementally-updated summary per region.

    This table is the "knowledge graph" — each region node
    contains its current spectral state and event history.
    """

    @pw.udf
    def severity_rank(severity: str) -> int:
        return {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(severity, 0)

    # Group by region, keep latest values (max timestamp wins)
    world_model = tiles_table.groupby(pw.this.region).reduce(
        region=pw.this.region,
        last_tile_id=pw.reducers.argmax(pw.this.timestamp, pw.this.tile_id),
        last_updated=pw.reducers.max(pw.this.timestamp),
        current_ndvi=pw.reducers.argmax(pw.this.timestamp, pw.this.ndvi),
        current_ndwi=pw.reducers.argmax(pw.this.timestamp, pw.this.ndwi),
        current_swir=pw.reducers.argmax(pw.this.timestamp, pw.this.band_swir),
        total_tiles_received=pw.reducers.count(),
    )

    return world_model


def build_event_summary(events_table: pw.Table) -> pw.Table:
    """
    Aggregate detected events per region.
    Provides the 'alert state' layer of the knowledge graph.
    """
    return events_table.groupby(pw.this.region).reduce(
        region=pw.this.region,
        active_events=pw.reducers.count(),
        last_event_type=pw.reducers.argmax(pw.this.timestamp, pw.this.event_type),
        last_event_ts=pw.reducers.max(pw.this.timestamp),
        last_confidence=pw.reducers.argmax(pw.this.timestamp, pw.this.confidence),
        total_area_ha=pw.reducers.sum(pw.this.area_hectares),
    )


def join_world_model(world_model: pw.Table, event_summary: pw.Table) -> pw.Table:
    """
    Join the spectral state with the event alert state.
    Produces the complete knowledge graph node per region.
    """
    return world_model.join_left(
        event_summary,
        pw.left.region == pw.right.region,
    ).select(
        pw.left.region,
        pw.left.last_tile_id,
        pw.left.last_updated,
        pw.left.current_ndvi,
        pw.left.current_ndwi,
        pw.left.current_swir,
        pw.left.total_tiles_received,
        active_events=pw.coalesce(pw.right.active_events, 0),
        last_event_type=pw.coalesce(pw.right.last_event_type, "none"),
        last_confidence=pw.coalesce(pw.right.last_confidence, 0.0),
        total_affected_ha=pw.coalesce(pw.right.total_area_ha, 0.0),
    )
