from web_interface import WebInterface
from overlay_window import OverlayWindow
import sys
import multiprocessing

def main():
    """
    Main entry point for the iRacing Telemetry Overlay application.
    Initializes and runs the web interface with selected overlays.
    """
    try:
        selected_overlays = ['input_telemetry']
        web_interface = WebInterface(selected_overlays)
        web_interface.run()
        print("Web interface running with selected overlays:", selected_overlays)
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
        web_interface.data_provider.disconnect()
        sys.exit(0)

if __name__ == '__main__':
    main()