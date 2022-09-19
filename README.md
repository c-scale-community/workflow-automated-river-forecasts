# use-case-high-res-land-surface-drought-analysis
Porting and deploying the High Resolution Land Surface Drought Analysis use case to C-SCALE

## Upload files to spider
```
rsync -W -e "ssh -i <<your private key>>" hrlsa.sif <<your surf email>>@spider.surfsara.nl:/project/hrlsa/<<target>>
```
## File explanation

### Bash scripts
The bash scripts are used to define and run the several steps in the workflow. Each step
consists of a separate bash script, which calls the relevant python script (or Wflow
executable). The `workflow.sh` contains all steps and does not require specific user input, as
the date is automatically retrieved (ensuring all input and output settings are correct). The
following bash scripts called by the `workflow.sh` script:
* `prepare.sh` takes care of downloading ERA5 and SEAS5 data, and converts the downloaded file
  into Wflow import (see `download_data.py` and `convert_data.py` below)
* `wflow_catchup.sh` runs the Wflow model for the most recent month with ERA5 data
* `wflow_batch.sh` runs the Wflow model for the 50 ensembles of the SEAS5 forecasts
* `plotting.sh` plots the results of the model simulations (see `plot_wflow_results.sh`)

### Python scripts
* `download_data.py` functionality to download ERA5 and SEAS5 data using the CDS API ([note
  that a key-file is required](https://cds.climate.copernicus.eu/api-how-to))
* `convert_data.py` functionality to convert downloaded data into suitable forcing input for a
  `wflow_sbm` model
* `plot_wflow_results.py` functionality to convert simulation results into a figure showing the
  last month of discharge, together with the forecasted discharge.


## Usage
1. Firstly, download the ERA5 and SEAS5 data from the Climate Data Store. ERA5 files are
downloaded upto the provided date, and the SEAS5 forecasts are downloaded starting from the
provided date. The script requires the following input parameters: `--output_dir` sets the
directory where the downloaded files are stored, `--date_string` expects a string (YYYY_MM) of
the current month, `--staticmaps_fn` expects the path to the file containing the staticmaps
input of the Wflow model (used to set the bounding box for the ERA5 and SEAS5 downloads,
`--buffer` can be defined to specify a buffer value (in degrees) around the bounding box, to
ensure the area of interest is fully covered.
```
python download_data.py --output_dir "workdir" --date_string "2022_01" --staticmaps_fn "../../Data/Model_input/staticmaps.nc" --buffer 0.5
```

2. Resample the downloaded data to the model grid. The script requires the following input
parameters: `--dir_downloads` refers to the directory with the downloaded data ('--output_dir'
from the previous script), and `--output_dir` to the directory where the forcing files are
exported to (currently set to the `wflow` model directory). `--date_string` expects a string
(YYYY_MM) of the current month. See the script for the optional settings (location of model
maps, ERA5 and SEAS5 elevation maps, and lapse rate value). Other options
(`--wflow_staticmaps_file`, `--era5_dem_file`, and `--era5_dem_file`) refer to elevation maps
in order to correctly apply a lapse rate (`--lapse_rate`) to the temperature. Note that the
elevation map in the Wflow staticmaps is named `wflow_dem`. The orography files for ERA5 and
SEAS5 are downloaded automatically.
```
python convert_data.py --dir_downloads "workdir" --output_dir "wflow_rhine" --date_string "2022_01"
```

3. Run the wflow model with the new forcing, both for ERA5 and SEAS5 data. Model runs need to
be performed every month, where two types of runs can be identified: (1) catching up with
observations from the "historical" period (ERA5), and performing simulations to cover the
forecasted period (SEAS5). The SEAS5 data consists of 50 ensemble members, which cover the
uncertainty range, and wflow needs to simulate each of these members. The following simulation
types need to be performed every month (using the trigger date of around 2022-01-15 as an
example):
 * wflow with ERA5 data, covering 2021-12-01 to 2021-12-31
 * wflow with SEAS5 data, which covers 2022-01-01 to 2022-08-02 (50 times, for each ensemble
   member)

Both runs need to be initialized, such that the model starts with "warm" states. The wflow
model outputs a "oustates.nc" file in the output directory of every simulation, which can be
used to initialize a new simulation. Again using a trigger date of around 2022-01-15 as an
example, the following states need to be used to initialize the two simulation types
 * wflow+ERA5 data (2021-12): initialized with the outstates from the wflow+ERA5 simulation
   from the month before (2021-11)
 * wflow+SEAS5 data (2022-01): initialized with the outstates from the most recent wflow+ERA5
 simulation (2021-12), same for every ensemble member.

The dates are extracted from the forcing files, such that the Wflow can be run with the same settings file (`wflow_sbm_static.toml`) for each simulation.

Usage:
```bash
wflow_cli "wflow_sbm_static.toml"
```

4. Post processing to produce figures/accessible data

Create a figure showing the results of the model output. Currently creates a .png file with the
discharge timeseries: a single line for the ERA5 simulation of the previous months, and the
10-90 percentile values (specified with colored ranges) and the median value based on the
ensemble SEAS5 simulations.

Usage:
```
python plot_wflow_results.py --output_dir "../../Data/model_output" --figure_out_dir "../../Public" --filename_figure "discharge_ts.png" --num_ensembles 51 --col_extract "Q_1" --start_date "2022_01"
```
`--output_dir` refers to the path of with the simulation results, `--filename_figure` is the
filename of the resulting figure (including figure format), which will be saved in the folder
specified by `--figure_out_dir`, `--num_ensembles` specifies the number of ensembles in SEAS5,
`--col_extract` specifies which column in the Wflow output csv file needs to be extract, and
`--start_date` the current month and year in YYYY_MM format.

## Folder structure
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
│   │   │   └── ...
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
│   └── home
|   │   ├── .cdsapirc                                           # needed to authenticate with the server
└── Software
    ├── cdsapirc.txt
    ├── images
    │   ├── hrlsa_j.sif
    │   └── wflowjulia.sif
    ├── python
    │   ├── convert_data.py
    │   └── download_data.py
    ├── scripts
    │   ├── prepare_data.sh
    │   ├── prepare.sh
    │   ├── run_wflow.sh
    │   └── wflow.sh
```
