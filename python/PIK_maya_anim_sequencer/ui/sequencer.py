import os

from PySide6.QtCore import Qt

from maya import cmds

from PIK_maya_anim_sequencer.ui.windows import DockableMainWindow, get_maya_main_window
from PIK_maya_anim_sequencer.scripts.cameras import SequencerCamera
from PIK_maya_anim_sequencer.scripts.constants import PREVIEW_CAMERA_NAME

# from quickBlast.main import run as quickBlast


def run():
    """
    Run the sequencer UI.
    Returns:
        None
    """
    folderpath = os.path.dirname(__file__)
    qml_url = os.path.join(folderpath, "sequencer.qml")
    width = 594
    height = 135

    dock_window_name = "sequencerWindow"

    if cmds.workspaceControl(dock_window_name + "WorkspaceControl", exists=True):
        cmds.deleteUI(dock_window_name + "WorkspaceControl")

    dock_window = DockableMainWindow(
        qml_url=qml_url, width=width, height=height, parent=get_maya_main_window()
    )
    dock_window.setObjectName(dock_window_name)
    dock_window.setWindowTitle("PIK_maya_anim_sequencer")
    dock_window.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
    dock_window.show(dockable=True, floating=True)

    return dock_window_name + "WorkspaceControl"
