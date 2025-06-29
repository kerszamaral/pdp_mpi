from pathlib import Path
from argparse import ArgumentParser
import json
from enum import StrEnum

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

def main() -> int:
    parser = ArgumentParser(description="Parse and process files in a directory.")
    parser.add_argument("--directory", "-d", type=Path, help="Directory containing files to parse", required=True)
    parser.add_argument("--output", "-o", type=Path, help="Output file to write results", default=Path("output.json"))
    
    parsed_args = parser.parse_args()
    directory: Path = parsed_args.directory
    if not directory.is_dir():
        print(f"Error: The specified directory '{directory}' does not exist or is not a directory.")
        return 1

    types_of_execs: set[ExecutionType] = set()
    matrix_sizes: set[int] = set()
    cores_used: set[int] = set()
    # Want a dataframe with the following keys: types_of_execs, matrix_sizes, and cores_used, it contains a dict with the keys: execution time, and Communication Time per Rank (as just a number of the ranks)
    results: dict[tuple[ExecutionType, int, int], dict[str, str | dict[str, str]]] = {}

    for file_path in directory.glob("*.out"):
        if not file_path.is_file():
            continue
        file_name = file_path.name
        file_name = file_name.split(".")[0]  # Remove the file extension
        try:
            name_split = file_name.split("_")
            if name_split[1] == "p2p":
                name_split[1] = name_split[2]
                matrix_size = int(name_split[3])
                cores = int(name_split[4])
            else:
                matrix_size = int(name_split[2])
                cores = int(name_split[3])

            exec_type = ExecutionType.from_string(name_split[1])
            types_of_execs.add(exec_type)
            matrix_sizes.add(matrix_size)
            cores_used.add(cores)
            key = (exec_type, matrix_size, cores)
            if key not in results:
                results[key] = {"execution_time": "", "communication_time": {}}
        except Exception as e:
            print(f"Error processing file {file_name}: {e}")
            continue
        
        with file_path.open("r") as file:
            content = file.readlines()
            filtered_content = [line.strip() for line in content if not line.strip().startswith("#")]
            sorted_content = sorted(filtered_content)
            try:
                for line in sorted_content:
                    if "Execution time" in line:
                        index_of_execution_time = sorted_content.index(line)
                        break
                else:
                    raise ValueError("Execution time not found in the file.")

                execution_time = sorted_content.pop(index_of_execution_time)
                execution_time = execution_time.split(":")[1].strip().split(" ")[0].strip()
                results[key]["execution_time"] = execution_time
                comm_time_per_rank = {}
                for line in sorted_content:
                    rank, comm_time = line.split(": ")
                    rank = rank.split(" ")[1].strip()
                    comm_time = comm_time.split(" ")[0].strip()
                    comm_time_per_rank[rank] = comm_time
                results[key]["communication_time"] = comm_time_per_rank
            except Exception as e:
                print(f"Error parsing file {file_name}: {e}")
                continue

    output_file: Path = parsed_args.output
    print(f"Writing results to {output_file}")
    print(f"Types of executions: {types_of_execs}")
    print(f"Matrix sizes: {matrix_sizes}")
    print(f"Cores used: {cores_used}")
    
    with output_file.open("w") as file:
        json.dump({str(k): v for k, v in results.items()}, file, indent=4)

if __name__ == "__main__":
    main()