#!/bin/bash
#SBATCH -N 1
#SBATCH -c 1
#SBATCH -t 10:00:00

project_home=/project/hrlsa
image_home=${project_home}/Share/home
image=${project_home}/Software/images/hrlsa_j.sif

# Download Data
srun --nodes 1 --ntasks 1 singularity exec \
        --bind ${project_home}/Data:/data \
	--bind ${project_home}/Software/python:/opt/python \
        -H ${image_home}:/home \
       	${image} \
	python /opt/python/download_data.py  --output_dir "/data/Forcing/downloaded"

# Prepare Wflow input
srun --nodes 1 --ntasks 1 singularity exec \
	--bind ${project_home}/Data:/data \
	--bind ${project_home}/Software/python:/opt/python \
       	-H ${project_home}:/home \
       	${image} \
       	python /opt/python/convert_data.py \
       	--dir_downloads "/data/Forcing/downloaded" \
      	--output_dir "/data/Forcing/converted" \
       	--wflow_staticmaps_file "/data/model_input/staticmaps.nc" \
       	--era5_dem_file "/data/model_input/orography_era5_rhine.grib" \
       	--seas5_dem_file "/data/model_input/orography_seas5_rhine.grib"

