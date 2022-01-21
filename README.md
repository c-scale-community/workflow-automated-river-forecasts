# use-case-high-res-land-surface-drought-analysis
Porting and deploying the High Resolution Land Surface Drought Analysis use case to C-SCALE

## File explanation

* `download_data.py` functionality to download ERA5 and SEAS5 data using the CDS API ([note that a key-file is required](https://cds.climate.copernicus.eu/api-how-to))
* `convert_data.py` functionality to convert downloaded data into suitable forcing input for a `wflow_sbm` model

## Usage
1. Firstly, download the ERA5 and SEAS5 data from the Climate Data Store. The script automatically downloads SEAS5 
data of the current month, and ERA5 data of the previous month. '--output_dir' sets the directory where the downloaded 
files are stored.
```
python download_data.py --output_dir "workdir"
```
2. Resample the downloaded data to the model grid. 
`--dir_downloads` refers to the directory with the downloaded data ('--output_dir' from the previous script), 
and `--output_dir` to the directory where the forcing files are exported to (currently set to the `wflow` model directory). 
See the script for the optional settings (location of model maps, ERA5 and SEAS5 elevation maps, and lapse rate value).
```
python convert_data.py --dir_downloads "workdir" --output_dir "wflow_rhine"
```

3. Run the wflow model with the new forcing, both for ERA5 and SEAS5 data. Model runs need to be performed every month, where 
two types of runs can be identified: (1) catching up with observations from the "historical" period (ERA5), and performing
simulations to cover the forecasted period (SEAS5). The SEAS5 data consists of 50 ensemble members, which cover the uncertainty
range, and wflow needs to simulate each of these members. The following simulation types need to be performed every month (using the 
trigger date of around 2022-01-15 as an example):
 * wflow with ERA5 data, covering 2021-12-01 to 2021-12-31
 * wflow with SEAS5 data, which covers 2022-01-01 to 2022-08-02 (50 times, for each ensemble member)

Both runs need to be initialized, such that the model starts with "warm" states. The wflow model outputs a "oustates.nc" file
in the output directory of every simulation, which can be used to initialize a new simulation. Again using a trigger date of 
around 2022-01-15 as an example, the following states need to be used to initialize the two simulation types
 * wflow+ERA5 data (2021-12): initialized with the outstates from the wflow+ERA5 simulation from the month before (2021-11)
 * wflow+SEAS5 data (2022-01): initialized with the outstates from the most recent wflow+ERA5 simulation (2021-12), same for 
 every ensemble member.

Usage:
```
julia start_wflow.jl --toml_filename "wflow_sbm_base.toml" --output_dir "output_era/" --instates_filename "output_era/outstates.nc" --forcing_filename "data/forcing_ERA5_2021-12-01_2021-12-31.nc"
```
`--toml_filename` refers to the TOML file with the settings for wflow, the exact details for each run will be modified by this 
script, `--instates_filename` to the location where the states are stored to initialize the model with, `--forcing_filename` to 
the location where the forcing file is located (output from `convert_data.py`).

4. Post processing to produce figures/accessible data

Create a figure showing the results of the model output. Currently creates a .png file with the discharge timeseries: a
single line for the ERA5 simulation of the previous months, and 50 timeseries for the SEAS5 simulations starting from the 
current month to 7 months in the future.

Usage:
```
python plot_wflow_results.py --path_to_main_dir "../../" --filename_figure "discharge_ts.png"
```
`--path_to_main_dir` refers to the path of the main folder, which contains the folders `Data`, `Public`, `Share`, and `Software`, 
`--filename_figure` is the filename of the resulting figure (including figure format), which will be saved in the `Public` folder.

## Folder structure

### Current structure
```bash
.
├── Data
│   ├── ERA5_2021_10.nc
│   ├── ERA5_2021_12.nc
│   ├── input
│   │   ├── orography_era5_rhine.grib
│   │   ├── orography_seas5_rhine.grib
│   │   └── staticmaps.nc
│   ├── model
│   │   ├── forcing_ERA5_2021-12-01_2021-12-31.nc
│   │   ├── forcing_SEAS5_ens0_2022-01-01_2022-08-02.nc
│   │   ├── forcing_SEAS5_ens1_2022-01-01_2022-08-02.nc
│   │   ├── forcing_SEAS5_ens2_2022-01-01_2022-08-02.nc
│   │   └── ....
│   ├── model_output
│   │   └── era5
│   │       ├── output.csv
│   │       └── outstates.nc
│   ├── SEAS5_2021_11.nc
│   ├── SEAS5_2022_1.nc
│   └── upper_androscoggin
│       ├── inmaps.nc
│       ├── runwflow.jl
│       ├── sbm_simple.toml
│       └── staticmaps.nc
├── Public
│   └── test.txt
├── Share
│   └── ...
└── Software
    ├── cdsapirc.txt
    ├── images
    │   ├── hrlsa_j.sif
    │   ├── hrlsa.sif
    │   ├── wflow_v0_4_0.sif
    │   └── wflow_wflowjulia.sif
    ├── python
    │   ├── convert_data.py
    │   └── download_data.py
    ├── scripts
    │   ├── prepare_data.sh
    │   ├── prepare.sh
    │   ├── run_wflow.sh
    │   └── wflow.sh
    ├── slurm-972046.out
    ├── slurm-972127.out
    ├── slurm-972157.out
    ├── slurm-972170.out
    ├── slurm-983637.out
    ├── slurm-983638.out
    ├── slurm-983656.out
    ├── slurm-983744.out
    ├── slurm-983745.out
    ├── slurm-984000.out
    ├── slurm-984001.out
    ├── slurm-984002.out
    ├── slurm-984003.out
    └── wflow
        └── wflow_rhine
            ├── forcing.nc
            ├── hydromt_data.yml
            ├── hydromt.log
            ├── inmaps-era5-2020.nc
            ├── instate
            ├── lake_hq_1244.csv
            ├── lake_hq_1248.csv
            ├── lake_hq_14005.csv
            ├── lake_hq_14023.csv
            ├── lake_hq_14029.csv
            ├── lake_sh_1243.csv
            ├── lake_sh_1244.csv
            ├── run_era
            ├── run_wflow.jl
            ├── staticgeoms
            │   ├── basins.geojson
            │   ├── gauges.geojson
            │   ├── gauges_grdc.geojson
            │   ├── gauges_wflow-gauges-extra.geojson
            │   ├── gauges_wflow-gauges-mainsub.geojson
            │   ├── gauges_wflow-gauges-rhineriv.geojson
            │   ├── glaciers.geojson
            │   ├── lakes.geojson
            │   ├── lakes_update.geojson
            │   ├── region.geojson
            │   ├── reservoirs.geojson
            │   ├── rivers.geojson
            │   ├── selected_grdc
            │   │   ├── selected_grdc_01.cpg
            │   │   ├── selected_grdc_01.dbf
            │   │   ├── selected_grdc_01.prj
            │   │   ├── selected_grdc_01.shp
            │   │   └── selected_grdc_01.shx
            │   ├── subcatch_grdc.geojson
            │   ├── subcatch_wflow-gauges-extra.geojson
            │   ├── subcatch_wflow-gauges-mainsub.geojson
            │   └── subcatch_wflow-gauges-rhineriv.geojson
            ├── staticmaps.nc
            ├── wflow_sbm_era.toml
            ├── wflow_sbm_seas.toml
            └── wflow_sbm.toml
```



### Proposed structure
```bash
.
├── Data
│   ├── Model_input
│   │   ├── hydromt_data.yml
│   │   ├── hydromt.log
│   │   ├── lake_hq_1244.csv
│   │   ├── lake_hq_1248.csv
│   │   ├── lake_hq_14005.csv
│   │   ├── lake_hq_14023.csv
│   │   ├── lake_hq_14029.csv
│   │   ├── lake_sh_1243.csv
│   │   ├── lake_sh_1244.csv
│   │   ├── run_wflow.jl                                        # Can this file be moved to the scripts directory?
│   │   ├── staticgeoms
│   │   │   ├── basins.geojson
│   │   │   ├── gauges.geojson
│   │   │   ├── gauges_grdc.geojson
│   │   │   ├── gauges_wflow-gauges-extra.geojson
│   │   │   ├── gauges_wflow-gauges-mainsub.geojson
│   │   │   ├── gauges_wflow-gauges-rhineriv.geojson
│   │   │   ├── glaciers.geojson
│   │   │   ├── lakes.geojson
│   │   │   ├── lakes_update.geojson
│   │   │   ├── region.geojson
│   │   │   ├── reservoirs.geojson
│   │   │   ├── rivers.geojson
│   │   │   ├── selected_grdc
│   │   │   │   ├── selected_grdc_01.cpg
│   │   │   │   ├── selected_grdc_01.dbf
│   │   │   │   ├── selected_grdc_01.prj
│   │   │   │   ├── selected_grdc_01.shp
│   │   │   │   └── selected_grdc_01.shx
│   │   │   ├──  subcatch_grdc.geojson
│   │   │   ├──  subcatch_wflow-gauges-extra.geojson
│   │   │   ├──  subcatch_wflow-gauges-mainsub.geojson
│   │   │   └── subcatch_wflow-gauges-rhineriv.geojson
│   │   ├── staticmaps.nc                                       # Also used by convert_data.py
│   │   └── wflow_sbm_base.toml                                 # With baseline settings, details are adjusted by start_wflow.jl
│   ├── Forcing
│   │   ├── downloaded                                          # To store files created by download_data.py 
│   │   │   ├── ERA5_2021_12.nc
│   │   │   └── SEAS5_2022_1.nc
│   │   └── converted                                           # To store files created by convert_data.py, also required to run wflow
│   │   │   ├── forcing_ERA5_2021-12-01_2021-12-31.nc
│   │   │   ├── forcing_SEAS5_ens0_2022-01-01_2022-08-02.nc
│   │   │   ├── forcing_SEAS5_ens1_2022-01-01_2022-08-02.nc
│   │   │   ├── forcing_SEAS5_ens2_2022-01-01_2022-08-02.nc
│   │   │   └── ...
│   │   ├── orography_era5_rhine.grib                           # Required for convert_data.py
│   │   └── orography_seas5_rhine.grib                          # Required for convert_data.py
│   └── Model_output                                            # To store results of the model simulation
│       ├── run_ERA5_2021_11                                    # ERA5 simulation result, directory name contains year_month of the simulated period
│       │   ├── output.csv
│       │   ├── output.nc
│       │   └── outstates.nc                                    # Required to initialize the ERA5_2021_12 simulation
│       ├── run_ERA5_2021_12                                    # ERA5 simulation result, directory name contains year_month of the simulated period
│       │   ├── output.csv
│       │   ├── output.nc
│       │   └── outstates.nc                                    # Required to initialize the SEAS5_ensX_2022_1 simulations
│       ├── run_SEAS5_ens0_2022_01                              # SEAS5 ensemble X simulation result, directory name contains year_month of the start of the simulated period
│       │   ├── output.csv
│       │   ├── output.nc
│       │   └── outstates.nc
│       ├── run_SEAS5_ens1_2022_01
│       │   ├── output.csv
│       │   ├── output.nc
│       │   └── outstates.nc
│       └── ...
├── Public                                                      # Directory to store output (figures/processed model output) in, accessible from "outside"
│   └── test.txt
├── Share
│   └── ...
└── Software
    ├── cdsapirc.txt
    ├── images
    │   ├── hrlsa_j.sif
    │   ├── hrlsa.sif
    │   ├── wflow_v0_4_0.sif
    │   └── wflow_wflowjulia.sif
    ├── python
    │   ├── convert_data.py
    │   └── download_data.py
    ├── scripts
    │   ├── prepare_data.sh
    │   ├── prepare.sh
    │   ├── run_wflow.sh
    │   └── wflow.sh
    ├── slurm-972046.out
    ├── slurm-972127.out
    ├── slurm-972157.out
    ├── slurm-972170.out
    ├── slurm-983637.out
    ├── slurm-983638.out
    ├── slurm-983656.out
    ├── slurm-983744.out
    ├── slurm-983745.out
    ├── slurm-984000.out
    ├── slurm-984001.out
    ├── slurm-984002.out
    └── slurm-984003.out
```    