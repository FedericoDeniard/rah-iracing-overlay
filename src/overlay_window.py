import webview

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
        self.window = webview.create_window(
            "iRacing Overlay",
            url=self.url,
            width=self.width,
            height=self.height,
            frameless=self.frameless,  
            transparent=False,  
            on_top=True,  
            easy_drag=True, 
            draggable=True
        )
        
        # Register window closed event handler
        if self.on_closed:
            self.window.events.closed += self.on_closed_handler
        
        webview.start()
    
    def on_closed_handler(self):
        """
        Handler called when the window is closed
        """
        if self.on_closed:
            self.on_closed()