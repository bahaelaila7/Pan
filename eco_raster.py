import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.features import rasterize
import numpy as np
import sys
import argparse
from pathlib import Path



if __name__ == '__main__':
    parser = argparse.ArgumentParser("Get Ecoregion ecocodes for pixels")
    parser.add_argument("input_raster", type = Path)
    parser.add_argument("output_raster", type = Path)
    parser.add_argument("--epa_level", type = int, default=4)
    parser.add_argument("--input_epa_shpfile", type = Path, default=Path("../us_eco_l4/us_eco_l4_no_st.shp"))
    parser.add_argument("--output_ecocode_csv", type = Path, default=Path("./epa_l4_ecocodes.csv"))

    args = parser.parse_args()
    assert args.input_raster.exists(), "Input raster file does not exist"
    assert args.input_epa_shpfile.exists(), "Input EPA Ecoregion IV does not exist"

# Load inputs
    gdf = gpd.read_file(args.input_epa_shpfile)


    with rasterio.open(args.input_raster) as src:
        meta = src.meta.copy()
        transform = src.transform
        shape = (src.height, src.width)
        crs = src.crs
        data = src.read(1)
        nodata = src.nodata

# Reproject shapefile to match raster CRS if needed

    if gdf.crs != crs:
        gdf = gdf.to_crs(crs)

    ecocode_field = 'ecocode'
    gdf[ecocode_field] = {1:gdf['NA_L1CODE'], 2:gdf['NA_L2CODE'],3:gdf['NA_L3CODE'], 4:gdf['NA_L3CODE']+'.'+gdf['US_L4CODE']}[args.epa_level]


    ecocode_list = list(enumerate(sorted(set(gdf[ecocode_field])) ,start = 1))
    ecocode_dict = {x:i for i,x in ecocode_list }
    pd.DataFrame(ecocode_list, columns = ['ecocode','epa_l4']).to_csv(args.output_ecocode_csv, index=False)
# Build (geometry, value) pairs for rasterization
    shapes = [(geom, ecocode_dict[value]) for geom, value in zip(gdf.geometry, gdf[ecocode_field])]

# Rasterize
    burned = rasterize(
        shapes=shapes,
        out_shape=shape,
        transform=transform,
        fill=0,          # value for pixels outside all polygons — change as needed
        dtype="int16",   # adjust based on your ID range
        all_touched=False  # True = any pixel touched by polygon edge; False = centroid-in-polygon rule
    )
    if nodata is not None:
        burned[ data == nodata] = 0


# Write output
    meta.update(dtype="int16", count=1, nodata=0)

    with rasterio.open(args.output_raster, "w", **meta) as dst:
        dst.write(burned, 1)
