# -*- coding: utf-8 -*-
"""
Created on Fri Oct 29 14:33:40 2021
@author: Buitink
"""
import os
import click
import logging
import numpy as np
import xarray as xr
from dateutil.relativedelta import relativedelta
from hydromt import workflows
from datetime import datetime

@click.command()
@click.option('--dir_downloads', required=True, type=str, help='Path where the downloaded ERA5 and SEAS5 data is stored',)
@click.option('--output_dir', required=True, type=str, help='Path to store the convert forcing files',)
@click.option('--date_string', required=True, type=str, help='String with year and month of current month (in YYYY_MM format)',)

# Optional settings
@click.option('--wflow_staticmaps_file', default="wflow_rhine/staticmaps.nc",
              type=str, help='NetCDF with all the staticmaps (including wflow_dem)')
@click.option('--era5_dem_file', default="orography_era5_rhine.grib",
              type=str, help='Raster file with ERA5 orography data (geopotential height)')
@click.option('--seas5_dem_file', default="orography_seas5_rhine.grib",
              type=str, help='Raster file with SEAS5 orography data (geopotential height)')
@click.option('--lapse_rate', default=-0.0065,
              type=float, help='Lapse rate for temperature correction')

def convert_data(dir_downloads, date_string, wflow_staticmaps_file, era5_dem_file,
                 seas5_dem_file, lapse_rate, output_dir):

    # Prepare logger
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')


    # Get current date, for month and year information
    current_date = datetime.strptime(date_string, '%Y_%m').date()
    current_month = current_date.month
    current_year = current_date.year

    previous_date = current_date - relativedelta(months=1)
    prev_month = previous_date.month
    prev_year = previous_date.year


    # Extract wflow model DEM from staticmaps
    dem_model = get_dem_model(staticmapfile = wflow_staticmaps_file)

    # ERA5 convert
    era5_file = os.path.join(dir_downloads, f'ERA5_{prev_year}_{prev_month}.nc')
    dem_era5 = get_dem_forcing(era5_dem_file)
    logging.info("Start converting of ERA5 dataset")
    convert_era5(filename=era5_file, dem_model=dem_model, dem_forcing=dem_era5,
                  lapse_rate=lapse_rate, crs=4326, output_dir=output_dir)
    logging.info("Copmleted converting of ERA5 dataset")

    # SEAS5 convert
    seas5_file = os.path.join(dir_downloads, f'SEAS5_{current_year}_{current_month}.nc')
    dem_seas5 = get_dem_forcing(seas5_dem_file)
    logging.info("Start converting of SEAS5 dataset")
    convert_seas5(filename=seas5_file, dem_model=dem_model, dem_forcing=dem_seas5,
                  lapse_rate=lapse_rate, crs=4326, output_dir=output_dir, log=logging)
    logging.info("Copmleted converting of SEAS5 dataset")



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
    modelmaps.raster.set_crs(crs)
    dem_model = modelmaps[dem_varname]
    return dem_model

def get_dem_forcing(filename):
    data = xr.open_rasterio(filename)
    data = data.sel(band=1)
    data = data/9.80665 # Correct from m2/s2 to m
    return data

def convert_era5(filename, dem_model, dem_forcing, output_dir,
                 lapse_rate=-0.0065, crs=4326):

    # Open seasonal forecast and set CRS
    # TODO CHUNKS CAN BE ADJUSTED WHEN RUNNING IN THE CLOUD?
    era= xr.open_dataset(filename, chunks = {"time" : 500})
    era.raster.set_crs(crs)

    # expver variable is added for recent ERA data
    if "expver" in era.variables:
        era = era.reduce(np.nansum, dim='expver',keep_attrs=True)

    era = era.resample(time = "D", label = "left", closed = "left").mean()
    era = era.rename({"longitude": "x", "latitude": "y"})

    # Convert correct units
    t2m = era.t2m - 273.15
    tp = era.tp * 1000 * 24
    msl = era.msl
    ssrd = era.ssrd / 86400

    # Apply lapse rate to temperature
    t_add_sea_level = temp_correction(dem_forcing)
    t_sea_level = t2m - t_add_sea_level

    # Slice and reproject temperature to model grid, and fix coordnames
    t_out = t_sea_level.raster.reproject_like(dem_model)
    precip = tp.raster.reproject_like(dem_model)

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
    forcing.to_netcdf(os.path.join(output_dir,
        "forcing_ERA5_{}_{}.nc".format(
            forcing.time[0].dt.strftime('%Y-%m-%d').values,
            forcing.time[-1].dt.strftime('%Y-%m-%d').values
            )),
        encoding=encoding,
        )

def convert_seas5(filename, dem_model, dem_forcing, output_dir, log,
                  lapse_rate=-0.0065, crs=4326):

    # Open seasonal forecast and set CRS
    # TODO CHUNKS CAN BE ADJUSTED WHEN RUNNING IN THE CLOUD?
    seas = xr.open_dataset(filename, chunks = {"number": 1, "time" : 500})
    seas.raster.set_crs(crs)

    # Loop through ensembles
    idx = 0
    for ensemble in seas.number:
        log.info(f"Converting SEAS5 ensemble {ensemble.values}")
        # Extract ensemble
        tmp = seas.sel(number=ensemble).load()

        # Resample to same timestep (daily)
        # TODO CHECK CLOSED SETTING, I think this is correct
        tmp = tmp.resample(time = "D", label = "left", closed = "right").mean()
        tmp = tmp.rename({"latitude" : "y", "longitude": "x"})

        # Correct values (remove aggregation) ssrd and tp
        # TODO: SHOULD THIS BE SHIFTED BY ONE DAY?, probably fixable with right label and closed settings above
        tmp_tp = tmp.tp.diff(dim = "time", label = "lower")
        tmp_ssrd = tmp.ssrd.diff(dim = "time", label = "lower")

        # Convert correct units
        tmp_t2m = tmp.t2m - 273.15 # K to C
        tmp_ssrd = tmp_ssrd / 86400 # J m-2 to W m-2 (assuming J day-1)
        tmp_tp = tmp_tp * 1000 # m to mm
        # Remove negative values
        tmp_tp = tmp_tp.where(tmp_tp > 0, 0)

        # Apply lapse rate to temperature
        t_add_sea_level = temp_correction(dem_forcing)
        t_sea_level = tmp_t2m - t_add_sea_level

        # Slice and reproject temperature to model grid, and fix coordnames
        t_out = t_sea_level.raster.reproject_like(dem_model)
        precip = tmp_tp.raster.reproject_like(dem_model)

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
        petinput = tmp.msl.to_dataset()
        petinput = petinput.rename({"msl" : "press_msl"})
        petinput["kin"] = tmp_ssrd
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

        # Drop last timestep, as this contains NaNs for P and SSRD
        forcing = forcing.sel(time=forcing.time[:-1])

        # Define decoding
        encoding = {
                    v: {"zlib": True, "dtype": "float32" }
                    for v in forcing.data_vars.keys()
                }
        # Export to netcdf
        forcing.to_netcdf(os.path.join(output_dir,
            "forcing_SEAS5_ens{}_{}_{}.nc".format(
                idx,
                forcing.time[0].dt.strftime('%Y-%m-%d').values,
                forcing.time[-1].dt.strftime('%Y-%m-%d').values
                )),
            encoding=encoding,
            )

        idx += 1

if __name__ == "__main__":
    convert_data()

    # LOCAL TESTING
    # dir_downloads = r"c:\Users\buitink\Documents\Projects\cscale\testing\downloads\\"
    # date_string = "2022_04"
    # wflow_staticmaps_file = r"c:\Users\buitink\Documents\Projects\cscale\wflow_rhine\staticmaps.nc"
    # era5_dem_file = r"c:\Users\buitink\Documents\Projects\cscale\testing\downloads\orography_era5.grib"
    # seas5_dem_file = r"c:\Users\buitink\Documents\Projects\cscale\testing\downloads\orography_seas5.grib"
    # lapse_rate = -0.0065
    # output_dir = r"c:\Users\buitink\Documents\Projects\cscale\testing\converted\\"

    # convert_data(dir_downloads, date_string, wflow_staticmaps_file, era5_dem_file,
    #                  seas5_dem_file, lapse_rate, output_dir)