import os
import sys
import platform

# Windows-specific configuration for eventlet
if platform.system() == 'Windows':
    # Patch environment before importing eventlet
    os.environ['EVENTLET_NO_GREENDNS'] = 'yes'
    # Comment out the hub selection to match web_interface.py
    # os.environ['EVENTLET_HUB'] = 'selectors'

from web_interface import WebInterface, using_fallback_mode
from overlay_window import OverlayWindow
import multiprocessing
import atexit
import signal
import time
import importlib
import subprocess
import threading

# Global variables to track processes
overlay_processes = []
web_interface_process = None
exit_flag = multiprocessing.Value('i', 0)  # Shared flag to signal program exit

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

def detect_overlays():
    """
    Detect available overlays in the overlays directory.
    """
    overlays_dir = resource_path('overlays')
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

def create_main_window_thread(exit_flag):
    """Create the main window in a thread instead of a process on Windows"""
    try:
        interface = OverlayWindow('http://127.0.0.1:8081/', width=1000, height=700, frameless=False)
        
        # Override window close handler
        def on_window_closed():
            exit_flag.value = 1
            
        interface.set_on_closed(on_window_closed)
        interface.create_overlay_window()
    except Exception as e:
        print(f"Error in main window thread: {e}")
        exit_flag.value = 1

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

def run_unified_app(selected_overlays):
    """
    Run both web interface and create window in the main thread
    This is used when we're in fallback mode to ensure pywebview runs in the main thread
    """
    try:
        # First start the web interface (but don't block)
        web_interface = WebInterface(selected_overlays)
        
        # Start the web interface in a separate thread
        web_thread = threading.Thread(target=lambda: web_interface.run())
        web_thread.daemon = True
        web_thread.start()
        
        # Allow web server to initialize
        time.sleep(1)
        
        # Create the main window in the main thread
        print("Creating main window in main thread...")
        interface = OverlayWindow('http://127.0.0.1:8081/', width=1000, height=700, frameless=False)
        
        # No need for on_closed handler since this is the main thread
        interface.create_overlay_window()
        
        # If we reach here, the window was closed
        print("Main window closed, shutting down...")
        
    except Exception as e:
        print(f"Error in unified app: {e}")

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
        # Detect overlays
        selected_overlays = detect_overlays()
        
        # Check if we are in fallback mode or frozen on Windows
        frozen_on_windows = platform.system() == 'Windows' and getattr(sys, 'frozen', False)
        
        # When using fallback mode, run everything in the main thread
        if using_fallback_mode or frozen_on_windows:
            print("Running in unified mode - web interface and window in same process")
            run_unified_app(selected_overlays)
            # If we get here, the application has been closed
            cleanup()
            return
            
        # Use standard multiprocessing approach
        web_interface_process = multiprocessing.Process(
            target=run_web_interface,
            args=(selected_overlays,)
        )
        web_interface_process.start()
        
        # Allow web server to initialize
        time.sleep(0.5)
        
        # On Windows with frozen app, use a thread for main window to avoid pipe issues
        if frozen_on_windows:
            import threading
            main_window_thread = threading.Thread(
                target=create_main_window_thread,
                args=(exit_flag,)
            )
            main_window_thread.daemon = True
            main_window_thread.start()
            
            # Wait for exit flag
            while True:
                if exit_flag.value == 1:
                    print("Main window closed, initiating shutdown...")
                    cleanup()
                    break
                time.sleep(0.1)
        else:
            # Create the main interface window as a process (normal approach)
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

if __name__ == '__main__':
    multiprocessing.freeze_support()  # Needed for PyInstaller
    main()