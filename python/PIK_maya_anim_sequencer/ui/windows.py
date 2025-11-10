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
    def __init__(self):
        super().__init__()
        self.dialog_create_shot = None

    @Slot(str, result=str)
    def get_camera_name(self, shot_name):
        return shot_name

    @Slot(result=str)
    def get_shot_name(self):
        sequencer_sequence = get_sequencer_sequence()
        return sequencer_sequence.generate_shot_name()

    @Slot(str, str, int, str)
    def do_create_shot(self, shot_name, color, shot_length, shot_camera):
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
        sequencer_sequence = get_sequencer_sequence()
        current_time = cmds.currentTime(query=True)
        sequencer_sequence.delete_shot_at_time(current_time)

    @Slot()
    def focus_active_shot(self):
        sequencer_sequence = get_sequencer_sequence()
        current_time = cmds.currentTime(query=True)
        active_shot = sequencer_sequence.get_shots_at_time(current_time)[0]
        if active_shot:
            active_shot.focus()

    @Slot()
    def defocus_active_shot(self):
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
        sequencer_sequence = get_sequencer_sequence()
        current_time = cmds.currentTime(query=True)
        sequencer_sequence.focus_previous_at_time(current_time)

    @Slot()
    def focus_next_shot(self):
        sequencer_sequence = get_sequencer_sequence()
        current_time = cmds.currentTime(query=True)
        sequencer_sequence.focus_next_at_time(current_time)

    @Slot()
    def reduce_active_shot_length(self):
        sequencer_sequence = get_sequencer_sequence()
        current_time = cmds.currentTime(query=True)
        sequencer_sequence.offset_frame_of_shot_at_time(current_time, -1)

    @Slot()
    def increase_active_shot_length(self):
        sequencer_sequence = get_sequencer_sequence()
        current_time = cmds.currentTime(query=True)
        sequencer_sequence.offset_frame_of_shot_at_time(current_time, 1)

    @Slot()
    def link_shots(self):
        sequencer_sequence = get_sequencer_sequence()
        sequencer_sequence.resolve_gaps_between_shots()

    @Slot()
    def unstack_shots(self):
        sequencer_sequence = get_sequencer_sequence()
        sequencer_sequence.resolve_overlapping_shots()

    @Slot()
    def playblast(self):
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

        confirmation = cmds.confirmDialog(
            title="Confirm",
            message="Do you want to export the current sequence datas ?\nThis will export a datas.json file and a .ma file for each camera.",
            button=["Yes", "No"],
            defaultButton="No",
            cancelButton="No",
            dismissString="No",
        )
        if confirmation == "No":
            return

        folder_path = cmds.fileDialog2(fileMode=2, dialogStyle=1, hideNameEdit=True)

        if folder_path:
            folder_path = folder_path[0]

            datas = list()
            for shot in sequencer_sequence.shots:
                datas.append(shot.as_dict())
                shot.export_camera(folder_path)

            with open(os.path.join(folder_path, "datas.json"), "w") as file:
                json.dump(datas, file, indent=4)

        os.startfile(folder_path)

    @Slot()
    def open_create_shot_dialog(self):
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
        if self.dialog_create_shot:
            self.dialog_create_shot.close()


backend = Backend()


class DockableMainWindow(MayaQWidgetDockableMixin, QMainWindow):
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


def get_maya_main_window():
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QWidget)
