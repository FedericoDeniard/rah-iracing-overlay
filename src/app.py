from web_interface import WebInterface
from overlay_window import OverlayWindow
import sys
import multiprocessing

def main():
    """
    Main entry point for the iRacing Telemetry Overlay application.
    Initializes and runs the web interface.
    """
    try:
        web_interface = WebInterface()
        web_interface.run()
        print("Web interface running")
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
        web_interface.data_provider.disconnect()
        sys.exit(0)

if __name__ == '__main__':
    main()