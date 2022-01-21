#!/bin/bash
#SBATCH --nodes 1
#SBATCH --tasks-per-node 1

# Download Data
srun --nodes 1 --ntasks 1 singularity exec --bind /project/hrlsa/Data:/data -H /home/hrlsa-avangils:/home hrsla.sif python /opt/download_data.py  --output_dir "/data"

# Prepare Wflow input
srun --nodes 1 --ntasks 1 singularity exec --bind /project/hrlsa/Data:/data -H /home/hrlsa-avangils:/home hrsla.sif python /opt/convert_data.py --dir_downloads "/data"  --output_dir "/data/model" --wflow_staticmaps_file "/opt/wflow_rhine/staticmaps.nc" --era5_dem_file "/opt/orography_era5_rhine.grib" --seas5_dem_file "/opt/orography_seas5_rhine.grib"

