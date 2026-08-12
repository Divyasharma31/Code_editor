import os
import subprocess
import tempfile
import time

def run_code(language: str, code: str, input_data: str, time_limit_ms: int):
    """
    Executes the given code in a temporary environment.
    Supported languages: python, cpp, javascript.
    Returns a dict with: status, output, error, time_taken_ms
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        time_limit_sec = time_limit_ms / 1000.0

        if language == "python":
            file_path = os.path.join(temp_dir, "solution.py")
            with open(file_path, "w") as f:
                f.write(code)
            cmd = ["python", file_path]
            return _execute_command(cmd, input_data, time_limit_sec, temp_dir)

        elif language == "cpp":
            source_path = os.path.join(temp_dir, "solution.cpp")
            exe_path = os.path.join(temp_dir, "solution.exe")
            with open(source_path, "w") as f:
                f.write(code)
            
            # Compile step
            compile_cmd = ["g++", "-O3", source_path, "-o", exe_path]
            try:
                compile_res = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=10)
                if compile_res.returncode != 0:
                    return {
                        "status": "Compilation Error",
                        "output": "",
                        "error": compile_res.stderr,
                        "time_taken_ms": 0
                    }
            except subprocess.TimeoutExpired:
                 return {
                        "status": "Compilation Time Exceeded",
                        "output": "",
                        "error": "Compilation took too long.",
                        "time_taken_ms": 0
                    }
            except FileNotFoundError:
                return {
                    "status": "Environment Error",
                    "output": "",
                    "error": "C++ compiler (g++) not found in system PATH.",
                    "time_taken_ms": 0
                }
            
            # Execution step
            cmd = [exe_path]
            return _execute_command(cmd, input_data, time_limit_sec, temp_dir)

        elif language == "javascript":
            file_path = os.path.join(temp_dir, "solution.js")
            with open(file_path, "w") as f:
                f.write(code)
            cmd = ["node", file_path]
            return _execute_command(cmd, input_data, time_limit_sec, temp_dir)

        else:
            return {
                "status": "Error",
                "output": "",
                "error": f"Unsupported language: {language}",
                "time_taken_ms": 0
            }


def _execute_command(cmd, input_data: str, time_limit_sec: float, cwd: str):
    start_time = time.time()
    try:
        process = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=time_limit_sec,
            cwd=cwd
        )
        end_time = time.time()
        time_taken_ms = int((end_time - start_time) * 1000)

        if process.returncode != 0:
            return {
                "status": "Runtime Error",
                "output": process.stdout,
                "error": process.stderr,
                "time_taken_ms": time_taken_ms
            }

        return {
            "status": "Success",
            "output": process.stdout,
            "error": "",
            "time_taken_ms": time_taken_ms
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "Time Limit Exceeded",
            "output": "",
            "error": f"Execution exceeded {time_limit_sec} seconds.",
            "time_taken_ms": int(time_limit_sec * 1000)
        }
    except FileNotFoundError:
        return {
            "status": "Environment Error",
            "output": "",
            "error": f"Executable not found for command: {cmd[0]}. Ensure it's installed and in your PATH.",
            "time_taken_ms": 0
        }
    except Exception as e:
        return {
            "status": "System Error",
            "output": "",
            "error": str(e),
            "time_taken_ms": 0
        }
