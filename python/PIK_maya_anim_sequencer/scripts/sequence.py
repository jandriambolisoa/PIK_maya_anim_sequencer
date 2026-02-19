import os
import json

from maya import cmds
from maya import OpenMaya
from maya.plugin.timeSliderBookmark import timeSliderBookmark

from PIK_maya_anim_sequencer.scripts.shots import SequencerShot
from PIK_maya_anim_sequencer.scripts.cameras import SequencerCamera
from PIK_maya_anim_sequencer.scripts.constants import (
    PREVIEW_CAMERA_NAME,
    PREVIEW_VIEWPORT_SIZE,
)

from PIK_maya_anim_sequencer.scripts.dependencies import valid_sequence_name


class SequencerSequence:
    """
    Sequencer object in the sequencer tool.
    A sequence consists of a list of shots.
    """

    instance = None

    def __init__(self, name: str = "SQ0010"):
        self.name = name
        self.shots = list()
        self.preview_viewport = None
        self.auto_solo_cam = False

    @classmethod
    def load(cls):
        """
        Load the sequencer sequence from the opened scene.
        Returns:
            :class:`SequencerSequence`: A class instance.
        """
        seq = cls("SQ0010")

        # Get all existing shots in the scene
        for node in cmds.ls(exactType="timeSliderBookmark"):
            shot = SequencerShot.get(node)
            if not shot:
                continue
            seq.shots.append(shot)

        # Sort datas by chronological order
        seq.shots = [shot for shot in sorted(seq.shots, key=lambda item: item.start)]

        if seq.shots:
            seq.name, _ = seq.shots[0].name.split("_")

        return seq

    def sort_shots(self):
        """
        Sort the shots in the sequence.
        Returns:
            None
        """
        self.shots = [shot for shot in sorted(self.shots, key=lambda item: item.start)]

    def get_shots_at_time(self, time: int):
        """
        Get the shots at the given time.
        Args:
            time (int): The time to get the shots at.

        Returns:
            list[:class:`SequencerShot`]: Shots at the given time.
        """
        shot_list = list()
        for shot in self.shots:
            if shot.start <= time <= shot.stop:
                shot_list.append(shot)

        return shot_list

    def delete_shot_at_time(self, time: int):
        """
        Delete the shot at the given time.
        Args:
            time (int): The time to delete the shot at.

        Returns:
            None
        """
        active_shot = self.get_shots_at_time(time)[0]
        self.shots.remove(active_shot)
        active_shot.delete()
        del active_shot

    def get_previous_shots_at_time(self, time: int):
        """
        Get the shots before the given time.
        Args:
            time (int): The time to get the shots at.

        Returns:
            list[:class:`SequencerShot`]: Shots at the given time.
        """
        shot_list = list()
        for shot in self.shots:
            if shot.stop < time:
                shot_list.append(shot)

        return shot_list

    def get_next_shots_at_time(self, time: int):
        """
        Get the shots after the given time.
        Args:
            time (int): The time to get the shots at.

        Returns:
            list[:class:`SequencerShot`]: Shots at the given time.
        """
        shot_list = list()
        for shot in self.shots:
            if shot.start > time:
                shot_list.append(shot)

        return shot_list

    def rename(self, name: str) -> None:
        """
        Rename the given sequence and all its shots.
        Args:
            name (str): The name of the new sequence. Must be unique and in the format 'SQXXXX' where 'X' are digits.
        """
        name = valid_sequence_name(name)

        if name == self.name:
            return

        self.name = name

        for shot in self.shots:
            seq, sh = shot.name.split("_")
            shot.name = name + "_" + sh

    def update_range_of_shot_at_time(self, time: int) -> None:
        """
        Update the range of the shot at the given time.
        Args:
            time (int): The time to get the shots at.

        Returns:
            None
        """
        shots = self.get_shots_at_time(time)
        if shots:
            for shot in shots:
                shot.start = cmds.getAttr(f"{shot.node}.timeRangeStart")
                shot.stop = cmds.getAttr(f"{shot.node}.timeRangeStop")

        self.sort_shots()

    def update_range_of_shots(self):
        """
        Update the range of the shots.

        Returns:
            None
        """
        for shot in self.shots:
            shot.start = cmds.getAttr(f"{shot.node}.timeRangeStart")
            shot.stop = cmds.getAttr(f"{shot.node}.timeRangeStop")
        self.sort_shots()

    def solo_cameras_of_shots_at_time(self, time: int):
        """
        Hide the cameras (in the viewport) of the shots that are not at the given time.
        Args:
            time (int): The time to get the shots at.
        """
        for shot in self.shots:
            if not shot.start <= time <= shot.stop:
                shot.cam.hide()
            else:
                shot.cam.show()

    def show_all_cameras(self):
        """
        Show the cameras (in the viewport) of all shots.
        """
        for shot in self.shots:
            shot.cam.show()

    def set_auto_solo_camera(self, value: bool) -> None:
        """
        Set auto solo camera. This option indicates that the user would like to automatically hide other shots cameras.
        Args:
            value (bool): True or False
        """
        self.auto_solo_cam = value

    @staticmethod
    def defocus():
        """
        Reset the playback range to see all shots.

        Returns:
            None
        """
        timeSliderBookmark.frameAllBookmark()

    @staticmethod
    def extra_defocus(defocus_amount: int = 24):
        """
        Extend the playback range by defocus_amount frames.

        Args:
            defocus_amount (int, optional): The number of frame to add at each end of the playback range. Defaults to 24.
        """
        current_start = cmds.playbackOptions(query=True, minTime=True)
        current_stop = cmds.playbackOptions(query=True, maxTime=True)
        cmds.playbackOptions(minTime=int(current_start) - defocus_amount)
        cmds.playbackOptions(maxTime=int(current_stop) + defocus_amount)

    def is_sequence_focus(self) -> bool:
        """
        Return True if a sequence is actually in focus.
        A focus means that the start and the end of a shot
        (or all the shots for a sequence) match the
        current playback range min and max values.

        Returns:
            bool: is current Sequence focus.
        """
        current_start = cmds.playbackOptions(query=True, minTime=True)
        current_stop = cmds.playbackOptions(query=True, maxTime=True)
        if [self.shots[0].start, self.shots[-1].stop] == [current_start, current_stop]:
            return True

        return False

    def is_shot_focus_at_time(self, time: int) -> bool:
        """
        Return True if the shot at a given time is in focus.
        A focus means that the start and the end of a shot
        (or all the shots for a sequence) match the
        current playback range min and max values.
        Args:
            time (int): The time to get the shots at.

        Returns:
            bool: is shot at a given time focus.
        """
        current_start = cmds.playbackOptions(query=True, minTime=True)
        current_stop = cmds.playbackOptions(query=True, maxTime=True)
        active_shots = self.get_shots_at_time(time)
        for shot in active_shots:
            if [shot.start, shot.stop] == [current_start, current_stop]:
                return True

        return False

    def is_sequence_fully_defocus(self) -> bool:
        """
        Returns True if the playback range contains all
        shots and does not focus the sequence.
        A focus means that the start and the end of a shot
        (or all the shots for a sequence) match the
        current playback range min and max values.

        Returns:
            bool: is the playback range contains all shots and does not focus the sequence
        """
        current_start = cmds.playbackOptions(query=True, minTime=True)
        current_stop = cmds.playbackOptions(query=True, maxTime=True)

        if self.shots[0].start > current_start and self.shots[-1].stop < current_stop:
            return True

        return False

    def focus_next_at_time(self, time: int):
        """
        Focus the shot coming after the shot at a given time.
        Args:
            time (int): The time to get the shot at.

        Returns:
            None
        """
        # Maya default function comes back at the first bookmark when calling it while
        # being at the last bookmark, which might be confusing.
        # timeSliderBookmark.frameNextBookmarkAtCurrentTime()

        next_shots = self.get_next_shots_at_time(time)
        if next_shots:
            cmds.playbackOptions(minTime=next_shots[-1].start)
            cmds.playbackOptions(maxTime=next_shots[-1].stop)
            cmds.currentTime(next_shots[-1].start)

    def focus_previous_at_time(self, time: int):
        """
        Focus the shot chronologically before the shot at a given time.
        Args:
            time (int): The time to get the shot at.

        Returns:
            None
        """
        # Maya default function seems to work 1 / 2 times
        # timeSliderBookmark.framePreviousBookmarkAtCurrentTime()

        previous_shots = self.get_previous_shots_at_time(time)
        if previous_shots:
            cmds.playbackOptions(minTime=previous_shots[-1].start)
            cmds.playbackOptions(maxTime=previous_shots[-1].stop)
            cmds.currentTime(previous_shots[-1].start)

    def offset_frame_of_shot_at_time(self, time: int, total: int = 1):
        """
        Change the length of the shot at a given time and
        move the next shots to avoid overlaps.

        Args:
            time (int): The time to get the shot at.
            total (int, optional): The number of frame to offset. Defaults to 1.

        Returns:
            None
        """
        active_shot = self.get_shots_at_time(time)[0]
        next_shots = self.get_next_shots_at_time(time)
        active_shot.offset_end_frame(total)
        for shot in next_shots:
            shot.move(total)

    def resolve_overlapping_shots(self):
        """
        Resolve overlapping shots by moving them to the future.
        Returns:
            None
        """
        for i in range(1, len(self.shots)):
            prev_shot = self.shots[i - 1]
            curr_shot = self.shots[i]

            if curr_shot.start < prev_shot.stop:
                offset = prev_shot.stop - curr_shot.start
                curr_shot.move(offset + 1)

        self.sort_shots()

    def resolve_gaps_between_shots(self):
        """
        Resolve shots separated by time by moving them.
        Returns:
            None
        """
        for i in range(0, len(self.shots) - 1):
            curr_shot = self.shots[i]
            next_shot = self.shots[i + 1]

            if curr_shot.stop < next_shot.start - 1:
                offset = next_shot.start - curr_shot.stop
                next_shot.move(-offset + 1)

        self.sort_shots()

    def generate_shot_name(self) -> str:
        """
        Generate a simple shot name.

        Returns:
            str: The generated shot name.
        """
        # We assume that the shot name format is SQXXXX_SHXXXX
        # If a shot already exists, use that sequence number
        # else don't generate the shot name
        if self.shots:
            sequence = self.shots[0].name.split("_")[0]
            self.name = sequence

            all_shots_number = [
                int(shot.name.split("_")[-1][2:-1]) for shot in self.shots
            ]
            all_shots_number.sort()

            return f"{self.name}_SH{all_shots_number[-1] + 1:03}0"
        else:
            return f"{self.name}_SH0010"


def get_sequencer_sequence(reset=False):
    """
    Get the sequencer sequence instance.
    Args:
        reset (bool): If true, return a new :class:`SequencerSequence` instance.

    Returns:
        :class:`SequencerSequence`: A class instance.
    """
    if not SequencerSequence.instance or reset:
        SequencerSequence.instance = SequencerSequence.load()
    return SequencerSequence.instance
