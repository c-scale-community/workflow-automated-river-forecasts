# Runs the hrlsa workflow as one script, based on current month

PROJECT_HOME=to_be_modified
# PROJECT_HOME=/project/hrlsa
scriptsdir="$PROJECT_HOME/Software/scripts"

# d=$(date)
tmp=${1-$(date)}
d=$(date -d "$tmp")
thisym=$(date --date "$d" "+%Y_%m")
lastym=$(date --date "$d -1 month" "+%Y_%m")
last2ym=$(date --date "$d -2 month" "+%Y_%m")

# Download and convert data
preparejobid=$(sbatch --export=ALL,PROJECT_HOME --output=$PROJECT_HOME/Data/logs/prepare.log $scriptsdir/prepare.sh $thisym | awk 'match($0, /[0-9]+/) {print substr($0, RSTART, RLENGTH)}')
echo "started data prep job with id: $preparejobid"
# Catch up with real data
catchupjobid=$(sbatch --export=ALL,PROJECT_HOME --output=$PROJECT_HOME/Data/logs/wflow-catchup.log --dependency=afterok:$preparejobid $scriptsdir/wflow_catchup.sh $lastym $last2ym | awk 'match($0, /[0-9]+/) {print substr($0, RSTART, RLENGTH)}')
echo "started catchup job with id: $catchupjobid"
# Forecast
forecastjobid=$(sbatch --export=ALL,PROJECT_HOME --output=$PROJECT_HOME/Data/logs/wflow-batch.log --dependency=afterok:$catchupjobid $scriptsdir/wflow_batch.sh $thisym $lastym | awk 'match($0, /[0-9]+/) {print substr($0, RSTART, RLENGTH)}')
echo "started forecasting job with id: $forecastjobid"
# Plotting
plottingjobid=$(sbatch --export=ALL,PROJECT_HOME --output=$PROJECT_HOME/Data/logs/plotting.log --dependency=afterok:$forecastjobid $scriptsdir/plotting.sh $thisym | awk 'match($0, /[0-9]+/) {print substr($0, RSTART, RLENGTH)}')
echo "started plotting job with id: $plottingjobid"
