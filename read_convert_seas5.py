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

def convert_seasonal_forecast(filename, dem_model, dem_forcing, 
                              lapse_rate=-0.0065, crs=4326):
    
    # Open seasonal forecast and set CRS
    # TODO CHUNKS CAN BE ADJUSTED WHEN RUNNING IN THE CLOUD?
    seas = xr.open_dataset(filename, chunks = {"number": 1, "time" : 500})
    seas = seas.rio.write_crs(crs)

    # Loop through ensembles
    idx = 0
    for ensemble in seas.number:
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
        t_out = t_sea_level.rio.reproject_match(dem_model)
        precip = tmp_tp.rio.reproject_match(dem_model)
        
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
        forcing.to_netcdf(
            "forcing_SEAS5_ens{}_{}_{}.nc".format(
                idx,
                forcing.time[0].dt.strftime('%Y-%m-%d').values,
                forcing.time[-1].dt.strftime('%Y-%m-%d').values
                ),
            encoding=encoding,
            )
        
        idx += 1
        



if __name__ == "__main__":
    
    dem_model = get_dem_model(staticmapfile = "staticmaps.nc")
    dem_forcing = get_dem_forcing(filename = "orography_seas5_rhine.grib")
    
    convert_seasonal_forecast(
        filename = r"p:\wflow_global\forcing\SEAS5\SEAS5_2019_01.nc",
        dem_model = dem_model, dem_forcing = dem_forcing)
