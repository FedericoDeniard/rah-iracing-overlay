import webview
import sys

class OverlayWindow:
    def __init__(self, url, width, height, frameless=True):
        self.url = url
        self.window = None
        self.width = width
        self.height = height
        self.frameless = frameless
        self.on_closed = None

    def set_on_closed(self, callback):
        """
        Set the callback function to be called when the window is closed
        """
        self.on_closed = callback

    def create_overlay_window(self):
        # Default window arguments
        window_args = {
            "title": "iRacing Overlay",
            "url": self.url,
            "width": self.width,
            "height": self.height,
            "frameless": self.frameless,
            "transparent": False,  # Keep this false so we can interact with the window
            "on_top": True,
            "easy_drag": True,
            "draggable": True,
            "min_size": (200, 100),
            "background_color": "#000000",  # Black as fallback
            "text_select": False  # Disable text selection
        }
        
        try:
            # Create the window with our settings
            self.window = webview.create_window(**window_args)
            
            # Register window closed event handler
            if self.on_closed:
                self.window.events.closed += self.on_closed_handler
            
            # Start the webview
            webview.start()
        except Exception as e:
            print(f"Error creating overlay window: {e}")
    
    def on_closed_handler(self):
        """
        Handler called when the window is closed
        """
        if self.on_closed:
            self.on_closed()