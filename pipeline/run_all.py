import subprocess, sys, os, pathlib

BASE = pathlib.Path(__file__).resolve().parent
def run(cmd):
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    root = BASE.parent
    run([sys.executable, "-m", "pipeline.run_harvest"]) 
    run([sys.executable, "-m", "pipeline.run_download"])
