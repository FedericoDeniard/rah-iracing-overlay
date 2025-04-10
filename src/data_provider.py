import irsdk
import os
import logging

class DataProvider:
    """
    Provides telemetry data from iRacing.
    Manages connection and data retrieval.
    """

    def __init__(self):
        self.ir_sdk = irsdk.IRSDK()
        self.is_connected = False
        self.lap_times = []  # Initialize lap_times here
        # Use debug level for this information instead of print
        logging.debug(f"DataProvider initialized. Current working directory: {os.getcwd()}")

    def connect(self):
        """
        Establish connection to iRacing.
        """
        if not self.is_connected:
            self.is_connected = self.ir_sdk.startup()
            if self.is_connected:
                logging.info("Connected to iRacing")
            else:
                logging.warning("Failed to connect to iRacing")

    def disconnect(self):
        """
        Disconnect from iRacing.
        """
        if self.is_connected:
            self.ir_sdk.shutdown()
            self.is_connected = False
            logging.info("Disconnected from iRacing")

    def get_telemetry_data(self):
        """
        Retrieve telemetry data from iRacing.
        """
        if self.is_connected:
            try:
                self.ir_sdk.freeze_var_buffer_latest()
                
                # Get speed and convert to km/h with type checking
                speed = self.ir_sdk['Speed']
                if speed is not None and isinstance(speed, (int, float)):
                    speed_kmh = speed * 3.6  # Convert to km/h
                else:
                    speed_kmh = 0.0  # Default value if speed is invalid
                
                # Get other values with safety checks
                gear = self.ir_sdk['Gear'] or 0
                throttle = self.ir_sdk['Throttle'] or 0.0
                brake = self.ir_sdk['Brake'] or 0.0
                clutch = self.ir_sdk['Clutch']
                # Invert clutch value with safety check
                clutch_value = 1.0 - float(clutch) if clutch is not None and isinstance(clutch, (int, float)) else 1.0
                
                steering = self.ir_sdk['SteeringWheelAngle']
                if not isinstance(steering, (int, float)):
                    steering = 0.0
                
                data = {
                    'speed': speed_kmh,
                    'gear': gear,
                    'throttle': float(throttle),
                    'brake': float(brake),
                    'clutch': clutch_value,
                    'steering_wheel_angle': float(steering)
                }
                return data
            except (TypeError, ValueError, KeyError) as e:
                logging.error(f"Error processing telemetry data: {e}")
                # Fallback with default values if there's an error
                return {
                    'speed': 0.0,
                    'gear': 0,
                    'throttle': 0.0,
                    'brake': 0.0,
                    'clutch': 1.0,
                    'steering_wheel_angle': 0.0
                }
            except Exception as e:
                logging.error(f"Unexpected error in get_telemetry_data: {e}")
                return {}
                
        logging.debug("Not connected to iRacing")
        return {}
    
    def get_lap_times(self):
        """
        Retrieve the last 10 lap times from iRacing.
        """
        if self.is_connected:
            try:
                current_lap = self.ir_sdk['Lap']
                
                # Check if current_lap is a valid number
                if current_lap is None or not isinstance(current_lap, (int, float)):
                    return self.lap_times
                
                current_lap = int(current_lap)
                
                lap_time = self.ir_sdk['LapCurrentLapTime']
                
                # Validate lap_time is a number
                if lap_time is None or not isinstance(lap_time, (int, float)):
                    lap_time = 0.0
                
                # Convert lap_time to float if it's not already
                lap_time = float(lap_time)
                
                if current_lap > len(self.lap_times):
                    # New lap completed
                    self.lap_times.append(lap_time)
                    if len(self.lap_times) > 10:
                        self.lap_times.pop(0)  # Keep only the last 10 lap times
                
                return self.lap_times
            except (TypeError, ValueError, KeyError) as e:
                logging.error(f"Error processing lap times: {e}")
                return self.lap_times
            except Exception as e:
                logging.error(f"Unexpected error in get_lap_times: {e}")
                return []
                
        logging.debug("Not connected to iRacing")
        return []