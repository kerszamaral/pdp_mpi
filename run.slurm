#!/bin/bash
#SBATCH --job-name=mpi_coletiva
#SBATCH --partition=hype
#SBATCH --nodes=2
#SBATCH --ntasks=40
#SBATCH --time=2:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

MACHINEFILE="nodes.$SLURM_JOB_ID"
srun -l hostname | sort -n | awk '{print $2}' > $MACHINEFILE

# Variar:
# - tipo do processo: coletiva, bloqeuante e nao bloqeuante
# - tamanho da matriz: 1024, 2048, 4096
# - numero de processos: 2, 4, 8, 16,

# Inserir Medicoes de tempo de comunicacao

# mpirun -np $SLURM_NTASKS \
       # -machinefile $MACHINEFILE \
       # --mca btl ^openib \
       # --mca btl_tcp_if_include eno2 \
       # --bind-to none -np $SLURM_NTASKS \
       # ./mpi_coletiva 2048

