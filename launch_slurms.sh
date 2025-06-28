#!/bin/bash

export PRTE_MCA_ras_slurm_use_entire_allocation=1
export PRTE_MCA_ras_base_launch_orted_on_hn=1
# export OMPI_MCA_pml="ucx"

JOBS_DIR="pdp_mpi_jobs"
rm -rf $JOBS_DIR
mkdir -p $JOBS_DIR

OUTPUT_DIR="pdp_mpi_outs"
mkdir -p $OUTPUT_DIR

CODE_DIR=$(pwd)
echo "Using code dir as $CODE_DIR"
make clean
make

declare -a MATRIX_SIZES=(
    "1024"
    "2048"
    "4096"
    # "8192"
    # "16384"
    # "32768"
)

max_procs="40"
declare -a NUM_PROCS=(
    # $(expr $max_procs / 8)
    $(expr $max_procs / 4)
    # $(expr $max_procs / 4 + $max_procs / 8)
    $(expr $max_procs / 2)
    # $(expr $max_procs / 2 + $max_procs / 8)
    $(expr $max_procs / 2 + $max_procs / 4)
    # $(expr $max_procs / 2 + $max_procs / 4 + $max_procs / 8)
    $max_procs
)
declare -a NUM_PROCS=($(printf '%s\n' "${NUM_PROCS[@]}" | sort -nur)) # Remove duplicates and sort

declare -a PROCESS_TYPES=(
    "coletiva"
    "p2p_bloqueante"
    "p2p_naobloqueante"
)

echo "Running MPI sbatches with the following configurations:"
echo "----------------------------------------"
echo "MACHINEFILE: $MACHINEFILE"
echo "MATRIX_SIZES: ${MATRIX_SIZES[@]}"
echo "NUM_PROCS: ${NUM_PROCS[@]}"
echo "PROCESS_TYPES: ${PROCESS_TYPES[@]}"
echo "----------------------------------------"
echo ""

overall_start=$(date +%s.%N)
for num_procs in "${NUM_PROCS[@]}"; do
    for matrix_size in "${MATRIX_SIZES[@]}"; do
        for process_type in "${PROCESS_TYPES[@]}"; do
            slurm_job_name="mpi_${process_type}_${matrix_size}_${num_procs}"
            slurm_num_tasks=$num_procs
            slurm_time_limit="2:00:00"
            slurm_process_type=$process_type
            slurm_matrix_size=$matrix_size

            job_file="#!/bin/bash
#SBATCH --job-name=$slurm_job_name
#SBATCH --partition=hype
#SBATCH --nodes=2
#SBATCH --ntasks=$slurm_num_tasks
#SBATCH --time=$slurm_time_limit
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

MACHINEFILE=\"nodes.\$SLURM_JOB_ID\"
srun -l hostname | sort -n | awk '{print \$2}' > \$MACHINEFILE

echo \"# ----------------------------------------\"
echo \"# job id: \$SLURM_JOB_ID\"
echo \"# job name: $slurm_job_name\"
echo \"# Running process type: $slurm_process_type\"
echo \"# Matrix size: $slurm_matrix_size\"
echo \"# Number of processes: $slurm_num_tasks\"
current_time=\$(date '+%d-%m-%Y %H:%M:%S.%M')
echo \"# Current time: \$current_time\"
echo \"# ----------------------------------------\"

echo \"# ----------------------------------------\" >&2
echo \"# job id: \$SLURM_JOB_ID\" >&2
echo \"# job name: $slurm_job_name\" >&2
echo \"# Running process type: $slurm_process_type\" >&2
echo \"# Matrix size: $slurm_matrix_size\" >&2
echo \"# Number of processes: $slurm_num_tasks\" >&2
current_time=\$(date '+%d-%m-%Y %H:%M:%S.%M') >&2
echo \"# Current time: \$current_time\" >&2
echo \"# ----------------------------------------\" >&2

mpirun -np \$SLURM_NTASKS \\
       -machinefile \$MACHINEFILE \\
       --mca btl ^openib \\
       --mca btl_tcp_if_include eno2 \\
       --bind-to none -np \$SLURM_NTASKS \\
       $CODE_DIR/mpi_$slurm_process_type $slurm_matrix_size

job_lasted=\$(echo \"\$(date +%s.%N) - \$current_time\" | bc)
echo \"# ----------------------------------------\"
echo \"# ----------------------------------------\" >&2

exit_code=\$?
if [ \$exit_code -ne 0 ]; then
    echo \"# Error: Process $slurm_process_type with matrix size $slurm_matrix_size and $slurm_num_tasks processes failed with exit code \$exit_code after \$job_lasted seconds\"
    echo \"# ----------------------------------------\"
    echo \"# Error: Process $slurm_process_type with matrix size $slurm_matrix_size and $slurm_num_tasks processes failed with exit code \$exit_code after \$job_lasted seconds\" >&2
    echo \"# ----------------------------------------\" >&2
    exit \$exit_code
fi

echo \"# Finished running $process_type with matrix size $matrix_size and $num_procs processes after $job_lasted seconds\"
echo \"# ----------------------------------------\"

echo \"# Finished running $process_type with matrix size $matrix_size and $num_procs processes after $job_lasted seconds\" >&2
echo \"# ----------------------------------------\" >&2
"

            # Create a temporary file for the job script
            temp_job_file="./$JOBS_DIR/${slurm_job_name}.slurm"
            echo "$job_file" > "$temp_job_file"

            # Submit the job to SLURM
            if [ "$1" == "--launch" ]
            then
                cd $OUTPUT_DIR
                echo "Submitting job: $slurm_job_name"
                sbatch "../$temp_job_file"
                cd ..
            else
                echo "Dry run: Would submit job: $slurm_job_name"
                echo "Would run: 'sbatch \"../$temp_job_file\"'"
                echo "To actually submit, run with --launch option."
            fi
        done
    done
done

echo "All tasks launched completed."
elapsed=$(echo "$(date +%s.%N) - $overall_start" | bc)
echo "Time elapsed: $elapsed seconds"
