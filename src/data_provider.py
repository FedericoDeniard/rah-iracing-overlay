import irsdk
import os

class DataProvider:
    """
    Provides telemetry data from iRacing.
    Manages connection and data retrieval.
    """

    def __init__(self):
        self.ir_sdk = irsdk.IRSDK()
        self.is_connected = False
        self.lap_times = []  # Initialize lap_times here
        # Print the current working directory
        print(f"DataProvider initialized. Current working directory: {os.getcwd()}")

    def connect(self):
        """
        Establish connection to iRacing.
        """
        if not self.is_connected:
            self.is_connected = self.ir_sdk.startup()
            if self.is_connected:
                print("Connected to iRacing")
            else:
                print("Failed to connect to iRacing")

    def disconnect(self):
        """
        Disconnect from iRacing.
        """
        if self.is_connected:
            self.ir_sdk.shutdown()
            self.is_connected = False
            print("Disconnected from iRacing")

    def get_telemetry_data(self):
        """
        Retrieve telemetry data from iRacing.
        """
        if self.is_connected:
            self.ir_sdk.freeze_var_buffer_latest()
            data = {
                'speed': self.ir_sdk['Speed'] * 3.6,  # Convert to km/h
                'gear': self.ir_sdk['Gear'],
                'throttle': self.ir_sdk['Throttle'],
                'brake': self.ir_sdk['Brake'],
                'clutch': 1 - self.ir_sdk['Clutch'],  # Invert clutch value
                'steering_wheel_angle': self.ir_sdk['SteeringWheelAngle']
            }
            return data
        print("Not connected to iRacing")
        return {} 
    
    def get_lap_times(self):
        """
        Retrieve the last 10 lap times from iRacing.
        """
        if self.is_connected:
            current_lap = self.ir_sdk['Lap']
            lap_time = self.ir_sdk['LapCurrentLapTime']
            if current_lap > len(self.lap_times):
                # New lap completed
                self.lap_times.append(lap_time)
                if len(self.lap_times) > 10:
                    self.lap_times.pop(0)  # Keep only the last 10 lap times
            return self.lap_times
        print("Not connected to iRacing")
        return []