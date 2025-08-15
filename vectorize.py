from __future__ import annotations
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape
from shapely.ops import unary_union

def mask_to_polygons(mask, transform, crs, min_area_m2=1000.0):
    results = []
    for geom, val in shapes(mask.astype('uint8'), mask=None, transform=transform):
        if val == 1:
            poly = shape(geom)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if poly.is_empty:
                continue
            results.append(poly)
    if not results:
        return gpd.GeoDataFrame(geometry=[], crs=crs)
    gdf = gpd.GeoDataFrame(geometry=results, crs=crs)
    # dissolve tiny internal bits
    gdf['area_m2'] = gdf.geometry.area
    gdf = gdf[gdf['area_m2'] >= min_area_m2].copy()
    gdf.reset_index(drop=True, inplace=True)
    gdf['sandbar_id'] = gdf.index + 1
    return gdf

def save_vector(gdf, path, layer='sandbars'):
    if path.lower().endswith('.gpkg'):
        gdf.to_file(path, layer=layer, driver='GPKG')
    else:
        gdf.to_file(path)  # auto-detect (e.g., GeoJSON, Shapefile)
