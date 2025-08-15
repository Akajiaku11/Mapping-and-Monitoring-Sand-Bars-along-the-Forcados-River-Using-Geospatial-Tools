import streamlit as st
import geopandas as gpd
import rasterio
import numpy as np
import pandas as pd
from rasterio.plot import reshape_as_image
from sandbars.raster_utils import read_multiband, clip_to_aoi
from sandbars.classify import classify_water, classify_sandbars
from sandbars.vectorize import mask_to_polygons
from sandbars.plotting import plot_polygons_over_rgb

st.set_page_config(page_title="Sand Bars Mapper", layout="wide")

st.title("Mapping & Monitoring Sand Bars")

image = st.text_input("Path to multi-band GeoTIFF", "data/S2_2024-01-05_Forcados.tif")
aoi = st.text_input("Path to AOI (GeoJSON/GPKG/SHP)", "data/aoi.geojson")
scale = st.number_input("Scale (divide DN)", value=1.0)

col1, col2, col3, col4, col5 = st.columns(5)
band_blue = col1.number_input("Blue band", min_value=1, value=1)
band_green = col2.number_input("Green band", min_value=1, value=2)
band_red = col3.number_input("Red band", min_value=1, value=3)
band_nir = col4.number_input("NIR band", min_value=1, value=4)
band_swir1 = col5.number_input("SWIR1 band", min_value=1, value=5)

water_method = st.selectbox("Water index", ["mndwi","ndwi"])
water_thr_method = st.selectbox("Water threshold method", ["otsu","quantile"])
water_thr = st.number_input("Water threshold (leave 0 for auto)", value=0.0, format="%.4f")
sand_min_area_px = st.number_input("Sand: min component size (pixels)", value=100, step=10)
sand_ndvi_max = st.number_input("Sand: NDVI max", value=0.15, format="%.2f")
sand_bsi_thr_method = st.selectbox("Sand BSI threshold method", ["quantile","otsu"])
sand_bsi_q = st.slider("Sand BSI quantile (if used)", min_value=0.5, max_value=0.95, value=0.7, step=0.01)
sand_bsi_thr = st.number_input("Sand BSI threshold (leave 0 for auto)", value=0.0, format="%.4f")
min_area_m2 = st.number_input("Min polygon area (m²)", value=500.0, step=50.0)

run = st.button("Run")

if run:
    try:
        band_map = {'blue':band_blue,'green':band_green,'red':band_red,'nir':band_nir,'swir1':band_swir1}
        arrs, profile = read_multiband(image, scale=scale, band_map=band_map)
        with rasterio.open(image) as ds:
            profile = ds.profile
        clipped, aoi_mask = clip_to_aoi(arrs, profile, aoi)

        wt, idx, thr = classify_water(clipped['green'], clipped['nir'], clipped['swir1'], method=water_method,
                                      thr=None if water_thr==0 else water_thr, thr_method=water_thr_method, mask=aoi_mask)
        sb, v_bsi, v_ndvi, bthr = classify_sandbars(clipped['blue'], clipped['green'], clipped['red'],
                                                    clipped['nir'], clipped['swir1'], wt,
                                                    area_px=int(sand_min_area_px), ndvi_max=float(sand_ndvi_max),
                                                    bsi_thr=None if sand_bsi_thr==0 else sand_bsi_thr,
                                                    bsi_thr_method=sand_bsi_thr_method, bsi_q=float(sand_bsi_q))
        gdf = mask_to_polygons(sb, profile['transform'], profile['crs'], min_area_m2=float(min_area_m2))
        st.success(f"Sand bars detected: {len(gdf)}; Total area m²: {gdf.geometry.area.sum():.1f}")
        st.dataframe(gdf.drop(columns='geometry'))

        # Preview overlay
        try:
            out_png = plot_polygons_over_rgb(image, gdf, out_png=None)
            st.pyplot()
        except Exception as e:
            st.warning(f"Preview failed: {e}")

    except Exception as e:
        st.error(str(e))
