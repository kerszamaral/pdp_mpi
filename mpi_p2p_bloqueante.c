// MPI Matrix Multiplication using Point-to-Point Communication
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

void initialize_matrices(int n, double* A, double* B, double* C) {
    for (int i = 0; i < n * n; i++) {
        A[i] = i % 100;
        B[i] = (i % 100) + 1;
        C[i] = 0.0;
    }
}

int main(int argc, char* argv[]) {
    int rank, size, n = atoi(argv[1]);
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    double *A, *B, *C;
    A = (double*)malloc(n * n * sizeof(double));
    B = (double*)malloc(n * n * sizeof(double));
    C = (double*)malloc(n * n * sizeof(double));

    if (rank == 0) {
        initialize_matrices(n, A, B, C);
    }

    double t_start = 0.0, t_end = 0.0;
    if (rank == 0)
        t_start = MPI_Wtime();

    double comm_time = 0.0;
    double comm_start, comm_end;

    double* local_A = (double*)malloc((n * n / size) * sizeof(double));
    double* local_C = (double*)malloc((n * n / size) * sizeof(double));

    // Comunicação: distribuição da matriz A
    if (rank == 0) {
        for (int i = 1; i < size; i++) {
            comm_start = MPI_Wtime();
            MPI_Send(A + i * (n * n / size), n * n / size, MPI_DOUBLE, i, 0, MPI_COMM_WORLD);
            comm_end = MPI_Wtime();
            comm_time += comm_end - comm_start;
        }
        for (int i = 0; i < n * n / size; i++) {
            local_A[i] = A[i];
        }
    } else {
        comm_start = MPI_Wtime();
        MPI_Recv(local_A, n * n / size, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        comm_end = MPI_Wtime();
        comm_time += comm_end - comm_start;
    }

    // Comunicação: broadcast da matriz B
    comm_start = MPI_Wtime();
    MPI_Bcast(B, n * n, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    comm_end = MPI_Wtime();
    comm_time += comm_end - comm_start;

    // Cálculo local
    for (int i = 0; i < n / size; i++) {
        for (int j = 0; j < n; j++) {
            local_C[i * n + j] = 0.0;
            for (int k = 0; k < n; k++) {
                local_C[i * n + j] += local_A[i * n + k] * B[k * n + j];
            }
        }
    }

    // Comunicação: coleta dos resultados em C
    if (rank == 0) {
        for (int i = 0; i < n * n / size; i++) {
            C[i] = local_C[i];
        }
        for (int i = 1; i < size; i++) {
            comm_start = MPI_Wtime();
            MPI_Recv(C + i * (n * n / size), n * n / size, MPI_DOUBLE, i, 1, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            comm_end = MPI_Wtime();
            comm_time += comm_end - comm_start;
        }
    } else {
        comm_start = MPI_Wtime();
        MPI_Send(local_C, n * n / size, MPI_DOUBLE, 0, 1, MPI_COMM_WORLD);
        comm_end = MPI_Wtime();
        comm_time += comm_end - comm_start;
    }

    if (rank == 0) {
        t_end = MPI_Wtime();
        printf("Execution time: %.6f seconds\n", t_end - t_start);
    }

    // Mostra o tempo de comunicação de cada processo
    printf("Rank %d - Communication time: %.6f seconds\n", rank, comm_time);

    free(A);
    free(B);
    free(C);
    free(local_A);
    free(local_C);

    MPI_Finalize();
    return 0;
}
