# pdp_mpi

Command to run the code:

```bash
mpirun -np $NUM_PROC --mca btl ^openib --bind-to none $MPI_PROG $MATRIX_SIZE
```
