#!/bin/bash
#
#SBATCH --job-name=wflow-batch
#SBATCH --output=/project/hrlsa/Data/logs/wflow-batch.log
#
#SBATCH -N 1
#SBATCH -c 1
#SBATCH -t 12:00:00
#
#SBATCH --array=0-50

# Usage wflow_batch <start_forecast> <start_input>
# start_forecast start time of the forecast in YYYY_MM format
# start_input start time of the data in YYYY_MM format

project_home=/project/hrlsa
image=${project_home}/Software/images/wflow_v0_4_0.sif

c_fname="forcing/converted"

# Run Wflow
srun --nodes 1 --ntasks 1 singularity exec \
	--bind ${project_home}/Data:/data \
	--bind ${project_home}/Software/scripts/start_wflow.jl:/data/start_wflow.jl \
       	--pwd /data \
       	$image \
       	julia start_wflow.jl \
       	--toml_filename "/data/model_input/wflow_sbm_base.toml" \
	--output_dir "/data/model_output/run_SEAS5_ens${SLURM_ARRAY_TASK_ID}_$1" \
       	--instates_filename "/data/model_output/run_ERA5_$2" \
	--forcing_filename "/data/${c_fname}/$(ls ${project_home}/Data/${c_fname} | grep forcing_SEAS5_ens${SLURM_ARRAY_TASK_ID}_`echo $1 | sed 's/_/-/g'`)"
