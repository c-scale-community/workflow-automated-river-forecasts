#!/bin/bash
#
#SBATCH --job-name=prepare
#SBATCH --ouutput=$project_home/Data/logs/prepare.log
#
#SBATCH -N 1
#SBATCH -c 1
#SBATCH -t 10:00:00

project_home=to_be_modified
# project_home=/project/hrlsa

image_home=$project_home/Share/home
image=$project_home/Software/images/hrlsa_j.sif

# Download Data
srun --nodes 1 --ntasks 1 singularity exec \
        --bind $project_home/Data:/data \
	--bind $project_home/Software/python:/opt/python \
        -H $image_home:/home \
       	$image \
	python /opt/python/download_data.py  \
		--output_dir "/data/forcing/downloaded" \
		--date_string $1 \
		--staticmaps_fn "/data/model_input/staticmaps.nc"

# Prepare Wflow input
srun --nodes 1 --ntasks 1 singularity exec \
	--bind $project_home/Data:/data \
	--bind $project_home/Software/python:/opt/python \
       	-H $project_home:/home \
       	$image \
       	python /opt/python/convert_data.py \
       	--dir_downloads "/data/forcing/downloaded" \
	--date_string $1 \
      	--output_dir "/data/forcing/converted" \
       	--wflow_staticmaps_file "/data/model_input/staticmaps.nc" \
       	--era5_dem_file "/data/forcing/downloaded/orography_era5.grib" \
       	--seas5_dem_file "/data/forcing/downloaded/orography_seas5.grib"

