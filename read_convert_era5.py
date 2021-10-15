# -*- coding: utf-8 -*-
"""
Created on Fri Oct 15 13:56:03 2021

@author: Buitink
"""

import numpy as np
import xarray as xr
import rasterio, rioxarray
from hydromt import workflows
import geopandas as gpd

def temp_correction(dem, lapse_rate=-0.0065):

    """Temperature correction based on elevation data.

    Parameters
    ----------
    dem : xarray.DataArray
        DataArray with elevation
    lapse_rate : float, default -0.0065
        lapse rate of temperature [°C m-1]

    Returns
    -------
    temp_add : xarray.DataArray
        temperature addition
    """

    temp_add = (dem * lapse_rate)#.fillna(0)

    return temp_add


def get_dem_model(staticmapfile, dem_varname = "wflow_dem", crs=4326):
    # Read model static maps, and set crs
    modelmaps = xr.open_dataset(staticmapfile)
    modelmaps = modelmaps.rio.write_crs(crs)
    dem_model = modelmaps[dem_varname]
    return dem_model

def get_dem_forcing(filename):
    data = xr.open_rasterio(filename)
    data = data.sel(band=1)
    data = data/9.80665 # Correct from m2/s2 to m
    return data

def convert_era(filename, dem_model, dem_forcing, 
                              lapse_rate=-0.0065, crs=4326):
    
    # Open seasonal forecast and set CRS
    # TODO CHUNKS CAN BE ADJUSTED WHEN RUNNING IN THE CLOUD?
    era = xr.open_dataset(filename, chunks = {"time" : 500})
    era = era.rio.write_crs(crs)

    era = era.resample(time = "D", label = "left", closed = "left").mean()
    era = era.rename({"longitude": "x", "latitude": "y"})

    # Convert correct units
    t2m = era.t2m - 273.15
    tp = era.tp * 1000
    msl = era.msl
    ssrd = era.ssrd / 86400
    
    # Rename coords
    # t2m = t2m.rename({"longitude": "x", "latitude": "y"})
    # tp = tp.rename({"longitude": "x", "latitude": "y"})


    # Apply lapse rate to temperature
    t_add_sea_level = temp_correction(dem_forcing)
    t_sea_level = t2m - t_add_sea_level
    
    # Slice and reproject temperature to model grid, and fix coordnames
    t_out = t_sea_level.rio.reproject_match(dem_model)
    precip = tp.rio.reproject_match(dem_model)
    
    # correct temperature based on high-res DEM
    t_add_elevation = temp_correction(dem_model, lapse_rate = lapse_rate)
    # Make sure both have the same x and y coords
    t_out = t_out.assign_coords(x = t_add_elevation.x,
                                y = t_add_elevation.y)
    precip = precip.assign_coords(x = t_add_elevation.x,
                                  y = t_add_elevation.y)
    # Correct temperature and set a name
    temperature = t_out + t_add_elevation
    temperature.name = "t2m"

    # Prepare PET input file    
    petinput = msl.to_dataset()
    petinput = petinput.rename({"msl" : "press_msl"})
    petinput["kin"] = ssrd
    petinput = petinput.compute()
    
    # Calculate PET
    pet = workflows.forcing.pet(
        ds = petinput, 
        temp = temperature, 
        dem_model = dem_model,
        method = "makkink", 
        press_correction = True
        )
    
    # Combine PET, T, TEMP into a single dataset 
    forcing = xr.merge([precip, temperature, pet])
    forcing = forcing.rename({"t2m": "TEMP",
                              "tp": "P",
                              "pet": "PET"})
    # Slice to basin
    forcing = forcing.where(~np.isnan(dem_model))
    
    # Define decoding
    encoding = {
                v: {"zlib": True, "dtype": "float32" }
                for v in forcing.data_vars.keys()
            }
    
    # Export to NetCDF
    forcing.to_netcdf(
        "forcing_ERA5_{}_{}.nc".format(forcing.time[0].dt.strftime('%Y-%m-%d').values,
                                       forcing.time[-1].dt.strftime('%Y-%m-%d').values
                                       ),
        encoding=encoding,
        )


if __name__ == "__main__":
    
    dem_model = get_dem_model(staticmapfile = "staticmaps.nc")
    dem_forcing = get_dem_forcing(filename = "orography_era5_rhine.grib")
    
    filename = r"p:\wflow_global\forcing\SEAS5\ERA5_2019_05.nc"
    crs = 4326
    
    convert_era(
        filename = r"p:\wflow_global\forcing\SEAS5\ERA5_2019_05.nc",
        dem_model = dem_model, dem_forcing = dem_forcing)