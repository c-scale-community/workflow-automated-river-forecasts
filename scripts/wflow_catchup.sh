#!/bin/bash
#
#SBATCH --job-name=wflow-catchup
#
#SBATCH -N 1
#SBATCH -c 1
#SBATCH -t 1:00:00

# Usage wflow_batch <start_forecast> <start_input>
# start_forecast start time of the forecast in YYYY_MM format
# start_input start time of the data in YYYY_MM format

image=$project_home/Software/images/wflow_063.sif

output_dir=$project_home/Data/model_output/run_ERA5_$1
input_dir=$project_home/Data/model_output/run_ERA5_$2

c_fname="forcing/converted"
forcing_name=$(ls $project_home/Data/$c_fname | grep forcing_ERA5_`echo $1 | sed 's/_/-/g'`)

# Create output directory if needed
mkdir -p -m770 $output_dir

# Run Wflow
srun --nodes 1 --ntasks 1 singularity exec \
	--writable-tmpfs \
    --bind $project_home/Data:/data \
    --bind $input_dir:/tempdata/input \
    --bind $output_dir:/tempdata/output \
    --bind $project_home/Data/$c_fname/$forcing_name:/tempdata/forcing/forcing.nc \
    --pwd /data \
    $image \
    /app/create_app/wflow_bundle/bin/wflow_cli /data/model_input/wflow_sbm_static.toml

