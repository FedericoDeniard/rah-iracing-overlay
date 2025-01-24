from telemetry.web_interface import TelemetryWebInterface
from overlay_window import OverlayWindow
import sys
import multiprocessing

def main():
    """
    Main entry point for the iRacing Telemetry Overlay application.
    Initializes and runs the web interface.
    """
    try:
        telemetry_interface = TelemetryWebInterface()
        telemetry_interface.run()
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
        telemetry_interface.data_provider.disconnect()
        sys.exit(0)

if __name__ == '__main__':
    main()