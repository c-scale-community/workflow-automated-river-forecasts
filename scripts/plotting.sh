#!/bin/bash
#
#SBATCH --job-name=plotting
#
#SBATCH -N 1
#SBATCH -c 1
#SBATCH -t 1:00:00

# Usage <start_forecast>
# start_forecast start time of the forecast in YYYY_MM format

image=$PROJECT_HOME/Software/images/hrlsa_j.sif

output_dir=$PROJECT_HOME/Data/model_output
figure_out_dir=$PROJECT_HOME/Public/$1

# Create figure out directory if needed
mkdir -p -m775 $figure_out_dir

# Copy html for easy viewing of figure
cp $PROJECT_HOME/Software/assets/view_image.html $figure_out_dir/view_image.html
chmod 664 $figure_out_dir/view_image.html

# Run plotting
srun --nodes 1 --ntasks 1 singularity exec \
        --bind $output_dir:/tempdata \
        --bind $figure_out_dir:/tempout \
	--bind $PROJECT_HOME/Software/python/plot_wflow_results.py:/data/plot_wflow_results.py \
        --pwd /data \
        $image \
        python plot_wflow_results.py \
	--output_dir /tempdata \
	--figure_out_dir /tempout \
	--filename_figure discharge_ts.png \
	--num_ensembles 51 \
	--col_extract Q_1 \
	--start_date $1
