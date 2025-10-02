import os

from PySide6.QtCore import Qt

from maya import cmds

from PIK_maya_anim_sequencer.ui.windows import DockableMainWindow, get_maya_main_window
from PIK_maya_anim_sequencer.scripts.cameras import create_preview_viewport


def run():
    folderpath = os.path.dirname(__file__)
    qml_url = os.path.join(folderpath, "sequencer.qml")
    width = 460
    height = 360

    dock_window_name = "sequencerWindow"

    if cmds.workspaceControl(dock_window_name + "WorkspaceControl", exists=True):
        cmds.deleteUI(dock_window_name + "WorkspaceControl", control=True)

    dock_window = DockableMainWindow(
        qml_url=qml_url, width=width, height=height, parent=get_maya_main_window()
    )
    dock_window.setObjectName(dock_window_name)
    dock_window.setWindowTitle("PIK_maya_anim_sequencer")
    dock_window.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
    dock_window.show(dockable=True, floating=True)
    create_preview_viewport()
    # TODO: Dock the sequencer ui to the preview viewport
    # For now, this command raises an error :
    # 'sequencerWindowWorkspaceControl is not unique'
    # cmds.workspaceControl(dock_window_name+"WorkspaceControl", dockToControl = [preview_viewport, "top"])

    return dock_window
