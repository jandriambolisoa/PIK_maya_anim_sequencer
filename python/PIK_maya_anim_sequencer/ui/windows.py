import json
import os

from maya import cmds
from maya import OpenMayaUI, OpenMaya
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from PySide6.QtCore import QUrl, QObject, Slot, Qt
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtQuick import QQuickItem
from PySide6.QtWidgets import QWidget, QMainWindow, QDialog, QGridLayout

from PySide6.QtGui import QColor

from shiboken6 import wrapInstance

from PIK_maya_anim_sequencer.scripts.shots import SequencerShot
from PIK_maya_anim_sequencer.scripts.cameras import SequencerCamera
from PIK_maya_anim_sequencer.scripts.sequence import get_sequencer_sequence
from quickBlast.settings import get_quickblast_folderpath
from quickBlast.main import run as quickBlast


class Backend(QObject):
    """
    The backend object used in the QQuickWidget.
    """

    def __init__(self):
        super().__init__()
        self.dialog_create_shot = None

    @Slot(str, result=str)
    def get_camera_name(self, shot_name):
        """
        Get the camera name for the given shot name.
        Args:
            shot_name (str): The shot name.

        Returns:
            str: The camera name.
        """
        return shot_name

    @Slot(result=str)
    def get_shot_name(self):
        """
        Get the shot name.
        Returns:
            (str): The shot name.
        """
        sequencer_sequence = get_sequencer_sequence()
        return sequencer_sequence.generate_shot_name()

    @Slot(str, str, int, str)
    def do_create_shot(self, shot_name, color, shot_length, shot_camera):
        """
        Create a shot at current time.
        Args:
            shot_name (str): The shot name.
            color (str): The color of the shot as hex color code.
            shot_length (int): The length of the shot.
            shot_camera (str): The camera transform name of the shot.

        Returns:
            None
        """
        sequencer_sequence = get_sequencer_sequence()
        shot = SequencerShot.create(shot_name, QColor(color).getRgbF(), shot_length)
        shot.cam = SequencerCamera.create(shot_camera)
        shot.cam.snap_to_another_camera()
        sequencer_sequence.shots.append(shot)
        sequencer_sequence.shots = [
            shot
            for shot in sorted(sequencer_sequence.shots, key=lambda item: item.start)
        ]

    @Slot()
    def delete_shot(self):
        """
        Delete the shot at current time.
        Returns:
            None
        """
        sequencer_sequence = get_sequencer_sequence()
        current_time = cmds.currentTime(query=True)
        shot = sequencer_sequence.get_shots_at_time(current_time)[0]
        if not shot:
            OpenMaya.MGlobal.displayWarning("Sequencer: No active shot detected.")
            return

        if show_confirmation_dialog(
            f"Do you want to delete current shot?\n{shot.name}"
        ):
            sequencer_sequence.delete_shot_at_time(current_time)

    @Slot()
    def focus_active_shot(self):
        """
        Focus the active shot.
        Returns:
            None
        """
        sequencer_sequence = get_sequencer_sequence()
        current_time = cmds.currentTime(query=True)
        active_shot = sequencer_sequence.get_shots_at_time(current_time)[0]
        if active_shot:
            active_shot.focus()

    @Slot()
    def defocus_active_shot(self):
        """
        Defocus the shot or expand the playback range.
        Returns:
            None
        """
        sequencer_sequence = get_sequencer_sequence()
        current_time = cmds.currentTime(query=True)
        if (
            sequencer_sequence.is_sequence_focus()
            or sequencer_sequence.is_shot_focus_at_time(current_time)
            or sequencer_sequence.is_sequence_fully_defocus()
        ):
            sequencer_sequence.extra_defocus()
        else:
            sequencer_sequence.defocus()

    @Slot()
    def focus_previous_shot(self):
        """
        Focus the previous shot.
        Returns:
            None
        """
        sequencer_sequence = get_sequencer_sequence()
        current_time = cmds.currentTime(query=True)
        sequencer_sequence.focus_previous_at_time(current_time)

    @Slot()
    def focus_next_shot(self):
        """
        Focus the next shot.
        Returns:
            None
        """
        sequencer_sequence = get_sequencer_sequence()
        current_time = cmds.currentTime(query=True)
        sequencer_sequence.focus_next_at_time(current_time)

    @Slot()
    def reduce_active_shot_length(self):
        """
        Reduce active shot length by 1 time unit.
        Returns:
            None
        """
        sequencer_sequence = get_sequencer_sequence()
        current_time = cmds.currentTime(query=True)
        sequencer_sequence.offset_frame_of_shot_at_time(current_time, -1)

    @Slot()
    def increase_active_shot_length(self):
        """
        Increase active shot length by 1 time unit.
        Returns:
            None
        """
        sequencer_sequence = get_sequencer_sequence()
        current_time = cmds.currentTime(query=True)
        sequencer_sequence.offset_frame_of_shot_at_time(current_time, 1)

    @Slot()
    def link_shots(self):
        """
        Resolve gaps between shots.
        Returns:
            None
        """
        sequencer_sequence = get_sequencer_sequence()
        sequencer_sequence.resolve_gaps_between_shots()

    @Slot()
    def unstack_shots(self):
        """
        Resolve overlapping shots.
        Returns:
            None
        """
        sequencer_sequence = get_sequencer_sequence()
        sequencer_sequence.resolve_overlapping_shots()

    @Slot()
    def playblast(self):
        """
        Launch a playblast for each shot.
        Returns:
            None
        """
        sequencer_sequence = get_sequencer_sequence()

        if cmds.file(query=True, modified=True):
            OpenMaya.MGlobal.displayError("Save your file before running playblasts.")
            return

        # Playblast shots individually with quickBlast
        folder_path = get_quickblast_folderpath()
        first_shot = True

        # Clear selection and set the preview viewport as active
        cmds.select(clear=True)
        cmds.modelEditor(
            sequencer_sequence.preview_viewport, edit=True, activeView=True
        )

        # Get orig components visibility before hiding them
        joints_vis = cmds.modelEditor(
            sequencer_sequence.preview_viewport, query=True, joints=True
        )
        locators_vis = cmds.modelEditor(
            sequencer_sequence.preview_viewport, query=True, locators=True
        )
        curves_vis = cmds.modelEditor(
            sequencer_sequence.preview_viewport, query=True, nurbsCurves=True
        )
        cmds.modelEditor(sequencer_sequence.preview_viewport, edit=True, joints=False)
        cmds.modelEditor(sequencer_sequence.preview_viewport, edit=True, locators=False)
        cmds.modelEditor(
            sequencer_sequence.preview_viewport, edit=True, nurbsCurves=False
        )

        for shot in sequencer_sequence.shots:
            shot.export_playblast()

        # Set back orig components visibility
        cmds.modelEditor(
            sequencer_sequence.preview_viewport, edit=True, joints=joints_vis
        )
        cmds.modelEditor(
            sequencer_sequence.preview_viewport, edit=True, locators=locators_vis
        )
        cmds.modelEditor(
            sequencer_sequence.preview_viewport, edit=True, nurbsCurves=curves_vis
        )

        os.startfile(folder_path)

    @Slot()
    def export_sequence_datas(self):
        """
        For each shot of this sequence, export the camera and a datas.json file containing shots infos.
        Returns:
            None
        """
        sequencer_sequence = get_sequencer_sequence()

        if show_confirmation_dialog(
            "Do you want to export the current sequence datas ?\nThis will export a shots.csv file for shotgrid imports and a .ma file for each camera."
        ):
            folder_path = cmds.fileDialog2(fileMode=2, dialogStyle=1, hideNameEdit=True)

            if folder_path:
                folder_path = folder_path[0]

                datas = list()
                for shot in sequencer_sequence.shots:
                    datas.append(shot.as_csv())
                    shot.export_camera(folder_path)

                with open(os.path.join(folder_path, "datas.csv"), "w") as file:
                    file.write(
                        "Sequence;Shot Code;Status;Cut In;Cut Out;Cut Duration;Task Template\n"
                    )
                    file.write("\n".join(datas))

            os.startfile(folder_path)

    @Slot()
    def open_create_shot_dialog(self):
        """
        Show a modal dialog to create a new shot.
        Returns:
            None
        """
        folderpath = os.path.dirname(__file__)
        qml_url = os.path.join(folderpath, "dialog_createShot.qml")

        width = 360
        height = 280

        dialog = DialogCreateShotWindow(
            qml_url=qml_url, width=width, height=height, parent=get_maya_main_window()
        )
        dialog.setObjectName("sequencerCreateShotDialog")
        dialog.setWindowTitle("Create Shot")
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        dialog.show()

        self.dialog_create_shot = dialog

    @Slot()
    def close_create_shot_dialog(self):
        """
        Close the create shot dialog window.
        Returns:
            None
        """
        if self.dialog_create_shot:
            self.dialog_create_shot.close()


backend = Backend()


class DockableMainWindow(MayaQWidgetDockableMixin, QMainWindow):
    """
    The Sequencer main window object.
    """

    def __init__(self, qml_url: str, width: int, height: int, *args, **kwargs):
        super(DockableMainWindow, self).__init__(*args, **kwargs)

        widget = QQuickWidget()
        widget.setSource(QUrl.fromLocalFile(qml_url))
        widget.engine().rootContext().setContextProperty("backend", backend)
        widget.resize(width, height)
        widget.setResizeMode(QQuickWidget.SizeRootObjectToView)

        self.setMinimumSize(width, height)
        self.setFocusPolicy(Qt.NoFocus)
        self.setCentralWidget(widget)


class DialogCreateShotWindow(QDialog):
    """
    The create shot dialog window object.
    """

    def __init__(self, qml_url: str, width: int, height: int, *args, **kwargs):
        super(DialogCreateShotWindow, self).__init__(*args, **kwargs)

        widget = QQuickWidget()
        widget.setSource(QUrl.fromLocalFile(qml_url))
        widget.engine().rootContext().setContextProperty("backend", backend)
        widget.resize(width, height)
        widget.setResizeMode(QQuickWidget.SizeRootObjectToView)

        layout = QGridLayout(parent=self)

        self.setLayout(layout)
        self.layout().addWidget(widget)
        self.setMinimumSize(width, height)

        self.setModal(True)


def show_confirmation_dialog(text) -> bool:
    """
    Show a confirmation dialog. Return True if the dialog was successful.
    Args:
        text (str): The message to display.

    Returns:
        bool: True if user confirmed successfully.
    """
    confirmation = cmds.confirmDialog(
        title="Confirm",
        message=text,
        button=["Yes", "No"],
        defaultButton="No",
        cancelButton="No",
        dismissString="No",
    )
    if confirmation == "Yes":
        return True
    else:
        return False


def create_viewport(label: str, viewport_size: tuple):
    """
    Create a floating viewport and return the model panel name.
    Args:
        label (str): The label of the viewport.
        viewport_size (tuple): The size of the viewport.

    Returns:
        str: The name of the panel containing the viewport.
    """
    dock_name = "PIK_" + label.title().replace(" ", "") + "Dock"

    if cmds.workspaceControl(dock_name + "WorkspaceControl", exists=True):
        cmds.workspaceControl(dock_name + "WorkspaceControl", edit=True, close=True)

    workspace = cmds.workspaceControl(
        dock_name + "WorkspaceControl",
        label=label,
        floating=True,
        initialWidth=viewport_size[0],
        initialHeight=viewport_size[1],
        retain=False,
    )

    cmds.setParent(workspace)

    cmds.paneLayout()
    panel = cmds.modelPanel()

    # Enable shading, manage visibilities
    cmds.modelEditor(
        panel,
        edit=True,
        displayAppearance="smoothShaded",
        wireframeOnShaded=False,
        grid=False,
        nurbsCurves=False,
        locators=False,
        cameras=False,
        joints=False,
        imagePlane=False,
        follicles=False,
        displayTextures=True,
    )

    return panel


def get_maya_main_window():
    """
    Get the maya main window object.
    Returns:
        :class: `QWidget`: The maya main window object.
    """
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QWidget)


def maya_dock_control_to_window(window: str, to_dock: str, position: str = "bottom"):
    """
    Dock a maya control to a maya window.
    Args:
        window (str): The name of the workspace control to dock to.
        to_dock (str): The name of the control to dock.
        position (str): The position of the control to dock (valid values are: "left", "right", "top", "bottom"). Defaults to bottom.

    Returns:
        None
    """
    try:
        control_to_dock = cmds.modelPanel(to_dock, query=True, control=True)
        if control_to_dock:
            control_to_dock = control_to_dock.split("|")[0]
            cmds.workspaceControl(
                window, edit=True, dockToControl=(control_to_dock, position)
            )
    except RuntimeError:
        # If the viewport is already docked, Maya will raise an error.
        pass
