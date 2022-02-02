# Runs the hrlsa workflow as one script, based on current month

d=$(date)
thisym=$(date "+%Y_%m")
lastym=$(date --date "$d -1 month" "+%Y_%m") 
last2ym=$(date --date "$d -2 month" "+%Y_%m")

# Download and convert data
preparejobid=$(sbatch prepare.sh $thisym | awk 'match($0, /[0-9]+/) {print substr($0, RSTART, RLENGTH)}')
echo "started data prep job with id: $preparejobid"
# Catch up with real data
catchupjobid=$(sbatch --dependency=afterok:$preparejobid wflow_catchup.sh $lastym $last2ym | awk 'match($0, /[0-9]+/) {print substr($0, RSTART, RLENGTH)}')
echo "stated catchup job with id: $catchupjobid"
# Forecast
forecastjobid=$(sbatch --dependency=afterok:$catchupjobid wflow_batch.sh $thisym $lastym)
echo "started forecasting job with id: $forecastjobid"
