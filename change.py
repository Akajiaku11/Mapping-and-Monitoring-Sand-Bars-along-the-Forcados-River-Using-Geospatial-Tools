from __future__ import annotations
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from shapely.ops import unary_union

def load_sandbars(paths):
    frames = []
    for p in paths:
        gdf = gpd.read_file(p)
        if 'date' not in gdf.columns:
            # try parse from parent directory name or filename
            import os, re
            date_guess = None
            base = os.path.basename(os.path.dirname(p)) + '_' + os.path.basename(p)
            m = re.search(r'(\d{4}-\d{2}-\d{2})', base)
            if m:
                date_guess = m.group(1)
            gdf['date'] = date_guess or 'unknown'
        frames.append(gdf[['sandbar_id','area_m2','geometry','date']].copy())
    return frames

def compare_two(gdf_early, gdf_late):
    early_union = unary_union(gdf_early.geometry)
    late_union = unary_union(gdf_late.geometry)
    gained = late_union.difference(early_union)
    lost = early_union.difference(late_union)
    persisted = late_union.intersection(early_union)
    return gained, lost, persisted

def change_stats(gained, lost, persisted, crs):
    import geopandas as gpd
    rows = []
    if not gained.is_empty:
        g = gpd.GeoDataFrame(geometry=[gained], crs=crs)
        rows.append({'class':'gained','area_m2':g.geometry.area.sum()})
    else:
        rows.append({'class':'gained','area_m2':0.0})
    if not lost.is_empty:
        g = gpd.GeoDataFrame(geometry=[lost], crs=crs)
        rows.append({'class':'lost','area_m2':g.geometry.area.sum()})
    else:
        rows.append({'class':'lost','area_m2':0.0})
    if not persisted.is_empty:
        g = gpd.GeoDataFrame(geometry=[persisted], crs=crs)
        rows.append({'class':'persisted','area_m2':g.geometry.area.sum()})
    else:
        rows.append({'class':'persisted','area_m2':0.0})
    return gpd.GeoDataFrame(rows)

def save_change_layers(gained, lost, persisted, crs, out_prefix):
    import geopandas as gpd
    if not gained.is_empty:
        gpd.GeoDataFrame(geometry=[gained], crs=crs).to_file(f"{out_prefix}_gained.gpkg", driver='GPKG')
    if not lost.is_empty:
        gpd.GeoDataFrame(geometry=[lost], crs=crs).to_file(f"{out_prefix}_lost.gpkg", driver='GPKG')
    if not persisted.is_empty:
        gpd.GeoDataFrame(geometry=[persisted], crs=crs).to_file(f"{out_prefix}_persisted.gpkg", driver='GPKG')
