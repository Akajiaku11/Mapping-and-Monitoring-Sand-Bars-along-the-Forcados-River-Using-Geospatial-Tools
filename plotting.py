from __future__ import annotations
import matplotlib.pyplot as plt
import geopandas as gpd
import rasterio
import numpy as np

def quickplot_rgb(raster_path, bands=(3,2,1), scale=1.0, out_png=None, aoi_path=None):
    with rasterio.open(raster_path) as ds:
        rgb = np.stack([ds.read(b) for b in bands]).astype('float32')
    if scale != 1.0:
        rgb = rgb / float(scale)
    rgb = np.clip(rgb / np.nanpercentile(rgb, 99), 0, 1)
    plt.figure()
    plt.imshow(np.transpose(rgb, (1,2,0)))
    plt.title("RGB Preview")
    plt.axis('off')
    if aoi_path:
        try:
            aoi = gpd.read_file(aoi_path).to_crs(ds.crs)
            aoi.boundary.plot(ax=plt.gca(), linewidth=1)
        except Exception:
            pass
    if out_png:
        plt.savefig(out_png, dpi=200, bbox_inches='tight')
    return out_png

def plot_polygons_over_rgb(raster_path, poly_gdf, out_png=None, bands=(3,2,1), scale=1.0, title="Sand Bars"):
    with rasterio.open(raster_path) as ds:
        rgb = np.stack([ds.read(b) for b in bands]).astype('float32')
        crs = ds.crs
    if scale != 1.0:
        rgb = rgb / float(scale)
    rgb = np.clip(rgb / np.nanpercentile(rgb, 99), 0, 1)
    plt.figure()
    plt.imshow(np.transpose(rgb, (1,2,0)))
    plt.title(title)
    plt.axis('off')
    try:
        poly_gdf.to_crs(crs).boundary.plot(ax=plt.gca(), linewidth=1)
    except Exception:
        pass
    if out_png:
        plt.savefig(out_png, dpi=200, bbox_inches='tight')
    return out_png
