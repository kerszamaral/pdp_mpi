#!/bin/bash
#SBATCH --job-name=pdp_mpi_test
#SBATCH --partition=hype
#SBATCH --nodes=2
#SBATCH --ntasks=40
#SBATCH --time=4:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

MACHINEFILE="nodes.$SLURM_JOB_ID"
srun -l hostname | sort -n | awk '{print $2}' > $MACHINEFILE

declare -a MATRIX_SIZES=(
    "1024"
    "2048"
    "4096"
    # "8192"
    # "16384"
    # "32768"
)

max_procs=$SLURM_NTASKS
declare -a NUM_PROCS=(
    $(expr $max_procs / 8)
    $(expr $max_procs / 4)
    $(expr $max_procs / 5 + $max_procs / 8)
    $(expr $max_procs / 2)
    $(expr $max_procs / 2 + $max_procs / 8)
    $(expr $max_procs / 2 + $max_procs / 4)
    $(expr $max_procs / 2 + $max_procs / 4 + $max_procs / 8)
    $max_procs
)

declare -a NUM_PROCS=($(printf '%s\n' "${NUM_PROCS[@]}" | sort -nu)) # Remove duplicates and sort

declare -a PROCESS_TYPES=(
    "coletiva"
    "p2p_bloqueante"
    "p2p_naobloqueante"
)

# Variar:
# - tipo do processo: coletiva, bloqeuante e nao bloqeuante
# - tamanho da matriz: 1024, 2048, 4096
# - numero de processos: 1, ..., ..., $SLURM_NTASKS,

echo "Running MPI processes with the following configurations:"
echo "----------------------------------------"
echo "MACHINEFILE: $MACHINEFILE"
echo "MATRIX_SIZES: ${MATRIX_SIZES[@]}"
echo "NUM_PROCS: ${NUM_PROCS[@]}"
echo "PROCESS_TYPES: ${PROCESS_TYPES[@]}"
echo "----------------------------------------"
echo ""

overall_start=$(date +%s.%N)
for process_type in "${PROCESS_TYPES[@]}"; do
    for matrix_size in "${MATRIX_SIZES[@]}"; do
        for num_procs in "${NUM_PROCS[@]}"; do
            echo "----------------------------------------"
            echo "Running process type: $process_type"
            echo "Matrix size: $matrix_size"
            echo "Number of processes: $num_procs"
            echo "----------------------------------------"

            mpirun -np $num_procs \
                   -machinefile $MACHINEFILE \
                   --mca btl ^openib \
                   --mca btl_tcp_if_include eno2 \
                   --bind-to none \
                   ./mpi_$process_type $matrix_size

            echo "Finished running $process_type with matrix size $matrix_size and $num_procs processes"
            echo "----------------------------------------"
            echo ""
        done
    done
done

echo "All processes completed."
elapsed=$(echo "$(date +%s.%N) - $overall_start" | bc)
echo "Time elapsed: $elapsed seconds"
