# Runs the hrlsa workflow as one script, based on current month

d=$(date)
thisym=$(date "+%Y_%m")
lastym=$(date --date "$d -1 month" "+%Y_%m") 
last2ym=$(date --date "$d -2 month" "+%Y_%m")

# Download and convert data
preparejobid=$(sbatch prepare.sh | awk 'match($0, /[0-9]+/) {print substr($0, RSTART, RLENGTH)}')
# Catch up with real data
catchupjobid=$(sbatch --dependency=afterok:$preparejobid wflow.sh ${lastym} ${last2ym})
# Forecast
forecastjobid=$(sbatch --dependency=afterok:$catchupjobid wflow.sh ${thisym} ${lastym})
