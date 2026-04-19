import subprocess
import sys
import os
import time

def run_diagnostic():
    print(f"Current Directory: {os.getcwd()}")
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8503", "--server.headless", "true"]
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False
        )
        
        # Wait for a bit
        time.sleep(10)
        
        # Check if process is still running
        retcode = proc.poll()
        if retcode is not None:
            print(f"Process terminated with code: {retcode}")
            stdout, stderr = proc.communicate()
            print("--- STDOUT ---")
            print(stdout)
            print("--- STDERR ---")
            print(stderr)
        else:
            print("Process is still running after 10s. Trying to read first few lines...")
            # We can't easily read if it's blocking, but we'll try communicate with timeout
            try:
                stdout, stderr = proc.communicate(timeout=2)
                print("--- STDOUT ---")
                print(stdout)
                print("--- STDERR ---")
                print(stderr)
            except subprocess.TimeoutExpired:
                print("Timeout expired while reading. Still running.")
                proc.kill() # Clean up

    except Exception as e:
        print(f"Execution Error: {e}")

if __name__ == "__main__":
    run_diagnostic()
