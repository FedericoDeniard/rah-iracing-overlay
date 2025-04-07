from web_interface import WebInterface
from overlay_window import OverlayWindow
import sys
import multiprocessing
import os
import atexit
import signal
import time
import importlib

# Global variables to track processes
overlay_processes = []
web_interface_process = None
exit_flag = multiprocessing.Value('i', 0)  # Shared flag to signal program exit

def detect_overlays():
    """
    Detect available overlays in the overlays directory.
    """
    overlays_dir = os.path.join(os.path.dirname(__file__), 'overlays')
    return [name for name in os.listdir(overlays_dir) if os.path.isdir(os.path.join(overlays_dir, name))]

def cleanup():
    """
    Cleanup function to terminate all processes on exit
    """
    print("Cleaning up resources...")
    
    # Import the interface module to access the opened_overlays dictionary
    try:
        from interface import opened_overlays
        print(f"Found {len(opened_overlays)} active overlay windows to close")
        
        # Terminate all opened overlay processes
        for overlay_name, process in opened_overlays.items():
            try:
                if process and process.is_alive():
                    print(f"Terminating overlay: {overlay_name}")
                    process.terminate()
                    process.join(timeout=1)
            except Exception as e:
                print(f"Error closing overlay {overlay_name}: {e}")
    except Exception as e:
        print(f"Error accessing opened overlays: {e}")
    
    # Terminate all overlay processes we started directly
    for process in overlay_processes:
        if process.is_alive():
            process.terminate()
            process.join(timeout=1)
    
    # Terminate web interface process
    if web_interface_process and web_interface_process.is_alive():
        web_interface_process.terminate()
        web_interface_process.join(timeout=1)
    
    print("All processes terminated successfully")

def signal_handler(sig, frame):
    """
    Handle termination signals
    """
    print(f"Received signal {sig}, shutting down...")
    cleanup()
    sys.exit(0)

def main():
    """
    Main entry point for the iRacing Telemetry Overlay application.
    Initializes and runs the web interface with detected overlays.
    """
    global overlay_processes, web_interface_process
    
    # Register the cleanup function to be called on normal exit
    atexit.register(cleanup)
    
    # Register signal handlers for graceful termination
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination request
    
    try:
        # Start web interface in separate process
        selected_overlays = detect_overlays()
        web_interface_process = multiprocessing.Process(
            target=run_web_interface,
            args=(selected_overlays,)
        )
        web_interface_process.start()
        
        # Allow web server to initialize
        time.sleep(0.5)
        
        # Create the main interface window
        overlay_process = multiprocessing.Process(
            target=create_main_window,
            args=(exit_flag,)
        )
        overlay_process.start()
        overlay_processes.append(overlay_process)
        
        # Main loop - check for exit flag
        while True:
            if exit_flag.value == 1:
                print("Main window closed, initiating shutdown...")
                cleanup()
                break
            time.sleep(0.1)
            
        sys.exit(0)

    except KeyboardInterrupt:
        print("Shutting down gracefully...")
        cleanup()
        sys.exit(0)

def create_main_window(exit_flag):
    """
    Create the main window in a separate process
    """
    try:
        interface = OverlayWindow('http://127.0.0.1:8081/', width=1000, height=700, frameless=False)
        
        # Override window close handler
        def on_window_closed():
            exit_flag.value = 1
            
        interface.set_on_closed(on_window_closed)
        interface.create_overlay_window()
    except Exception as e:
        print(f"Error in main window process: {e}")
        exit_flag.value = 1

def run_web_interface(selected_overlays):
    """
    Run the web interface in a separate process
    """
    try:
        web_interface = WebInterface(selected_overlays)
        web_interface.run()
    except Exception as e:
        print(f"Error in web interface: {e}")

if __name__ == '__main__':
    multiprocessing.freeze_support()  # Needed for PyInstaller
    main()