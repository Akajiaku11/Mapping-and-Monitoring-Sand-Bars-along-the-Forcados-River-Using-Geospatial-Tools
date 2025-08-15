from __future__ import annotations
import numpy as np
from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_holes, remove_small_objects, binary_opening, disk
from .indices import ndwi, mndwi, ndvi, bsi

def auto_threshold(arr, method='otsu', q=None, mask=None):
    data = arr.copy()
    if mask is not None:
        data = data[mask]
    data = data[np.isfinite(data)]
    if data.size == 0:
        return 0.0
    if method == 'otsu':
        try:
            return float(threshold_otsu(data))
        except Exception:
            # fallback to median if distribution is odd
            return float(np.nanmedian(data))
    elif method == 'quantile':
        if q is None:
            q = 0.5
        return float(np.nanquantile(data, q))
    else:
        raise ValueError("method must be 'otsu' or 'quantile'")

def classify_water(green, nir, swir1, method='mndwi', thr=None, thr_method='otsu', mask=None):
    if method == 'ndwi':
        idx = ndwi(green, nir)
    else:
        idx = mndwi(green, swir1)
    if thr is None:
        thr = auto_threshold(idx, method=thr_method, mask=mask)
    water = idx > thr
    return water, idx, thr

def classify_sandbars(blue, green, red, nir, swir1, water_mask, area_px=100, ndvi_max=0.15, bsi_thr=None, bsi_thr_method='quantile', bsi_q=0.7):
    v_ndvi = ndvi(nir, red)
    v_bsi = bsi(blue, red, nir, swir1)
    if bsi_thr is None:
        bsi_thr = auto_threshold(v_bsi, method=bsi_thr_method, q=bsi_q, mask=~water_mask & np.isfinite(v_bsi))
    # bare and bright
    bare = (v_bsi > bsi_thr) & (v_ndvi < ndvi_max) & (~water_mask)
    # clean
    bare = remove_small_objects(bare, min_size=area_px)
    bare = remove_small_holes(bare, area_threshold=area_px)
    bare = binary_opening(bare, footprint=disk(1))
    return bare, v_bsi, v_ndvi, bsi_thr
