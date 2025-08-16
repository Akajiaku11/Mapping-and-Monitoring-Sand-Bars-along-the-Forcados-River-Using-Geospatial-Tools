# Mapping and Monitoring Sand Bars along the Forcados River Using Geospatial Tools

This project provides a **reproducible Python pipeline** and an optional **Streamlit app** to map and monitor sand bars along the Forcados River (or any river) from multi-date satellite imagery (e.g., Sentinel‑2 or Landsat).

## Features
- Preprocess & clip multi-band GeoTIFFs to an Area of Interest (AOI).
- Compute indices (NDWI, MNDWI, NDVI, BSI) for water/bare soil discrimination.
- Classify **water** and **sand bar** masks with Otsu/quantile thresholds.
- Morphological clean-up and connected-component filtering by minimum area.
- Vectorize masks to polygons and compute **area statistics**.
- **Change detection** across dates (gains/losses/persistence).
- Figure exports and a **Streamlit** viewer for quick QA.
- CRS-aware, uses `rasterio`, `geopandas`, `numpy`, `scikit-image`.

> **Inputs**: Multi-band GeoTIFF(s) with at least: Blue, Green, Red, NIR, SWIR1; and an AOI polygon (GeoPackage/GeoJSON/Shapefile).  
> **Outputs**: Clean sand-bar polygons, per-scene stats CSV, and change maps/CSV across dates.

## Quick Start
1. Create and activate a Python 3.10+ environment.
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Prepare inputs (place in `data/`):
   - Imagery (e.g., `S2_2024-01-05_Forcados.tif`, `S2_2025-01-07_Forcados.tif`), reprojected to a **projected CRS** (e.g., UTM 31N EPSG:32631 or a suitable local UTM).
   - AOI file: `aoi.geojson` (single polygon covering river corridor).
4. Edit `config/example_config.yaml` or pass CLI flags.
5. Run the pipeline for one date:
   ```bash
   python scripts/run_pipeline.py      --image data/S2_2024-01-05_Forcados.tif      --aoi data/aoi.geojson      --outdir outputs/2024-01-05
   ```
6. Run change detection across multiple dated outputs:
   ```bash
   python scripts/run_pipeline.py --change      --inputs outputs/2024-01-05/sandbars.gpkg outputs/2025-01-07/sandbars.gpkg      --outdir outputs/change_2024_2025
   ```

## Streamlit App (optional)
```bash
streamlit run app/streamlit_app.py
```
Then select imagery, AOI, and thresholds interactively.

## Notes
- If your imagery is top-of-atmosphere reflectance with 0–1 scale, indices work directly. If DN-scaled (0–10000), set `--scale 10000`.
- Tweak thresholds using quantiles if Otsu fails (e.g., cloudy scenes).
- 
- Ensure AOI CRS matches imagery or let the pipeline reproject automatically.
https://github.com/Akajiaku11
---

