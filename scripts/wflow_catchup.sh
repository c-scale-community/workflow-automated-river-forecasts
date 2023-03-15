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

image=$PROJECT_HOME/Software/images/wflow_063.sif

output_dir=$PROJECT_HOME/Data/model_output/run_ERA5_$1
input_dir=$PROJECT_HOME/Data/model_output/run_ERA5_$2

c_fname="forcing/converted"
forcing_name=$(ls $PROJECT_HOME/Data/$c_fname | grep forcing_ERA5_`echo $1 | sed 's/_/-/g'`)

# Create output directory if needed
mkdir -p -m770 $output_dir

# Run Wflow
srun --nodes 1 --ntasks 1 singularity exec \
        --bind $PROJECT_HOME/Data:/data \
	--bind $input_dir:/tempdata/input \
	--bind $output_dir:/tempdata/output \
	--bind $PROJECT_HOME/Data/$c_fname/$forcing_name:/tempdata/forcing/forcing.nc \
        --pwd /data \
        $image \
	/opt/wflow_cli/bin/wflow_cli /data/model_input/wflow_sbm_static.toml
        # --output_dir "/data/model_output/run_ERA5_$1" \
        # --instates_filename "/data/model_output/run_ERA5_$2" \
        # --forcing_filename "/data/${c_fname}/$(ls ${PROJECT_HOME}/Data/${c_fname} | grep forcing_ERA5_`echo $1 | sed 's/_/-/g'`)"

