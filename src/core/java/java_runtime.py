import subprocess
from pathlib import Path



class JavaRuntime:
    @staticmethod
    def check(path:Path) -> subprocess.CompletedProcess:
        result = subprocess.run([str(path), "-version"], check=True, capture_output=True,text=True, timeout=8)
        return result