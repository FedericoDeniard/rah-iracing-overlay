import os
import subprocess
import sys
import shutil
import platform
import time

def check_requirements():
    """Check if required packages are installed"""
    try:
        import PyInstaller
        print("PyInstaller found!")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Check other dependencies
    required_packages = ["irsdk", "flask", "flask_socketio", "eventlet", "pywebview", "dnspython"]
    for package in required_packages:
        try:
            __import__(package)
            print(f"{package} found!")
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def build_exe():
    """Build the executable using PyInstaller"""
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(script_dir, "src")
    
    # Remove old build and dist directories if they exist
    for dir_name in ["build", "dist"]:
        path = os.path.join(script_dir, dir_name)
        if os.path.exists(path):
            print(f"Removing old {dir_name} directory...")
            try:
                shutil.rmtree(path)
            except PermissionError as e:
                print(f"\nERROR: Cannot remove {dir_name} directory. Files may be in use by another process.")
                print("Please close any applications that might be using files in this directory.")
                print("Specifically, make sure you've closed any instances of RAH_Telemetry_Overlay.")
                print(f"Error details: {e}")
                print("\nTry one of the following solutions:")
                print("1. Close any running instances of the application")
                print("2. Restart your computer")
                print("3. Manually delete the directory before running this script again")
                sys.exit(1)
    
    # Get spec file path
    spec_file = os.path.join(src_dir, "RAH_Telemetry_Overlay.spec")
    
    # Build the executable
    print("Building executable...")
    os.chdir(script_dir)  # Change to project root directory
    
    # Use absolute paths for everything to avoid working directory issues
    dist_path = os.path.join(script_dir, "dist")
    work_path = os.path.join(script_dir, "build")
    
    subprocess.check_call([
        sys.executable, 
        "-m", 
        "PyInstaller", 
        spec_file,
        "--distpath", 
        dist_path,
        "--workpath", 
        work_path
    ])
    
    print("\n============ BUILD COMPLETED ============")
    print("The executable should be in the 'dist/RAH_Telemetry_Overlay' directory.")
    print("To run the application, double-click on 'RAH_Telemetry_Overlay.exe'")

if __name__ == "__main__":
    print("========== Building RAH Telemetry Overlay ==========")
    print(f"Python version: {platform.python_version()}")
    print(f"Operating system: {platform.system()} {platform.release()}")
    
    check_requirements()
    build_exe() 