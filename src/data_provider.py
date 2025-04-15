import irsdk
import os
import logging
from typing import Dict, List, Optional, Union, Any

class DataProvider:
    """
    Provides telemetry data from iRacing.
    
    This class manages the connection to the iRacing SDK and handles
    retrieval of telemetry data and lap times for overlays.
    """

    def __init__(self) -> None:
        """
        Initialize the DataProvider with default values.
        """
        self.ir_sdk = irsdk.IRSDK()
        self.is_connected = False
        self.lap_times: List[float] = []
        logging.debug(f"DataProvider initialized. Current working directory: {os.getcwd()}")

    def connect(self) -> bool:
        """
        Establish connection to iRacing.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if not self.is_connected:
            self.is_connected = self.ir_sdk.startup()
            if self.is_connected:
                logging.info("Connected to iRacing")
            else:
                logging.warning("Failed to connect to iRacing")
        return self.is_connected

    def disconnect(self) -> None:
        """
        Disconnect from iRacing and clean up resources.
        """
        if self.is_connected:
            self.ir_sdk.shutdown()
            self.is_connected = False
            logging.info("Disconnected from iRacing")

    def get_telemetry_data(self) -> Dict[str, Union[float, int]]:
        """
        Retrieve telemetry data from iRacing.
        
        Returns:
            Dict[str, Union[float, int]]: Dictionary containing telemetry values
                or empty dict if not connected or error occurs
        """
        if not self.is_connected:
            logging.debug("Not connected to iRacing")
            return {}
            
        try:
            self.ir_sdk.freeze_var_buffer_latest()
            return self._extract_telemetry_data()
        except (TypeError, ValueError, KeyError) as e:
            logging.error(f"Error processing telemetry data: {e}")
            return self._get_default_telemetry()
        except Exception as e:
            logging.error(f"Unexpected error in get_telemetry_data: {e}")
            return {}
    
    def _extract_telemetry_data(self) -> Dict[str, Union[float, int]]:
        """
        Extract and normalize telemetry data from iRacing SDK.
        
        Returns:
            Dict[str, Union[float, int]]: Normalized telemetry data
        """
        speed = self.ir_sdk['Speed']
        speed_kmh = speed * 3.6 if isinstance(speed, (int, float)) and speed is not None else 0.0
        
        gear = self.ir_sdk['Gear'] or 0
        throttle = self.ir_sdk['Throttle'] or 0.0
        brake = self.ir_sdk['Brake'] or 0.0
        
        clutch = self.ir_sdk['Clutch']
        clutch_value = 1.0 - float(clutch) if isinstance(clutch, (int, float)) and clutch is not None else 1.0
        
        steering = self.ir_sdk['SteeringWheelAngle']
        steering_value = float(steering) if isinstance(steering, (int, float)) else 0.0
        
        return {
            'speed': speed_kmh,
            'gear': gear,
            'throttle': float(throttle),
            'brake': float(brake),
            'clutch': clutch_value,
            'steering_wheel_angle': steering_value
        }
    
    def _get_default_telemetry(self) -> Dict[str, Union[float, int]]:
        """
        Provide default telemetry values when data cannot be retrieved.
        
        Returns:
            Dict[str, Union[float, int]]: Default telemetry values
        """
        return {
            'speed': 0.0,
            'gear': 0,
            'throttle': 0.0,
            'brake': 0.0,
            'clutch': 1.0,
            'steering_wheel_angle': 0.0
        }
    
    def get_lap_times(self) -> List[float]:
        """
        Retrieve the last 10 lap times from iRacing.
        
        Updates internal lap times list and returns all stored times.
        
        Returns:
            List[float]: List of up to 10 most recent lap times or empty list if not connected
        """
        if not self.is_connected:
            logging.debug("Not connected to iRacing")
            return []
        
        try:
            self._update_lap_times()
            return self.lap_times
        except (TypeError, ValueError, KeyError) as e:
            logging.error(f"Error processing lap times: {e}")
            return self.lap_times
        except Exception as e:
            logging.error(f"Unexpected error in get_lap_times: {e}")
            return []
    
    def _update_lap_times(self) -> None:
        """
        Update the stored lap times with new data from iRacing.
        """
        current_lap = self.ir_sdk['Lap']
        
        if not isinstance(current_lap, (int, float)) or current_lap is None:
            return
        
        current_lap = int(current_lap)
        lap_time = self.ir_sdk['LapCurrentLapTime']
        
        if not isinstance(lap_time, (int, float)) or lap_time is None:
            lap_time = 0.0
        
        lap_time = float(lap_time)
        
        if current_lap > len(self.lap_times):
            self.lap_times.append(lap_time)
            if len(self.lap_times) > 10:
                self.lap_times.pop(0)