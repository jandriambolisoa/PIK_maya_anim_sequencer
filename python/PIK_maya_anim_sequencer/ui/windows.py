import os

from maya import OpenMayaUI
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from PySide6.QtCore import QUrl, QObject, Slot, Qt
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import QWidget, QMainWindow

from PySide6.QtGui import QColor

from shiboken6 import wrapInstance

from PIK_maya_anim_sequencer.scripts.shots import (
    focus_next,
    focus_previous,
    offset_frame_of_active_shot,
    resolve_gaps_between_shots,
    resolve_overlapping_shots,
    delete_active_shot,
    create_shot,
    generate_shot_name,
    defocus,
    get_active_shot,
    export_shots,
    extra_defocus,
    is_active_shot_focus,
    is_sequence_focus,
    is_sequence_fully_defocus,
)
from PIK_maya_anim_sequencer.scripts.cameras import (
    create_sequencer_camera,
    generate_camera_name,
)
from quickBlast.main import run as quickBlast


class Backend(QObject):
    def __init__(self):
        super().__init__()

    @Slot(str, result=str)
    def get_camera_name(self, shot_name):
        return generate_camera_name(shot_name)

    @Slot(result=str)
    def get_shot_name(self):
        return generate_shot_name()

    @Slot(str, str, int, str)
    def do_create_shot(self, shot_name, color, shot_length, shot_camera):
        create_shot(shot_name, QColor(color).getRgbF(), shot_length, shot_camera)
        create_sequencer_camera(shot_camera)

    @Slot()
    def delete_shot(self):
        delete_active_shot()

    @Slot()
    def focus_active_shot(self):
        active_shot = get_active_shot()
        if active_shot:
            active_shot.focus()

    @Slot()
    def defocus_active_shot(self):
        if is_sequence_focus() or is_active_shot_focus() or is_sequence_fully_defocus():
            extra_defocus()
        else:
            defocus()

    @Slot()
    def focus_previous_shot(self):
        focus_previous()

    @Slot()
    def focus_next_shot(self):
        focus_next()

    @Slot()
    def reduce_active_shot_length(self):
        offset_frame_of_active_shot(-1)

    @Slot()
    def increase_active_shot_length(self):
        offset_frame_of_active_shot(1)

    @Slot()
    def link_shots(self):
        resolve_gaps_between_shots()

    @Slot()
    def unstack_shots(self):
        resolve_overlapping_shots()

    @Slot()
    def playblast(self):
        quickBlast()

    @Slot()
    def export_sequence_datas(self):
        export_shots()


backend = Backend()


class DockableMainWindow(MayaQWidgetDockableMixin, QMainWindow):
    def __init__(self, qml_url: str, width: int, height: int, *args, **kwargs):
        super(DockableMainWindow, self).__init__(*args, **kwargs)

        widget = QQuickWidget()
        widget.setSource(QUrl.fromLocalFile(qml_url))
        widget.engine().rootContext().setContextProperty("backend", backend)
        widget.engine().addImportPath(
            os.path.join(os.path.dirname(__file__), "widgets")
        )
        widget.resize(width, height)
        widget.setResizeMode(QQuickWidget.SizeRootObjectToView)

        self.setMinimumSize(width, height)
        self.setFocusPolicy(Qt.NoFocus)
        self.setCentralWidget(widget)


def get_maya_main_window():
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QWidget)
