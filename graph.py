from pathlib import Path
from argparse import ArgumentParser
import json
from enum import StrEnum
import matplotlib.pyplot as plt
import numpy as np

class ExecutionType(StrEnum):
    BLOCKING = "bloqueante"
    NON_BLOCKING = "naobloqueante"
    COLLECTIVE = "coletiva"
    
    @classmethod
    def from_string(cls, value: str) -> "ExecutionType":
        value = value.lower()
        if value == "bloqueante":
            return cls.BLOCKING
        elif value == "naobloqueante":
            return cls.NON_BLOCKING
        elif value == "coletiva":
            return cls.COLLECTIVE
        else:
            raise ValueError(f"Unknown execution type: {value}")
        
    def __str__(self) -> str:
        return self.value
    
def get_key(value: str) -> tuple[ExecutionType, int, int]:
    value = value[1:]  # Remove the leading parenthesis
    value = value[:-1]  # Remove the trailing parenthesis
    value = value.split(", ")
    if len(value) != 3:
        raise ValueError(f"Invalid key format: {value}")

    exec_type = (value[0].split(": ")[1].replace("'", "").replace('>', ''))
    exec_type = ExecutionType.from_string(exec_type)
    matrix_size = int(value[1])
    cores = int(value[2])
    return exec_type, matrix_size, cores


def plot_execution_time_vs_cores(data: dict, matrix_size: int, output_dir: Path):
    """
    Plots the execution time vs. the number of cores for a given matrix size.

    Args:
        data: The parsed data.
        matrix_size: The matrix size to plot.
        server_name: The name of the server for the plot title.
    """
    plt.figure(figsize=(10, 6))
    for exec_type in ExecutionType:
        cores = sorted([k[2] for k in data if k[0] == exec_type and k[1] == matrix_size])
        execution_times = [float(data[(exec_type, matrix_size, c)]['execution_time']) for c in cores]
        if cores:
            plt.plot(cores, execution_times, marker='o', linestyle='-', label=str(exec_type))

    plt.xlabel("Number of Cores")
    plt.ylabel("Execution Time (s)")
    plt.title(f"Execution Time vs. Number of Cores (Matrix Size: {matrix_size})")
    plt.legend()
    plt.grid(True)
    plt.savefig(output_dir / f"execution_time_vs_cores_{matrix_size}.png")
    plt.close()

def plot_execution_time_vs_matrix_size(data: dict, num_cores: int, output_dir: Path):
    """
    Plots the execution time vs. the matrix size for a given number of cores.

    Args:
        data: The parsed data.
        num_cores: The number of cores to plot.
        server_name: The name of the server for the plot title.
    """
    plt.figure(figsize=(10, 6))
    for exec_type in ExecutionType:
        matrix_sizes = sorted([k[1] for k in data if k[0] == exec_type and k[2] == num_cores])
        execution_times = [float(data[(exec_type, m, num_cores)]['execution_time']) for m in matrix_sizes]
        if matrix_sizes:
            plt.plot(matrix_sizes, execution_times, marker='o', linestyle='-', label=str(exec_type))

    plt.xlabel("Matrix Size")
    plt.ylabel("Execution Time (s)")
    plt.title(f"Execution Time vs. Matrix Size (Cores: {num_cores})")
    plt.legend()
    plt.grid(True)
    plt.savefig(output_dir / f"execution_time_vs_matrix_size_{num_cores}.png")
    plt.close()

def plot_communication_time_vs_cores(data: dict, matrix_size: int, output_dir: Path):
    """
    Plots the average communication time vs. the number of cores for a given matrix size.

    Args:
        data: The parsed data.
        matrix_size: The matrix size to plot.
        server_name: The name of the server for the plot title.
    """
    plt.figure(figsize=(10, 6))
    for exec_type in ExecutionType:
        cores = sorted([k[2] for k in data if k[0] == exec_type and k[1] == matrix_size])
        avg_comm_times = []
        for c in cores:
            comm_times_str = data[(exec_type, matrix_size, c)]['communication_time'].values()
            comm_times = [float(t) for t in comm_times_str]
            avg_comm_times.append(np.mean(comm_times))
        if cores:
            plt.plot(cores, avg_comm_times, marker='o', linestyle='-', label=str(exec_type))

    plt.xlabel("Number of Cores")
    plt.ylabel("Average Communication Time (s)")
    plt.title(f"Communication Time vs. Number of Cores (Matrix Size: {matrix_size})")
    plt.legend()
    plt.grid(True)
    plt.savefig(output_dir / f"communication_time_vs_cores_{matrix_size}.png")
    plt.close()
    
def main() -> int:
    parser = ArgumentParser(description="Parse and process files in a directory.")
    parser.add_argument("--file", "-f", type=Path, help="Json file to process", required=True)
    parser.add_argument("--output", "-o", type=Path, help="Output directory for plots", default=Path("."))

    parsed_args = parser.parse_args()
    file_path: Path = parsed_args.file
    if not file_path.is_file():
        print(f"Error: The specified file '{file_path}' does not exist or is not a file.")
        return 1
    
    initial_data = json.loads(file_path.read_text(encoding="utf-8"))
    parsed_data: dict[tuple[ExecutionType, int, int], dict[str, str | dict[str, str]]] = {get_key(k): v for k, v in initial_data.items()}
    # Data format is as follows:
    # {(<ExecutionType>, <matrix_size>, <cores>): <value>}
    # value: dict with keys: "execution_time" and "communication_time"
    # where "execution_time" is a string and "communication_time" is a dict with keys as ranks and values as communication time
    see_data = False
    if see_data:
        print("Parsed data:")
        for key, value in parsed_data.items():
            print(f"{key}:")
            for k, v in value.items():
                print(f"  {k}:", end=" ")
                if isinstance(v, dict):
                    print("{")
                    for sub_k, sub_v in v.items():
                        print(f"    {sub_k}: {sub_v}")
                    print("  }")
                else:
                    print(v)

    # --- Generate Plots ---
    # Get unique matrix sizes and core counts from the data
    matrix_sizes = sorted(list(set(k[1] for k in parsed_data)))
    core_counts = sorted(list(set(k[2] for k in parsed_data)))

    output_dir: Path = parsed_args.output
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    # Generate plots for each matrix size and core count
    for size in matrix_sizes:
        plot_execution_time_vs_cores(parsed_data, size, output_dir)
        plot_communication_time_vs_cores(parsed_data, size, output_dir)

    for cores in core_counts:
        plot_execution_time_vs_matrix_size(parsed_data, cores, output_dir)

    print(f"Plots generated successfully!")

if __name__ == "__main__":
    main()
