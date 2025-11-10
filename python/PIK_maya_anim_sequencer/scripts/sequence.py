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

    @classmethod
    def load(cls):
        """
        Load the sequencer sequence from the opened scene.
        Returns:
            An instance of SequencerSequence.
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
        self.shots = [shot for shot in sorted(self.shots, key=lambda item: item.start)]

    def get_shots_at_time(self, time: int):
        shot_list = list()
        for shot in self.shots:
            if shot.start <= time <= shot.stop:
                shot_list.append(shot)

        return shot_list

    def delete_shot_at_time(self, time: int):
        active_shot = self.get_shots_at_time(time)[0]
        if not active_shot:
            OpenMaya.MGlobal.displayWarning("Sequencer: No active shot detected.")
            return

        confirmation = cmds.confirmDialog(
            title="Confirm",
            message=f"Do you want to delete current shot?\n{active_shot.name}",
            button=["Yes", "No"],
            defaultButton="No",
            cancelButton="No",
            dismissString="No",
        )
        if confirmation == "Yes":
            self.shots.remove(active_shot)
            active_shot.delete()
            del active_shot

    def get_previous_shots_at_time(self, time: int):
        shot_list = list()
        for shot in self.shots:
            if shot.stop < time:
                shot_list.append(shot)

        return shot_list

    def get_next_shots_at_time(self, time: int):
        shot_list = list()
        for shot in self.shots:
            if shot.start > time:
                shot_list.append(shot)

        return shot_list

    def update_range_of_shot_at_time(self, time: int) -> None:
        shots = self.get_shots_at_time(time)
        if shots:
            for shot in shots:
                shot.start = cmds.getAttr(f"{shot.node}.timeRangeStart")
                shot.stop = cmds.getAttr(f"{shot.node}.timeRangeStop")

        self.sort_shots()

    def update_range_of_shots(self):
        for shot in self.shots:
            shot.start = cmds.getAttr(f"{shot.node}.timeRangeStart")
            shot.stop = cmds.getAttr(f"{shot.node}.timeRangeStop")
        self.sort_shots()

    @staticmethod
    def defocus():
        """Reset the playback range to see all shots."""
        timeSliderBookmark.frameAllBookmark()

    @staticmethod
    def extra_defocus(defocus_amount: int = 24):
        """Extend the playback range by defocus_amount frames.

        Args:
            defocus_amount (int, optional): The number of frame to add at each end of the playback range. Defaults to 24.
        """
        current_start = cmds.playbackOptions(query=True, minTime=True)
        current_stop = cmds.playbackOptions(query=True, maxTime=True)
        cmds.playbackOptions(minTime=int(current_start) - defocus_amount)
        cmds.playbackOptions(maxTime=int(current_stop) + defocus_amount)

    def is_sequence_focus(self) -> bool:
        """Return True if a sequence is actually in focus.
        A focus means that the start and the end of a shot
        (or all the shots for a sequence) match the
        current playback range min and max values.

        Returns:
            bool: Sequence focus.
        """
        current_start = cmds.playbackOptions(query=True, minTime=True)
        current_stop = cmds.playbackOptions(query=True, maxTime=True)
        if [self.shots[0].start, self.shots[-1].stop] == [current_start, current_stop]:
            return True

        return False

    def is_shot_focus_at_time(self, time: int) -> bool:
        """Return True if the active shot is in focus.
        A focus means that the start and the end of a shot
        (or all the shots for a sequence) match the
        current playback range min and max values.

        Returns:
            bool: Active shot focus.
        """
        current_start = cmds.playbackOptions(query=True, minTime=True)
        current_stop = cmds.playbackOptions(query=True, maxTime=True)
        active_shots = self.get_shots_at_time(time)
        for shot in active_shots:
            if [shot.start, shot.stop] == [current_start, current_stop]:
                return True

        return False

    def is_sequence_fully_defocus(self) -> bool:
        """Returns True if the playback range contains all
        shots and does not focus the sequence.
        A focus means that the start and the end of a shot
        (or all the shots for a sequence) match the
        current playback range min and max values.

        Returns:
            bool: The playback range contains all shots and does not focus the sequence
        """
        current_start = cmds.playbackOptions(query=True, minTime=True)
        current_stop = cmds.playbackOptions(query=True, maxTime=True)

        if self.shots[0].start > current_start and self.shots[-1].stop < current_stop:
            return True

        return False

    def focus_next_at_time(self, time: int):
        """Focus the next bookmark."""
        timeSliderBookmark.frameNextBookmarkAtCurrentTime()

    def focus_previous_at_time(self, time: int):
        """Focus the previous bookmark."""
        # Maya default function seems to work 1 / 2 times
        # timeSliderBookmark.framePreviousBookmarkAtCurrentTime()

        previous_shots = self.get_previous_shots_at_time(time)
        if previous_shots:
            cmds.playbackOptions(minTime=previous_shots[-1].start)
            cmds.playbackOptions(maxTime=previous_shots[-1].stop)
            cmds.currentTime(previous_shots[-1].start)

    def offset_frame_of_shot_at_time(self, time: int, total: int = 1):
        """Change the length of a shot and
        move the next shots to avoid overlaps.

        Args:
            total (int, optional): The number of frame to offset. Defaults to 1.
        """
        active_shot = self.get_shots_at_time(time)[0]
        next_shots = self.get_next_shots_at_time(time)
        active_shot.offset_end_frame(total)
        for shot in next_shots:
            shot.move(total)

    def resolve_overlapping_shots(self):
        """Move shots that are overlapping."""
        for i in range(1, len(self.shots)):
            prev_shot = self.shots[i - 1]
            curr_shot = self.shots[i]

            if curr_shot.start < prev_shot.stop:
                offset = prev_shot.stop - curr_shot.start
                curr_shot.move(offset + 1)

        self.sort_shots()

    def resolve_gaps_between_shots(self):
        """Move shots that are not connected."""
        for i in range(0, len(self.shots) - 1):
            curr_shot = self.shots[i]
            next_shot = self.shots[i + 1]

            if curr_shot.stop < next_shot.start - 1:
                offset = next_shot.start - curr_shot.stop
                next_shot.move(-offset + 1)

        self.sort_shots()

    def generate_shot_name(self) -> str | None:
        """Generate a simple shot name.

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

    def create_preview_viewport(self, label: str = "Preview Viewport") -> str:
        """Create a new viewport dockable window.

        Returns:
            str: The name of the new model panel name (viewport)
        """
        dock_name = "PIK_" + label.title().replace(" ", "") + "Dock"

        if cmds.workspaceControl(dock_name + "WorkspaceControl", exists=True):
            cmds.workspaceControl(dock_name + "WorkspaceControl", edit=True, close=True)

        workspace = cmds.workspaceControl(
            dock_name + "WorkspaceControl",
            label=label,
            floating=True,
            initialWidth=PREVIEW_VIEWPORT_SIZE[0],
            initialHeight=PREVIEW_VIEWPORT_SIZE[1],
            retain=False,
        )

        cmds.setParent(workspace)

        cmds.paneLayout()
        preview_panel = cmds.modelPanel()

        # Enable shading, manage visibilities
        cmds.modelEditor(
            preview_panel,
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

        self.preview_viewport = preview_panel

        return preview_panel


def get_sequencer_sequence(reset=False):
    if not SequencerSequence.instance or reset:
        SequencerSequence.instance = SequencerSequence.load()
    return SequencerSequence.instance
