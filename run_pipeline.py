from __future__ import annotations
import os
import typer
import geopandas as gpd
import pandas as pd
import numpy as np
from rasterio.transform import Affine
import rasterio
from sandbars.raster_utils import read_multiband, clip_to_aoi, save_mask
from sandbars.classify import classify_water, classify_sandbars
from sandbars.vectorize import mask_to_polygons, save_vector
from sandbars.plotting import plot_polygons_over_rgb
from sandbars.change import load_sandbars, compare_two, change_stats, save_change_layers

app = typer.Typer(add_completion=False)

@app.command()
def process(
    image: str = typer.Option(..., help="Path to multi-band GeoTIFF (Blue,Green,Red,NIR,SWIR1 order by default)"),
    aoi: str = typer.Option(..., help="Path to AOI polygon (GeoJSON/GPKG/SHP)"),
    outdir: str = typer.Option("outputs", help="Output directory"),
    scale: float = typer.Option(1.0, help="Scale to divide the DN values (e.g., 10000 for Sentinel-2 L2A)"),
    band_blue: int = 1,
    band_green: int = 2,
    band_red: int = 3,
    band_nir: int = 4,
    band_swir1: int = 5,
    water_method: str = "mndwi",
    water_thr: float = None,
    water_thr_method: str = "otsu",
    sand_min_area_px: int = 100,
    sand_ndvi_max: float = 0.15,
    sand_bsi_thr: float = None,
    sand_bsi_thr_method: str = "quantile",
    sand_bsi_q: float = 0.7,
    min_area_m2: float = 500.0,
    preview_png: bool = True
):
    os.makedirs(outdir, exist_ok=True)
    band_map = {'blue':band_blue,'green':band_green,'red':band_red,'nir':band_nir,'swir1':band_swir1}
    arrs, profile = read_multiband(image, scale=scale, band_map=band_map)
    # Ensure essential profile fields exist
    with rasterio.open(image) as ds:
        profile = ds.profile

    clipped, aoi_mask = clip_to_aoi(arrs, profile, aoi)

    water_mask, mndwi_arr, used_thr = classify_water(clipped['green'], clipped['nir'], clipped['swir1'],
                                                     method=water_method, thr=water_thr, thr_method=water_thr_method,
                                                     mask=aoi_mask)

    sand_mask, bsi_arr, ndvi_arr, bsi_thr = classify_sandbars(clipped['blue'], clipped['green'], clipped['red'],
                                                              clipped['nir'], clipped['swir1'], water_mask,
                                                              area_px=sand_min_area_px, ndvi_max=sand_ndvi_max,
                                                              bsi_thr=sand_bsi_thr, bsi_thr_method=sand_bsi_thr_method,
                                                              bsi_q=sand_bsi_q)

    # Save masks
    save_mask(os.path.join(outdir, "water_mask.tif"), water_mask, profile)
    save_mask(os.path.join(outdir, "sandbar_mask.tif"), sand_mask, profile)

    # Vectorize
    gdf = mask_to_polygons(sand_mask, profile['transform'], profile['crs'], min_area_m2=min_area_m2)
    gdf['area_m2'] = gdf.geometry.area
    gdf.to_file(os.path.join(outdir, "sandbars.gpkg"), driver="GPKG")
    # Stats
    stats = gdf[['sandbar_id','area_m2']].copy()
    stats.to_csv(os.path.join(outdir, "sandbar_stats.csv"), index=False)

    # Preview
    if preview_png:
        try:
            plot_polygons_over_rgb(image, gdf, out_png=os.path.join(outdir, "sandbars_over_rgb.png"))
        except Exception as e:
            print(f"Preview failed: {e}")

    typer.echo(f"Done. Sand bars: {len(gdf)}; total area m^2: {gdf['area_m2'].sum():.2f}")
    typer.echo(f"Water threshold: {used_thr:.4f}; BSI threshold: {bsi_thr:.4f}")

@app.command()
def change(
    inputs: list[str] = typer.Option(..., help="List of sandbar polygon files (e.g., outputs/DATE/sandbars.gpkg), at least two", rich_help_panel="Change"),
    outdir: str = typer.Option("outputs/change", help="Output directory for change layers"),
):
    if len(inputs) < 2:
        raise typer.BadParameter("Provide at least two sandbar polygon files for change detection.")
    os.makedirs(outdir, exist_ok=True)
    frames = load_sandbars(inputs)
    early = frames[0]
    late = frames[-1]
    # reproject to common CRS if needed
    if early.crs != late.crs:
        late = late.to_crs(early.crs)

    gained, lost, persisted = compare_two(early, late)
    stats = change_stats(gained, lost, persisted, early.crs)
    stats.to_csv(os.path.join(outdir, "sandbar_change_stats.csv"), index=False)
    save_change_layers(gained, lost, persisted, early.crs, os.path.join(outdir, "sandbar_change"))
    print("Change detection saved.")

if __name__ == "__main__":
    app()
