document.addEventListener("DOMContentLoaded", function() {
    var socket = io('/driver_in_front', {
        reconnection: true,
        reconnectionAttempts: Infinity,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        timeout: 20000
    });

    // Track connection status
    let isConnected = false;
    let reconnectTimer = null;

    // DOM elements - safely get elements and check if they exist
    const driverNameElement = document.getElementById("driver-name"); // This one doesn't exist in the HTML
    const lastLapTimeElement = document.getElementById("last-lap-time");
    const lapDeltaElement = document.getElementById("lap-delta");
    const targetPaceElement = document.getElementById("target-pace");
    const sessionTypeElement = document.getElementById("session-type");
    
    // Label elements
    const lapTimeLabelElement = document.getElementById("lap-time-label");
    const targetPaceLabelElement = document.getElementById("target-pace-label");

    // Delta timeout handler
    let deltaTimeoutId = null;
    
    // Track session type for UI adjustments
    let isRaceSession = true;
    let currentSessionType = "race";

    // Connect to socket
    socket.on('connect', function() {
        console.log("Connected to driver in front namespace");
        isConnected = true;
        clearTimeout(reconnectTimer);
    });

    // Listen for driver data updates
    socket.on('driver_in_front_update', function(data) {
        console.log("Received driver data:", data);
        updateDriverData(data);
    });

    // Handle heartbeats to ensure connection is alive
    socket.on('heartbeat', function(data) {
        console.log("Heartbeat received");
    });

    socket.on('disconnect', function() {
        console.log("Disconnected from driver in front namespace");
        isConnected = false;
        
        // Try to reconnect manually if socket.io reconnection fails
        reconnectTimer = setTimeout(function() {
            if (!isConnected) {
                console.log("Manually attempting to reconnect...");
                socket.connect();
            }
        }, 3000);
    });
    
    socket.on('error', function(error) {
        console.error("Socket error:", error);
    });
    
    socket.on('reconnect_attempt', function() {
        console.log("Attempting to reconnect...");
    });
    
    socket.on('reconnect', function(attemptNumber) {
        console.log("Reconnected after", attemptNumber, "attempts");
    });

    // Function to update the driver data in the UI
    function updateDriverData(data) {
        // Validate input data
        if (!data || typeof data !== 'object') {
            console.error('Invalid driver data received:', data);
            return;
        }

        // Update driver name (only if element exists)
        if (driverNameElement && data.name) {
            driverNameElement.textContent = data.name;
        } else if (driverNameElement) {
            driverNameElement.textContent = "Unknown";
        }

        // Get session type from data
        const sessionType = data.session_type || 'race';
        
        // Check if session type has changed
        if (sessionType !== currentSessionType) {
            currentSessionType = sessionType;
            isRaceSession = (sessionType === 'race');
            updateSessionDisplay();
        }
        
        // Update lap time display based on session type (check if element exists)
        if (lastLapTimeElement) {
            if (isRaceSession) {
                // Race session - show last lap time
                if (data.front_last_lap_time !== undefined && data.front_last_lap_time > 0) {
                    lastLapTimeElement.textContent = formatTimePrecise(data.front_last_lap_time);
                } else {
                    lastLapTimeElement.textContent = "-";
                }
            } else {
                // Practice/qualifying - show best lap time
                if (data.front_best_lap_time !== undefined && data.front_best_lap_time > 0) {
                    lastLapTimeElement.textContent = formatTimePrecise(data.front_best_lap_time);
                } else {
                    lastLapTimeElement.textContent = "-";
                }
            }
        }

        // Format delta text if it exists
        let deltaText = "-";
        let isPositiveDelta = false;
        
        if (data.lap_delta !== undefined && data.lap_delta !== 0) {
            isPositiveDelta = data.lap_delta > 0;
            const prefix = isPositiveDelta ? "+" : "-";
            const absValue = Math.abs(data.lap_delta);
            deltaText = prefix + formatDeltaTime(absValue);
        }

        // Update lap delta in different places based on session type
        if (isRaceSession) {
            // In race mode: show delta next to last lap time
            if (lapDeltaElement) {
                lapDeltaElement.textContent = deltaText;
                
                // Apply color class based on sign
                lapDeltaElement.classList.remove('positive', 'negative');
                if (data.lap_delta !== undefined && data.lap_delta !== 0) {
                    lapDeltaElement.classList.add(isPositiveDelta ? 'positive' : 'negative');
                    // Show delta with animation for 10 seconds
                    showDeltaWithTimeout(10000);
                } else {
                    lapDeltaElement.classList.remove('visible');
                }
            }
            
            // Update target pace for race mode
            if (targetPaceElement) {
                if (data.target_pace !== undefined && data.target_pace > 0) {
                    targetPaceElement.textContent = formatTimeRounded(data.target_pace);
                } else {
                    targetPaceElement.textContent = "-";
                }
            }
        } else {
            // In practice/qualifying: hide lap delta and show it in target pace element
            if (lapDeltaElement) {
                lapDeltaElement.textContent = "-";
                lapDeltaElement.classList.remove('visible', 'positive', 'negative');
            }
            
            // Put delta in target pace element
            if (targetPaceElement) {
                targetPaceElement.textContent = deltaText;
                
                // Apply appropriate color class
                targetPaceElement.classList.remove('positive', 'negative');
                if (data.lap_delta !== undefined && data.lap_delta !== 0) {
                    targetPaceElement.classList.add(isPositiveDelta ? 'positive' : 'negative');
                }
            }
        }
    }
    
    // Update UI labels and session display based on session type
    function updateSessionDisplay() {
        // Update labels (check if elements exist)
        if (lapTimeLabelElement) {
            lapTimeLabelElement.textContent = isRaceSession ? "Last Lap:" : "Best Lap:   ";
        }
        
        if (targetPaceLabelElement) {
            targetPaceLabelElement.textContent = isRaceSession ? "Target Pace:" : "Delta Gap:";
        }
        
        // Update session indicator (check if element exists)
        if (sessionTypeElement) {
            // Update session indicator
            sessionTypeElement.textContent = currentSessionType;
            
            // Remove all previous session classes
            sessionTypeElement.classList.remove('session-race', 'session-practice', 'session-qualify');
            
            // Add the current session class
            sessionTypeElement.classList.add(`session-${currentSessionType}`);
        }
    }

    // Helper function to format time precisely in X:YY:DDD format
    function formatTimePrecise(timeInSeconds) {
        if (timeInSeconds <= 0) return "-";
        
        const minutes = Math.floor(timeInSeconds / 60);
        const seconds = Math.floor(timeInSeconds % 60);
        const milliseconds = Math.floor((timeInSeconds % 1) * 1000);
        
        // Format with leading zeros
        const formattedSec = String(seconds).padStart(2, '0');
        const formattedMs = String(milliseconds).padStart(3, '0');
        
        // For less than a minute, just show seconds
        if (minutes === 0) {
            return `${formattedSec}.${formattedMs}`;
        }
        
        return `${minutes}:${formattedSec}.${formattedMs}`;
    }
    
    // Helper function to format delta time in S.DDD format
    function formatDeltaTime(timeInSeconds) {
        if (timeInSeconds <= 0) return "-";
        
        const seconds = Math.floor(timeInSeconds);
        const milliseconds = Math.floor((timeInSeconds % 1) * 1000);
        
        // Format with leading zeros for milliseconds
        const formattedMs = String(milliseconds).padStart(3, '0');
        
        return `${seconds}.${formattedMs}`;
    }
    
    // Helper function to format time rounded to one decimal (X:YY:D00)
    function formatTimeRounded(timeInSeconds) {
        if (timeInSeconds <= 0) return "-";
        
        const minutes = Math.floor(timeInSeconds / 60);
        const seconds = Math.floor(timeInSeconds % 60);
        const milliseconds = Math.floor((timeInSeconds % 1) * 1000);
        
        // Round to 1 decimal (hundreds of milliseconds)
        const roundedMs = Math.floor(milliseconds / 100) * 100;
        const formattedMs = String(roundedMs).padStart(3, '0');
        
        // Format with leading zeros
        const formattedSec = String(seconds).padStart(2, '0');
        
        // For less than a minute, just show seconds
        if (minutes === 0) {
            return `${formattedSec}.${formattedMs.charAt(0)}00`;
        }
        
        return `${minutes}:${formattedSec}.${formattedMs.charAt(0)}00`;
    }
    
    // Function to show delta with timeout
    function showDeltaWithTimeout(duration) {
        // Only proceed if the element exists
        if (!lapDeltaElement) return;
        
        // Clear any existing timeout
        if (deltaTimeoutId) {
            clearTimeout(deltaTimeoutId);
        }
        
        // Show delta
        lapDeltaElement.classList.add('visible');
        
        // Set timeout to hide delta
        deltaTimeoutId = setTimeout(() => {
            lapDeltaElement.classList.remove('visible');
        }, duration);
    }
    
    // Initialize the session display
    updateSessionDisplay();
});
