# Automated monthly river forecasts

Easily deploy a workflow that produces a monthly high resolution, ensemble river discharge forecast for a river basin of interest.

This workflow produces a monthly high resolution, ensemble river discharge forecast for a river basin of interest. It build upon locally developed tools, and combines these in a workflow that is deployed in the cloud. The workflow uses the global ERA5 re-analysis product and SEAS5 seasonal meterological forecasts from the Copernicus Climate Data Store as input for the wflow_sbm hydrological model. The input data is automatically downloaded for the model domain, resampled to the required model grid, and runs a 50-member ensemble forecast simulation. This workflow is triggered every month when new SEAS5 forecasts become available.

## Workflow steps
As mentioned above, the workflow is triggered every month, at the moment when new SEAS5 forecasts become available. The SEAS5 data become available on the 13th day of the month, and provides a forecast to 7 months in the future. Therefore, this workflow is triggered on the 15th of every month. The following steps are automatically performed when the workflow is triggered (using November 15 2022 as the example trigger date):

1. Download ERA5 data for the previous month (from 2022-10-01 until 2022-11-01)
2. Download the most recent SEAS5 forecast data (from 2022-11-01 until 2023-06-01)
3. Download orography information from both ERA5 and SEAS5, to allow for lapse-rate temperature correction
3. Resample both ERA5 and SEAS5 data to the model grid (and apply a lapse rate to temperature)
4. Run the wflow_sbm model with the ERA5 data to provide correct initial conditions for the SEAS5 forecast
5. Run the wflow_sbm model with all members (50) of the SEAS5 forecast
6. Plot discharge forecasts

## Script explanation

One main bash script orchestrates all steps in this workflow, with the arguments between brackets. The parameter **thisym** corresponds to the date set when curring `workflow.sh`, **lastym** one month before thisym, and **last2ym** two months before thisym.

- `workflow.sh` (**date**, *optional in YYYY-MM-DD format*)

    This bash script orchestrates all steps in the workflow, ensuring they are executed in the correct order. This file can be run with and without any additional arguments. If run without any arguments, the current month is used as the start of the forecasting period. Additionally, it can be run with any date as argument (passed as `./workflow.sh "2022-10-15"`), in the case older forecasts need to be (re-)run. The script then runs the following four scripts in sequence, where the previous script needs to be completed before proceeding to the next step.

    ```bash
    ./workflow.sh # to run for the current month
    ./workflow.sh "2022-11-15" # to run for any month
    ```

- `prepare.sh` (**thisym**, in *YYYY_MM* format)

    This script downloads the ERA5 and SEAS5 data from the Copernicus Data Store, using the domain of the hydrological model to reduce the size of the requested data. The time frame for the ERA5 data is set be one month, ending at the provided month in **thisym**. SEAS5 is downloaded as the forecast at the provided month, to 7 months after the provided month. The download request is sent using the [CDS API](https://cds.climate.copernicus.eu/api-how-to), and is executed by the `download_data.py` script.

    After downloading, both ERA5 and SEAS5 data are re-gridded to the model grid (using the `staticmaps.nc` from the wflow_sbm model configuration). A lapse rate correction is applied to the temperature to correct for the elevation provided in the model configuration. Furthermore, the potential evaporation (PET) is calculated based on Makkink's equation (requiring temperature, pressure and incoming radiation data). The regridding, lapse rate correction and PET calculation is performed by the `convert_data.py` script that is called by this bash script.

    ```bash
    ./prepare.sh "2022_11" # download and convert ERA5 and SEAS5 data
    ```

- `wflow_catchup.sh` (**lastym**, in *YYYY_MM* format; **last2ym**, in *YYYY_MM* format)

    When the ERA5 and SEAS5 data is downloaded and converted, the wflow_sbm model can be ran to ensure correct initial conditions when starting the forecasts simulations. This bash script calls `wflow_cli` with all correct run settings. The wflow_sbm models takes the initial conditions from the last ERA5 simulation (hence the **last2ym** argument), and starts the simulation with ERA5 data. The simulation stops at the point where the SEAS5 forecast starts, where the `wflow_batch.sh` script starts.

    ```bash
    ./wflow_catchup.sh "2022_10" "2022_09" # run the wflow_sbm model for 2022-10
    ```

- `wflow_batch.sh`(**thisym**, in *YYYY_MM* format; **lastym**, in *YYYY_MM* format)

    After running the catchup job, the wflow_sbm model is started (through calling `wflow_cli`) for each of the 50 ensemble members in the SEAS5 forecast. The initial conditions from the catchup job are used to initialize the hydrological model. The 50 ensemble runs are run in parallel, as they are completely independent simulations.

    ```bash
    ./wflow_batch.sh "2022_11" "2022_10" # run the wflow_sbm model with forecasts starting at 2022-10
    ```

- `plotting.sh` (**thisym**, in *YYYY_MM* format)

    After running the wflow_sbm simulations, the results are summarized in a hydrograph. The results of the 50 members are combined, and presented using percentile values (ranging between 10% and 90%, with intervals of 10%). This bash script calls the `plot_wflow_results.py` script, which produces the visualisation of the results. The figure (`discharge_ts.png`) is stored in the `Public` folder, in a subfolder indicating the start of the forecast data. Additionally, the `view_image.html` file is copied to this same folder, to allow to easily view this figure in the browser (rather than downloading the .png file).

    ```bash
    ./plotting_sh "2022_11" # plots the discharge simulations of the forecast that started at 2022-11
    ```

## Setting up the workflow

1. Download `setup_directories.sh` script
2. Modify the path the home of your project in line 10 in this script (`# project_home=/path/to/your/project`)
3. Run `setup_directories.sh`, which clones this repo and corrects all paths with you project home

### Other requirements

- Model configuration files:

    This workflow assumes you have already built a wflow_sbm model, and that this model is at the expected location (see folder structure below)

- CDS API key

    A CDS API key is required to download data from the Copernicus Data Store. See [this link](https://cds.climate.copernicus.eu/api-how-to) on how to set this up.

- scrontab file to automatically trigger the workflow

    A scrontab file is required to automatically trigger the workflow on every 15th day of the month. This should look something like this `0 0 15 * * /project/hrlsa/Software/scripts/workflow.sh`

## Overview folder structure

<details>
  <summary>Click to view folder structure</summary>

```bash
.
├── Data
│   ├── forcing
│   │   ├── converted
│   │   │   ├── forcing_ERA5_YYYY-MM-DD_YYYY-MM-DD.nc
│   │   │   └── forcing_SEAS5_ensX_YYYY-MM-DD_YYYY-MM-DD.nc
│   │   └── downloaded
│   │       ├── ERA5_YYYY_MM.nc
│   │       ├── orography_era5.grib
│   │       ├── orography_seas5.grib
│   │       └── SEAS5_YYYY_MM.nc
│   ├── logs
│   │   ├── cron.log
│   │   ├── plotting.log
│   │   ├── prepare.log
│   │   ├── wflow-batch.log
│   │   └── wflow-catchup.log
│   ├── model_input
│   │   ├── hydromt_data.yml
│   │   ├── hydromt.log
│   │   ├── instate
│   │   ├── lake_hq_1244.csv
│   │   ├── lake_hq_1248.csv
│   │   ├── lake_hq_14005.csv
│   │   ├── lake_hq_14023.csv
│   │   ├── lake_hq_14029.csv
│   │   ├── lake_sh_1243.csv
│   │   ├── lake_sh_1244.csv
│   │   ├── log.txt
│   │   ├── staticmaps.nc
│   │   └── wflow_sbm_static.toml
│   └── model_output
│       ├── run_ERA5_YYYY_MM
│       │   ├── output.csv
│       │   ├── output.nc
│       │   └── outstates.nc
│       └── run_SEAS5_ensX_YYYY_MM
│           ├── output.csv
│           ├── output.nc
│           └── outstates.nc
├── Public
│   └── YYYY_MM
│       ├── discharge_ts.png
│       ├── orig_discharge_ts.png
│       └── view_image.html
└── Software
    ├── assets
    │   └── view_image.html
    ├── images
    │   ├── environment.yaml
    │   ├── hrlsa.def
    │   ├── hrlsa_j.sif
    │   └── wflowjulia.sif
    ├── python
    │   ├── convert_data.py
    │   ├── download_data.py
    │   └── plot_wflow_results.py
    ├── README.md
    ├── requirements.txt
    └── scripts
        ├── plotting.sh
        ├── prepare.sh
        ├── setup_directories.sh
        ├── wflow_batch.sh
        ├── wflow_catchup.sh
        └── workflow.sh
```
</details>

## Notes

From November 2022 a new version of ECMWF SEAS5 output substituted the old version. This new
version (v5.1) will be labelled with the keyword `system=51`. See between the updates of 12
October 2022 and 30 October 2022
[here](https://confluence.ecmwf.int/display/CKB/Announcements). This system is automatically selected depending on the start of the forecasting period (when this workflow is used to perform hindcasts).