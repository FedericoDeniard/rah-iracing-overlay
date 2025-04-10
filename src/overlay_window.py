import webview
import sys
import json
import threading
import time
import ctypes

def get_windows_dpi_scaling():
    """Get the Windows DPI scaling factor"""
    try:
        if sys.platform == 'win32':
            user32 = ctypes.windll.user32
            # Get DPI awareness context
            try: 
                # Try Windows 10 API first
                awareness = user32.GetDpiAwarenessContextForWindow(0)
                if awareness:
                    dpi = user32.GetDpiForWindow(0)
                    return dpi / 96.0  # 96 is the base DPI
            except AttributeError:
                # Fall back to older API
                try:
                    user32.SetProcessDPIAware()
                    dc = user32.GetDC(0)
                    dpi_x = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
                    user32.ReleaseDC(0, dc)
                    return dpi_x / 96.0
                except:
                    pass
        # Default fallback
        return 1.0
    except Exception as e:
        print(f"Error getting DPI scaling: {e}")
        return 1.0

class OverlayWindow:
    def __init__(self, url, width, height, frameless=True, transparent=False):
        self.url = url
        self.window = None
        self.width = width
        self.height = height
        self.frameless = frameless
        self.transparent = transparent
        self.on_closed = None
        self.position = None
        self.folder_name = None  # Store folder name for position reporting
        self.position_tracker_thread = None
        self.position_offset = {'x': 0, 'y': 0}  # Store offset for position correction
        self.dpi_scale = get_windows_dpi_scaling()  # Get Windows DPI scaling factor
        print(f"Windows DPI scaling detected: {self.dpi_scale}")
        self.window_closed = threading.Event()  # Use threading.Event instead of destroy_event

    def set_folder_name(self, folder_name):
        """Set the folder name for position reporting"""
        self.folder_name = folder_name

    def set_on_closed(self, callback):
        """
        Set the callback function to be called when the window is closed
        """
        self.on_closed = callback

    def create_overlay_window(self):
        self.window_closed.clear()
        adjusted_position = None
        if self.position:
            adjusted_position = {
                'x': int(self.position.get('x', 0) / self.dpi_scale),
                'y': int(self.position.get('y', 0) / self.dpi_scale)
            }
            print(f"Original position: {self.position}, Adjusted for DPI: {adjusted_position}")
        
        window_args = {
            "title": "iRacing Overlay",
            "url": self.url,
            "width": self.width,
            "height": self.height,
            "frameless": self.frameless,
            "transparent": self.transparent,
            "on_top": True,
            "easy_drag": True,
            "min_size": (200, 100),
            "background_color": "#000000",
            "text_select": False
        }
        
        if adjusted_position:
            window_args["x"] = adjusted_position.get('x', 0)
            window_args["y"] = adjusted_position.get('y', 0)
        
        try:
            self.window = webview.create_window(**window_args)
            
            if self.on_closed:
                self.window.events.closed += self.on_closed_handler
                
            if not self.transparent and self.folder_name:
                self.window.events.loaded += self.inject_position_reporter
                
                self.position_tracker_thread = threading.Thread(target=self.track_window_position)
                self.position_tracker_thread.daemon = True
                self.position_tracker_thread.start()
            
            webview.start(gui='edgechromium', debug=False)
        except Exception as e:
            print(f"Error creating overlay window: {e}")
    
    def track_window_position(self):
        """Continuously track window position and expose it to the window"""
        if not self.window:
            return
            
        try:
            time.sleep(1)
            
            js_dpi = f"""
            if (!window.pywebview) {{
                window.pywebview = {{}};
            }}
            window.pywebview.dpiScale = {self.dpi_scale};
            console.log("DPI Scale:", {self.dpi_scale});
            """
            self.window.evaluate_js(js_dpi)
            
            while self.window and not self.window_closed.is_set():
                try:
                    x, y = self.window.x, self.window.y
                    
                    scaled_x = int(x * self.dpi_scale)
                    scaled_y = int(y * self.dpi_scale)
                    
                    js = f"""
                    if (!window.pywebview) {{
                        window.pywebview = {{}};
                    }}
                    window.pywebview.position = {{
                        x: {scaled_x},
                        y: {scaled_y}
                    }};
                    
                    // Update position display if it exists
                    var display = document.getElementById('position-display');
                    if (display) {{
                        display.textContent = 'Position: ({scaled_x}, {scaled_y}) - DPI: {self.dpi_scale}x';
                    }}
                    
                    // Update save button display if it exists
                    var saveBtn = document.getElementById('position-save-button');
                    if (saveBtn) {{
                        var btnHtml = '<span>Save Position</span><small style="display:block;font-size:10px;margin-top:2px;">Current: ({scaled_x}, {scaled_y})</small>';
                        if (saveBtn.innerHTML.indexOf('Position Saved!') >= 0) {{
                            btnHtml = '<span>Position Saved!</span><small style="display:block;font-size:10px;margin-top:2px;">({scaled_x}, {scaled_y})</small>';
                        }}
                        saveBtn.innerHTML = btnHtml;
                    }}
                    """
                    self.window.evaluate_js(js)
                except Exception as e:
                    print(f"Error updating position in JavaScript: {e}")
                    
                # Update every 100ms
                time.sleep(0.1)
        except Exception as e:
            print(f"Error in position tracker thread: {e}")
    
    def inject_position_reporter(self):
        """Inject JavaScript to periodically report window position"""
        if not self.window or not self.folder_name:
            return
            
        self.window.evaluate_js("""
            // Add a subtle positioning mode indicator to the telemetry container
            const overlayContainer = document.querySelector('.telemetry-container');
            if (overlayContainer) {
                // Add a border indicator to show we're in positioning mode
                overlayContainer.style.border = '2px dashed rgba(46, 204, 113, 0.8)';
                
                // Add a small indicator in the top-left corner
                const modeIndicator = document.createElement('div');
                modeIndicator.id = 'positioning-mode-indicator';
                modeIndicator.style.position = 'absolute';
                modeIndicator.style.top = '10px';
                modeIndicator.style.left = '10px';
                modeIndicator.style.backgroundColor = 'rgba(46, 204, 113, 0.9)';
                modeIndicator.style.color = 'white';
                modeIndicator.style.padding = '4px 8px';
                modeIndicator.style.borderRadius = '4px';
                modeIndicator.style.zIndex = '9999';
                modeIndicator.style.fontFamily = 'Arial, sans-serif';
                modeIndicator.style.fontSize = '11px';
                modeIndicator.style.fontWeight = 'bold';
                modeIndicator.style.opacity = '0.9';
                modeIndicator.textContent = 'POSITIONING MODE';
                
                overlayContainer.appendChild(modeIndicator);
                
                // Add a pulse animation to the container
                const style = document.createElement('style');
                style.textContent = `
                    .telemetry-container {
                        animation: pulse 2s infinite;
                    }
                    @keyframes pulse {
                        0% { box-shadow: 0 0 15px rgba(46, 204, 113, 0.2); }
                        50% { box-shadow: 0 0 20px rgba(46, 204, 113, 0.8); }
                        100% { box-shadow: 0 0 15px rgba(46, 204, 113, 0.2); }
                    }
                `;
                document.head.appendChild(style);
            }
        """)
            
        js_code = """
        // Variables to store current position
        let currentX = 0;
        let currentY = 0;
        let initialX = 0;
        let initialY = 0;
        let positionReported = false;
        let dpiScale = window.pywebview && window.pywebview.dpiScale ? window.pywebview.dpiScale : 1.0;
        
        console.log("DPI Scale in position reporter:", dpiScale);
        
        // Record initial position after window is fully loaded
        setTimeout(function() {
            if (window.pywebview && window.pywebview.position) {
                initialX = window.pywebview.position.x;
                initialY = window.pywebview.position.y;
                console.log("Initial position:", initialX, initialY);
            }
        }, 1000);
        
        // Create a position reporter that runs every second
        setInterval(function() {
            try {
                // Try to get position from pywebview API first (more accurate, set by our Python code)
                if (window.pywebview && window.pywebview.position) {
                    currentX = window.pywebview.position.x;
                    currentY = window.pywebview.position.y;
                } else {
                    // Fallback to browser methods
                    currentX = window.screenX || window.screenLeft || 0;
                    currentY = window.screenY || window.screenTop || 0;
                    
                    // Apply DPI scaling
                    currentX = Math.round(currentX * dpiScale);
                    currentY = Math.round(currentY * dpiScale);
                }
            } catch (e) {
                console.error("Error getting position:", e);
            }
            
            // Create floating save button if it doesn't exist
            if (!document.getElementById('position-save-button')) {
                var saveBtn = document.createElement('div');
                saveBtn.id = 'position-save-button';
                saveBtn.style.position = 'absolute';
                saveBtn.style.top = '10px';
                saveBtn.style.right = '10px';
                saveBtn.style.zIndex = '9999999';
                saveBtn.style.padding = '6px 10px';
                saveBtn.style.backgroundColor = 'rgba(46, 204, 113, 0.95)';
                saveBtn.style.color = 'white';
                saveBtn.style.borderRadius = '8px';
                saveBtn.style.cursor = 'pointer';
                saveBtn.style.boxShadow = '0 4px 10px rgba(0, 0, 0, 0.5)';
                saveBtn.style.fontSize = '13px';
                saveBtn.style.fontFamily = 'Arial, sans-serif';
                saveBtn.style.backdropFilter = 'blur(5px)';
                saveBtn.style.border = '2px solid white';
                saveBtn.style.transition = 'all 0.3s ease';
                saveBtn.style.pointerEvents = 'auto';
                
                // Add a floppy disk icon
                saveBtn.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                            <polyline points="17 21 17 13 7 13 7 21"></polyline>
                            <polyline points="7 3 7 8 15 8"></polyline>
                        </svg>
                        <div>
                            <span style="font-weight: 500;">Save Position</span>
                        </div>
                    </div>
                `;
                
                saveBtn.addEventListener('mouseover', function() {
                    this.style.backgroundColor = 'rgba(39, 174, 96, 0.95)';
                    this.style.transform = 'translateY(-2px)';
                });
                
                saveBtn.addEventListener('mouseout', function() {
                    this.style.backgroundColor = 'rgba(46, 204, 113, 0.95)';
                    this.style.transform = 'translateY(0)';
                });
                
                // Update the saving state styling
                function updateSaveBtnState(state, x, y) {
                    if (state === 'saving') {
                        saveBtn.style.backgroundColor = 'rgba(243, 156, 18, 0.9)';
                        saveBtn.innerHTML = `
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" stroke-dasharray="1, 2"></path>
                                </svg>
                                <div>
                                    <span style="font-weight: 500;">Saving...</span>
                                </div>
                            </div>
                        `;
                    } else if (state === 'success') {
                        saveBtn.style.backgroundColor = 'rgba(39, 174, 96, 0.95)';
                        saveBtn.innerHTML = `
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M20 6L9 17l-5-5"></path>
                                </svg>
                                <div>
                                    <span style="font-weight: 500;">Saved!</span>
                                </div>
                            </div>
                        `;
                    } else if (state === 'error') {
                        saveBtn.style.backgroundColor = 'rgba(231, 76, 60, 0.95)';
                        saveBtn.innerHTML = `
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <line x1="12" y1="8" x2="12" y2="12"></line>
                                    <line x1="12" y1="16" x2="12" y2="16"></line>
                                </svg>
                                <div>
                                    <span style="font-weight: 500;">Error!</span>
                                </div>
                            </div>
                        `;
                    } else {
                        saveBtn.style.backgroundColor = 'rgba(46, 204, 113, 0.95)';
                        saveBtn.innerHTML = `
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path>
                                    <polyline points="17 21 17 13 7 13 7 21"></polyline>
                                    <polyline points="7 3 7 8 15 8"></polyline>
                                </svg>
                                <div>
                                    <span style="font-weight: 500;">Save Position</span>
                                </div>
                            </div>
                        `;
                    }
                }
                
                saveBtn.addEventListener('click', function() {
                    // Get the most current position directly
                    let x = currentX;
                    let y = currentY;
                    
                    // Update visual state to saving
                    updateSaveBtnState('saving', x, y);
                    
                    // Report position on button click
                    fetch('/report_window_position', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            folder_name: '%s',
                            position: {
                                x: x,
                                y: y
                            },
                            dpi_scale: dpiScale
                        })
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.status === 'success') {
                            // Update to success state
                            updateSaveBtnState('success', x, y);
                            
                            // Close window automatically after successful save
                            setTimeout(function() {
                                window.close();
                            }, 1000);
                        } else {
                            throw new Error(data.message || 'Unknown error');
                        }
                    })
                    .catch(error => {
                        console.error('Error saving position:', error);
                        // Update to error state
                        updateSaveBtnState('error', x, y);
                        
                        setTimeout(function() {
                            updateSaveBtnState('default', currentX, currentY);
                        }, 2000);
                    });
                });
                
                // Find the overlay container and append the save button to it
                var overlayContainer = document.querySelector('.telemetry-container');
                if (overlayContainer) {
                    // Make the container position relative if it's not already
                    if (window.getComputedStyle(overlayContainer).position !== 'relative') {
                        overlayContainer.style.position = 'relative';
                    }
                    
                    // Add the save button directly to the overlay container
                    overlayContainer.appendChild(saveBtn);
                } else {
                    // Fallback to body if container not found
                    document.body.appendChild(saveBtn);
                }
                
                // Add position display that updates with current position
                var positionDisplay = document.createElement('div');
                positionDisplay.id = 'position-display';
                positionDisplay.style.position = 'fixed';
                positionDisplay.style.bottom = '10px';
                positionDisplay.style.left = '10px';
                positionDisplay.style.zIndex = '9999999';
                positionDisplay.style.padding = '4px 8px';
                positionDisplay.style.backgroundColor = 'rgba(0,0,0,0.8)';
                positionDisplay.style.color = 'white';
                positionDisplay.style.borderRadius = '4px';
                positionDisplay.style.fontSize = '12px';
                positionDisplay.style.fontFamily = 'monospace';
                positionDisplay.style.pointerEvents = 'none';
                positionDisplay.textContent = `Position: (${currentX}, ${currentY}) - DPI: ${dpiScale}x`;
                
                document.body.appendChild(positionDisplay);
            }
        }, 1000);
        """ % self.folder_name
        
        self.window.evaluate_js(js_code)
    
    def on_closed_handler(self):
        """
        Handler called when the window is closed
        """
        # Set window closed flag
        self.window_closed.set()
        
        if self.on_closed:
            self.on_closed()
            
    def get_position(self):
        """
        Get the current position of the window
        """
        if self.window:
            # Get the raw position
            raw_x, raw_y = self.window.x, self.window.y
            
            # Scale it to account for DPI
            return {
                'x': int(raw_x * self.dpi_scale), 
                'y': int(raw_y * self.dpi_scale)
            }
        return None
        
    def set_position(self, x, y):
        """
        Set the position of the window
        """
        # Store the raw position
        self.position = {'x': x, 'y': y}
        
        if self.window:
            # Adjust for DPI when setting window position
            adjusted_x = int(x / self.dpi_scale)
            adjusted_y = int(y / self.dpi_scale)
            print(f"Moving window to: {adjusted_x}, {adjusted_y} (original: {x}, {y})")
            self.window.move(adjusted_x, adjusted_y)
            
    def toggle_transparency(self):
        """
        Toggle the transparency of the window
        Note: This requires destroying and recreating the window
        as transparency cannot be changed after creation
        """
        if self.window:
            position = self.get_position()
            self.window_closed.set()  # Set close flag before destroying       
            self.window.destroy()            
            self.transparent = not self.transparent
            self.position = position
            self.create_overlay_window()
            
        return self.transparent