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
    
def main() -> int:
    parser = ArgumentParser(description="Parse and process files in a directory.")
    parser.add_argument("--file", "-f", type=Path, help="Json file to process", required=True)

    parsed_args = parser.parse_args()
    file_path: Path = parsed_args.file
    if not file_path.is_file():
        print(f"Error: The specified file '{file_path}' does not exist or is not a file.")
        return 1
    
    initial_data = json.loads(file_path.read_text(encoding="utf-8"))
    parsed_data: dict[tuple[ExecutionType, int, int], dict[str, str | dict[str, str]]] = {get_key(k): v for k, v in initial_data.items()}
    # Data format is as follows:
    # {(<ExecutionType>, <matrix_size>, <cores>): <value>}
    # value: dict with keys: "execution_time" and "communication_time_per_rank"
    # where "execution_time" is a string and "communication_time_per_rank" is a dict with keys as ranks and values as communication time
    see_data = True
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

if __name__ == "__main__":
    main()
