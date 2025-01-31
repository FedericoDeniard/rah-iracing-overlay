from web_interface import WebInterface
from overlay_window import OverlayWindow
import sys
import multiprocessing
import os

def detect_overlays():
    """
    Detect available overlays in the overlays directory.
    """
    overlays_dir = os.path.join(os.path.dirname(__file__), 'overlays')
    return [name for name in os.listdir(overlays_dir) if os.path.isdir(os.path.join(overlays_dir, name))]

def main():
    """
    Main entry point for the iRacing Telemetry Overlay application.
    Initializes and runs the web interface with detected overlays.
    """
    try:
        interface = OverlayWindow('http://127.0.0.1:8081/', width=1000, height=700, frameless=False)
        overlay_process = multiprocessing.Process(target=interface.create_overlay_window)
        overlay_process.start()
        
        selected_overlays = detect_overlays()
        web_interface = WebInterface(selected_overlays)
        web_interface.run()

    except KeyboardInterrupt:
        print("Shutting down gracefully...")
        web_interface.data_provider.disconnect()
        sys.exit(0)

if __name__ == '__main__':
    main()