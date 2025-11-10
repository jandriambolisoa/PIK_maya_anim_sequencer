import os
import json

from maya import cmds
from maya import OpenMaya
from maya.plugin.timeSliderBookmark import timeSliderBookmark

from PIK_maya_anim_sequencer.scripts.cameras import SequencerCamera
from PIK_maya_anim_sequencer.scripts.dependencies import valid_shot_name

from quickBlast.settings import get_quickblast_folderpath
from quickBlast.main import run as quickBlast


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
        shot_name = valid_shot_name(shot_name)

        if self.get(f"bookmark_{shot_name}"):
            raise RuntimeError(f"Shot {shot_name} already exists.")

        cmds.rename(self.cam.transform, shot_name)  # camera
        cmds.rename(self.node, "bookmark_" + shot_name)  # bookmark

        self.name = shot_name
        self.cam = SequencerCamera.get(self.name)

    def delete(self):
        cmds.delete(self.cam.transform)  # camera
        cmds.delete(self.node)  # bookmark

    def move(self, offset: int, move_bookmark: bool = True, move_camera: bool = True):
        """Move the shot in time. Use move_bookmark or move_camera args
        to independetly move the bookmark or the camera.

        Args:
            offset (int): The number of frame it has to move.
            move_bookmark (bool, optional): Move the bookmark. Defaults to True.
            move_camera (bool, optional): Move the camera. Defaults to True.
        """
        if move_bookmark:
            cmds.setAttr(f"{self.node}.timeRangeStart", self.start + offset)
            cmds.setAttr(f"{self.node}.timeRangeStop", self.stop + offset)

        self.start = cmds.getAttr(f"{self.node}.timeRangeStart")
        self.stop = cmds.getAttr(f"{self.node}.timeRangeStop")

        if move_camera:
            self.cam.move(offset)

    def offset_end_frame(self, offset: int):
        """Offset the stop frame of the bookmark.

        Args:
            offset (int): The amount of offset.
        """
        cmds.setAttr(f"{self.node}.timeRangeStop", self.stop + offset)
        self.stop = cmds.getAttr(f"{self.node}.timeRangeStop")

    def focus(self):
        """Update Maya playback range to frame this shot."""
        cmds.playbackOptions(edit=True, min=self.start, max=self.stop)

    def export_playblast(self, show_output=False, show_popup_errors=False):
        """Export Maya playblast."""
        orig_min_time_slider = cmds.playbackOptions(query=True, min=True)
        orig_max_time_slider = cmds.playbackOptions(query=True, max=True)

        folder_path = get_quickblast_folderpath()
        self.focus()
        self.cam.set_attr("displayResolution", 0)
        cmds.file(modified=False)
        quickBlast(
            show_output=show_output,
            custom_filepath=os.path.join(folder_path, f"{self.name}.mp4"),
            show_popup_errors=show_popup_errors,
        )
        self.cam.set_attr("displayResolution", 1)

        cmds.playbackOptions(
            edit=True, min=orig_min_time_slider, max=orig_max_time_slider
        )

    def export_camera(self, folder_path: str, show_output=False):
        """Export this shot camera as a maya ASCII file."""
        cmds.select(self.cam.transform, replace=True)
        cmds.file(
            os.path.join(folder_path, self.name + ".ma"),
            exportSelected=True,
            type="mayaAscii",
            force=True,
        )
        if show_output:
            os.startfile(folder_path)

    def as_dict(self):
        """
        Convert the shot into a dictionary.
        dict structure:
        {
            "name": "SQ0020_SH0010",
            "sequence": "SQ0020",
            "shot": SH0010,
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
