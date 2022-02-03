#!/bin/bash
#
#SBATCH --job-name=plotting
#SBATCH --output=/project/hrlsa/Data/logs/plotting.log
#
#SBATCH -N 1
#SBATCH -c 1
#SBATCH -t 1:00:00

# Usage <start_forecast>
# start_forecast start time of the forecast in YYYY_MM format

project_home=/project/hrlsa
image=$project_home/Software/images/hrlsa_j.sif

output_dir=$project_home/Data/model_output
figure_out_dir=$project_home/Public/$1

# Create figure out directory if needed
mkdir -p -m774 $figure_out_dir

# Run plotting
srun --nodes 1 --ntasks 1 singularity exec \
        --bind $output_dir:/tempdata \
        --bind $figure_out_dir:/tempout \
	--bind $project_home/Software/python/plot_wflow_results.py:/data/plot_wflow_results.py \
        --pwd /data \
        $image \
        python plot_wflow_results.py \
	--output_dir /tempdata \
	--figure_out_dir /tempout \
	--filename_figure discharge_ts.png \
	--num_ensembles 51 \
	--col_extract Q_1
