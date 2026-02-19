import os
import json

from maya import cmds
from maya import OpenMaya
from maya.plugin.timeSliderBookmark import timeSliderBookmark

from PIK_maya_anim_sequencer.scripts.cameras import SequencerCamera
from PIK_maya_anim_sequencer.scripts.constants import (
    EXPORT_OVERSCAN,
    DEFAULT_OVERSCAN,
    SHOT_TASK_TEMPLATE,
)
from PIK_maya_anim_sequencer.scripts.dependencies import valid_shot_name

# from quickBlast.settings import get_quickblast_folderpath
# from quickBlast.main import run as quickBlast


class SequencerShot:
    """
    Shot object in the sequencer tool.
    A shot consists of a bookmark and a camera.
    """

    def __init__(self, node: str):
        self.node = node
        self.name = node.removeprefix("bookmark_")
        self.cam = SequencerCamera.get(self.name)
        self.start = cmds.getAttr(f"{self.node}.timeRangeStart")
        self.stop = cmds.getAttr(f"{self.node}.timeRangeStop")
        self.color = cmds.getAttr(f"{self.node}.color")[-1]

    @classmethod
    def get(cls, node: str):
        """
        Get a Sequencer Shot object from a shot name or a bookmark name.
        Args:
            node (str): The shot name or bookmark name

        Returns:
            :class:`SequencerShot`: A class instance.
        """
        if node in cmds.ls(exactType="timeSliderBookmark"):
            return cls(node)
        elif node in [
            bookmark.removeprefix("bookmark_")
            for bookmark in cmds.ls(exactType="timeSliderBookmark")
        ]:
            return cls("bookmark_" + node)
        else:
            return None

    @classmethod
    def create(cls, shot_name: str, color: tuple, shot_length: int):
        """
        Create a Sequencer Shot object.
        Args:
            shot_name (str): The name of the shot.
            color (tuple): The color of the shot.
            shot_length (int): The length of the shot.

        Returns:
            :class:`SequencerShot`: A class instance.
        """
        shot_name = valid_shot_name(shot_name)

        if cls.get(f"bookmark_{shot_name}"):
            raise RuntimeError(f"Shot {shot_name} already exists.")

        start = int(cmds.currentTime(query=True))
        stop = start + shot_length

        node = timeSliderBookmark.createBookmark(
            name=shot_name, start=start, stop=stop, color=color
        )
        node = cmds.rename(node, f"bookmark_{shot_name}")

        return cls(node)

    def rename(self, shot_name: str):
        """
        Rename the shot.
        Args:
            shot_name: The new name of the shot.

        Returns:
            None
        """
        shot_name = valid_shot_name(shot_name)

        if self.get(f"bookmark_{shot_name}"):
            raise RuntimeError(f"Shot {shot_name} already exists.")

        cmds.rename(self.cam.transform, shot_name)  # camera
        cmds.rename(self.node, "bookmark_" + shot_name)  # bookmark

        self.name = shot_name
        self.cam = SequencerCamera.get(self.name)

    def delete(self):
        """
        Delete the shot.

        Returns:
            None
        """
        cmds.delete(self.cam.transform)  # camera
        cmds.delete(self.node)  # bookmark

    def move(self, offset: int, move_bookmark: bool = True, move_camera: bool = True):
        """
        Move the shot in time. Use move_bookmark or move_camera args
        to independently move the bookmark or the camera.
        Args:
            offset (int): The number of frame it has to move.
            move_bookmark (bool, optional): Move the bookmark. Defaults to True.
            move_camera (bool, optional): Move the camera. Defaults to True.

        Returns:
            None
        """
        if move_bookmark:
            cmds.setAttr(f"{self.node}.timeRangeStart", self.start + offset)
            cmds.setAttr(f"{self.node}.timeRangeStop", self.stop + offset)

        self.start = cmds.getAttr(f"{self.node}.timeRangeStart")
        self.stop = cmds.getAttr(f"{self.node}.timeRangeStop")

        if move_camera:
            self.cam.move(offset)

    def offset_end_frame(self, offset: int):
        """
        Offset the stop frame of the bookmark.
        Args:
            offset (int): The amount of offset.

        Returns:
            None
        """
        cmds.setAttr(f"{self.node}.timeRangeStop", self.stop + offset)
        self.stop = cmds.getAttr(f"{self.node}.timeRangeStop")

    def focus(self):
        """
        Update Maya playback range to frame this shot.

        Returns:
            None
        """
        cmds.playbackOptions(edit=True, min=self.start, max=self.stop)

    def export_playblast(self, show_output=False, show_popup_errors=False):
        """
        Export a playblast of this shot.
        Args:
            show_output (bool): If true, show the output folder of the playblast.
            show_popup_errors (bool): If true, show popup error message if any.

        Returns:
            None
        """
        # This revision excludes quickBlast, so we fall back to the default playblast dialog
        OpenMaya.MGlobal.displayWarning("No quickBlast : a default playblast is run.")
        cmds.playblast(options=True)

        # orig_min_time_slider = cmds.playbackOptions(query=True, min=True)
        # orig_max_time_slider = cmds.playbackOptions(query=True, max=True)
        #
        # folder_path = get_quickblast_folderpath()
        # self.focus()
        # self.cam.set_attr("overscan", EXPORT_OVERSCAN)
        # self.cam.set_attr("displayResolution", 0)
        # cmds.file(modified=False)
        # quickBlast(
        #     show_output=show_output,
        #     custom_filepath=os.path.join(folder_path, f"{self.name}.mp4"),
        #     show_popup_errors=show_popup_errors,
        # )
        #
        # # Ignore reset
        # self.cam.set_attr("overscan", DEFAULT_OVERSCAN)
        # self.cam.set_attr("displayResolution", 1)
        #
        # cmds.playbackOptions(
        #     edit=True, min=orig_min_time_slider, max=orig_max_time_slider
        # )

    def export_camera(self, folder_path: str, show_output=False):
        """
        Export this shot camera as a maya ASCII file.
        Args:
            folder_path (str): The folder path of the export.
            show_output (bool): If true, show the output folder.

        Returns:
            None
        """
        # Conform camera
        cmds.select(self.cam.transform, replace=True)
        self.cam.set_attr("overscan", EXPORT_OVERSCAN)

        # Offset keyframes to have the animation starting at 1001
        shot_length = self.stop - self.start
        cmds.keyframe(self.cam.transform, relative=True, timeChange=-shot_length+1001)
        cmds.keyframe(self.cam.shape, relative=True, timeChange=-shot_length+1001)

        # Export
        cmds.file(
            os.path.join(folder_path, self.name + ".ma"),
            exportSelected=True,
            type="mayaAscii",
            force=True,
        )
        # Offset keyframes back
        cmds.keyframe(self.cam.transform, relative=True, timeChange=shot_length-1001)
        cmds.keyframe(self.cam.shape, relative=True, timeChange=shot_length-1001)

        self.cam.set_attr("overscan", DEFAULT_OVERSCAN)
        if show_output:
            os.startfile(folder_path)

    def as_dict(self):
        """
        Convert the shot into a dictionary.
        dict structure:
        {
            "name": "SQ0020_SH0010",
            "sequence": "SQ0020",
            "shot": "SH0010",
            "length": 24,
            "start": 1001,
            "stop": 1025,
            "color": [
                0.9607843160629272,
                0.48627451062202454,
                0.0
            ]
        }

        Returns:
            A dictionary.
        """
        sequence, shot = self.name.split("_")
        length = self.stop - self.start
        return {
            "name": self.name,
            "sequence": sequence,
            "shot": shot,
            "length": length,
            "start": self.start,
            "stop": self.stop,
            "color": self.color,
        }

    def as_csv(
        self,
        status: str = "wtg",
        start_frame: int = 1001,
        task_template: str = SHOT_TASK_TEMPLATE,
    ):
        """
        Convert the shot into a CSV line for Shotgrid imports.
        Format of the line will be : Sequence;Shot Code;Status;Cut In;Cut Out;Cut Duration;Task Template
        Returns:
            str: A CSV line of the shot.
        """
        sequence, shot = self.name.split("_")
        shot_length = int(self.stop - self.start)
        return ";".join(
            [
                sequence,
                self.name,
                status,
                str(start_frame),
                str(start_frame + shot_length),
                str(shot_length),
                task_template,
            ]
        )
