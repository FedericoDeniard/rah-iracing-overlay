import webview

class OverlayWindow:
    def __init__(self, url, width, height):
        self.url = url
        self.window = None
        self.width = width
        self.height = height

    def create_overlay_window(self):
        self.window = webview.create_window(
            "iRacing Overlay",
            url=self.url,
            width=self.width,
            height=self.height,
            frameless=True,  
            transparent=False,  
            on_top=True,  
            easy_drag=True, 
            draggable=True
        )
        webview.start()