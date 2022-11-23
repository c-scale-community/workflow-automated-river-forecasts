# Runs the hrlsa workflow as one script, based on current month
project_home=/project/hrlsa
scriptsdir="$project_home/Software/scripts"

job1=$(sbatch $scriptsdir/workflow.sh "2022-01-15")
job2=$(sbatch --dependency=afterok:$job1 $scriptsdir/workflow.sh "2022-02-15")
job3=$(sbatch --dependency=afterok:$job2 $scriptsdir/workflow.sh "2022-03-15")
job4=$(sbatch --dependency=afterok:$job3 $scriptsdir/workflow.sh "2022-04-15")
job5=$(sbatch --dependency=afterok:$job4 $scriptsdir/workflow.sh "2022-05-15")
job6=$(sbatch --dependency=afterok:$job5 $scriptsdir/workflow.sh "2022-06-15")
job7=$(sbatch --dependency=afterok:$job6 $scriptsdir/workflow.sh "2022-07-15")
job8=$(sbatch --dependency=afterok:$job7 $scriptsdir/workflow.sh "2022-08-15")
job9=$(sbatch --dependency=afterok:$job8 $scriptsdir/workflow.sh "2022-09-15")
job10=$(sbatch --dependency=afterok:$job9 $scriptsdir/workflow.sh "2022-10-15")
job11=$(sbatch --dependency=afterok:$job10 $scriptsdir/workflow.sh "2022-11-15")