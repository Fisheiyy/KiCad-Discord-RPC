import os
import time
from threading import Thread, Event
from pypresence import Presence
import pcbnew # type: ignore
import wx # type: ignore

# Set your Discord Application Client ID here
CLIENT_ID = '1249186546196807731'

# Initialize the Discord Rich Presence client
rpc = Presence(CLIENT_ID)
rpc.connect()

class RPC():
    def __init__(self):
        self.board = pcbnew.GetBoard()
        self.start_time = time.time()
        self.running = False
        self.thread = None
        self.stop_event = Event()

    def update_presence(self):
        while True and not self.stop_event.is_set():
            # Fetch details about the current KiCad project
            board = self.board
            if board is not None:
                project_name = os.path.basename(board.GetFileName())
                footprint_count = len(board.GetFootprints())
                net_count = board.GetNetCount()
                track_count = len(board.GetTracks())
                #layer_count = board.GetCopperLayerCount()

                board_size = board.GetBoardEdgesBoundingBox()
                board_width = board_size.GetWidth() / 1000000.0  # convert from nanometers to millimeters
                board_height = board_size.GetHeight() / 1000000.0  # convert from nanometers to millimeters

                selected_footprint_refs = []
                for footprint in board.GetFootprints():  # Iterate over all footprints on the board
                    if footprint.IsSelected():
                        selected_footprint_refs.append(footprint.GetReference())
                
                if len(selected_footprint_refs) > 0:
                    details = (f"Editing Footprint(s) '{', '.join(selected_footprint_refs)}', "
                                f"{track_count} Tracks, "
                                f"{net_count} Nets")
                else:
                    details = (f"{footprint_count} Footprints, "
                            f"{net_count} Nets, "
                            f"{track_count} Tracks, "
                            f"PCB Size: {board_width:.2f}x{board_height:.2f}mm")
                
                # Update Rich Presence
                rpc.update(
                    state=f"Editing {project_name} in {os.path.basename(os.path.dirname(board.GetFileName()))}",
                    details=details,
                    large_image="kicad_logo",
                    large_text=f"KiCad EDA v{pcbnew.GetBuildVersion()}",
                    start=self.start_time
                )
            else:
                rpc.clear()

            time.sleep(15)

    def start_presence(self):
        if not self.running:
            if pcbnew.GetBoard() is not None:
                try:
                    self.running = True
                    self.stop_event.clear()
                    self.thread = Thread(target=self.update_presence)
                    self.thread.start()
                    wx.MessageBox("Discord Rich Presence is now running in the background", "Discord Rich Presence", wx.OK | wx.ICON_INFORMATION)
                except Exception as e:
                    import logging
                    logger = logging.getLogger()
                    logger.debug(repr(e))
            else:
                wx.MessageBox("No pcbnew board is currently loaded", "Discord Rich Presence", wx.OK | wx.ICON_ERROR)
                
            
    def stop_presence(self):
        if self.running:
            self.running = False
            self.stop_event.set()
            self.thread.join()
            rpc.clear()
            wx.MessageBox("Discord Rich Presence has been stopped", "Discord Rich Presence", wx.OK | wx.ICON_INFORMATION)
    
    def toggle_presence(self):
        if self.running:
            self.stop_presence()
        else:
            self.start_presence()
    
class Plugin(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Discord Rich Presence"
        self.category = "Custom Tools"
        self.description = "Update Discord Rich Presence with current KiCad project details"
        self.pcbnew_icon_support = hasattr(self, "show_toolbar_button")
        self.show_toolbar_button = True  # This ensures the button appears in the toolbar
        self.icon_file_name = os.path.join(os.path.dirname(__file__), './icon.png')

    def Run(self):
        RPC().toggle_presence()
