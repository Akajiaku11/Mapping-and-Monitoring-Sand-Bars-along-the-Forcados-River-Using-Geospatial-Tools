from __future__ import annotations
import rasterio
from rasterio.features import geometry_mask
from rasterio.mask import mask
from rasterio.enums import Resampling
from rasterio.warp import transform_geom
import numpy as np
import geopandas as gpd
from shapely.geometry import mapping

def read_multiband(path, scale=1.0, band_map=None):
    """
    Reads a multiband GeoTIFF and returns dict of arrays keyed by logical band names.
    band_map: dict mapping logical names to raster band indices (1-based). Defaults to Sentinel-2: 
       {'blue':1,'green':2,'red':3,'nir':4,'swir1':5}
    """
    if band_map is None:
        band_map = {'blue':1,'green':2,'red':3,'nir':4,'swir1':5}
    with rasterio.open(path) as ds:
        arrs = {}
        for name, idx in band_map.items():
            band = ds.read(idx).astype('float32')
            if scale != 1.0:
                band = band / float(scale)
            arrs[name] = band
        profile = ds.profile
    return arrs, profile

def reproject_geom_to_crs(geom, src_crs, dst_crs):
    return transform_geom(src_crs, dst_crs, geom)

def clip_to_aoi(arrs, profile, aoi_path):
    with rasterio.open(profile['driver'] if False else profile.get('name',''), 'r') as _:
        pass
    # We can't reopen from profile; open from original path isn't provided. Instead, derive a mask using an in-memory geometry mask.
    # We'll reopen the dataset path to use rasterio.mask properly.
    # For simplicity, require profile contains 'transform', 'height', 'width', and 'crs'.
    gdf = gpd.read_file(aoi_path)
    if gdf.empty:
        raise ValueError("AOI geometry is empty.")
    # Assume single polygon AOI
    aoi_geom = gdf.geometry.unary_union
    aoi_geom = mapping(aoi_geom)
    # Build mask over current arrays/grid
    transform = profile['transform']
    invert = False
    mask_arr = geometry_mask([aoi_geom], out_shape=(profile['height'], profile['width']),
                             transform=transform, invert=True)
    clipped = {k: np.where(mask_arr, v, np.nan) for k,v in arrs.items()}
    return clipped, mask_arr

def save_raster(path, array, profile, nodata=np.nan):
    new_prof = profile.copy()
    if array.ndim == 2:
        new_prof.update({'count':1, 'dtype':'float32', 'nodata':nodata})
    elif array.ndim == 3:
        new_prof.update({'count':array.shape[0], 'dtype':'float32', 'nodata':nodata})
    else:
        raise ValueError("array must be 2D or 3D")
    with rasterio.open(path, 'w', **new_prof):
        if array.ndim == 2:
            rasterio.open(path).write(array.astype('float32'), 1)
        else:
            for i in range(array.shape[0]):
                rasterio.open(path).write(array[i].astype('float32'), i+1)

def save_mask(path, mask_bool, profile, nodata=0):
    new_prof = profile.copy()
    new_prof.update({'count':1, 'dtype':'uint8', 'nodata':nodata})
    with rasterio.open(path, 'w', **new_prof) as dst:
        dst.write(mask_bool.astype('uint8'), 1)
