import os
import json

from maya import cmds
from maya import OpenMaya
from maya.plugin.timeSliderBookmark import timeSliderBookmark


class Shot:
    """Shot object in the sequencer tool.
    A shot consists of a bookmark and a camera.
    """

    def __init__(self, node: str):
        self.node = node
        self.name = cmds.getAttr(f"{self.node}.shot")
        self.cam = cmds.getAttr(f"{self.node}.cam")
        self.start = cmds.getAttr(f"{self.node}.timeRangeStart")
        self.stop = cmds.getAttr(f"{self.node}.timeRangeStop")
        self.color = cmds.getAttr(f"{self.node}.color")[-1]

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

        self.refresh()

        if move_camera:
            # Move this shot's camera
            cmds.keyframe(self.cam, relative=True, timeChange=int(offset))

    def offset_end_frame(self, offset: int):
        """Offset the stop frame of the bookmark.

        Args:
            offset (int): The amount of offset.
        """
        cmds.setAttr(f"{self.node}.timeRangeStop", self.stop + offset)

    def refresh(self):
        """Refresh the values of the Shot object.

        Returns:
            Shot: The instance itself.
        """
        self.name = (cmds.getAttr(f"{self.node}.shot"),)
        self.cam = cmds.getAttr(f"{self.node}.cam")
        self.start = cmds.getAttr(f"{self.node}.timeRangeStart")
        self.stop = cmds.getAttr(f"{self.node}.timeRangeStop")
        self.color = cmds.getAttr(f"{self.node}.color")[-1]

    def focus(self):
        """Update Maya playback range to frame this shot."""
        cmds.playbackOptions(edit=True, min=self.start, max=self.stop)


def create_custom_bookmark(
    name: str, start: int, stop: int, cam: str, color: tuple
) -> str:
    """Create a Maya time slider bookmark with
    shot name and linked camera datas as attributes.

    Args:
        name (str): The name of the bookmark
        start (int): Starting frame
        stop (int): Ending frame
        cam (str): The transform camera name
        color (tuple): The color as RGB values

    Returns:
        str: The time slider bookmark node name.
    """
    node = timeSliderBookmark.createBookmark(
        name=name, start=start, stop=stop, color=color
    )
    node = cmds.rename(node, f"bookmark_{name}")

    cmds.addAttr(node, longName="cam", dataType="string")
    cmds.addAttr(node, longName="shot", dataType="string")

    cmds.setAttr(f"{node}.cam", cam, type="string")
    cmds.setAttr(f"{node}.shot", name, type="string")

    return node


def create_shot(
    shot_name: str, color: tuple, shot_length: int, shot_camera: str
) -> Shot:
    """Create a Shot object by creating a bookmark.
    This function won't do anything if the shot
    already exists.

    Args:
        shot_name (str): The name of the shot.
        color (tuple): The RGB float values of the bookmark.
        shot_length (int): The lenght of the shot.
        shot_camera (str): The camera name.

    Returns:
        Shot: The created shot instance.
    """

    if shot_name in [shot.name for shot in get_all_shots()]:
        OpenMaya.MGlobal.displayWarning("This shot already exists.")
        return

    start = int(cmds.currentTime(query=True))
    stop = start + shot_length

    node = create_custom_bookmark(shot_name, start, stop, shot_camera, color)

    return Shot(node)


def get_active_shot() -> Shot:
    """Returns the active shot if there is.

    Returns:
        Shot: The active shot.
    """
    # Maya default function doesn't work if you open
    # a saved file already containing bookmarks
    # for some reason... thx Autodesk!
    # node = timeSliderBookmark.getBookmarkAtCurrentTime()

    all_shots = get_all_shots()
    current_time = cmds.currentTime(query=True)
    active_shot = None

    for shot in all_shots:
        if current_time >= shot.start and current_time <= shot.stop:
            active_shot = shot
            break

    return active_shot


def delete_active_shot():
    """Delete the active shot if there is.
    A confirm dialog will appear to avoid
    mistakes.
    """
    active_shot = get_active_shot()

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
        cmds.delete(active_shot.cam)
        cmds.delete(active_shot.node)


def get_all_shots(sort: bool = True) -> list[Shot]:
    """Returns all shots as Shot instances chronologically sorted.

    Args:
        sorted (bool, optional): If False, return order is not sorted. Defaults to True.

    Returns:
        list[Shot]: A list of Shot instances.
    """
    all_shots = []
    for node in cmds.ls(exactType="timeSliderBookmark"):
        try:
            all_shots.append(Shot(node))
        except ValueError:
            # The time slider bookmark might not be created
            # by the sequencer. In this case, attributes
            # are missing and raise an error. We don't
            # want to append it as it's not a shot.
            continue

    if sort and all_shots:
        all_shots = sorted(all_shots, key=lambda x: x.start)

    return all_shots


def get_previous_shots() -> list[Shot]:
    """List shots that are before the active shot.

    Returns:
        list[Shot]: A list of shots chronologically sorted.
    """
    all_shots = get_all_shots()
    active_shot = get_active_shot()
    all_shots_name = [shot.name for shot in all_shots]
    active_shot_index = all_shots_name.index(active_shot.name)
    return all_shots[:active_shot_index]


def get_next_shots() -> list[Shot]:
    """List shots that are after the active shot.

    Returns:
        list[Shot]: A list of shots chronologically sorted.
    """
    all_shots = get_all_shots()
    active_shot = get_active_shot()
    all_shots_name = [shot.name for shot in all_shots]
    active_shot_index = all_shots_name.index(active_shot.name)
    return all_shots[active_shot_index + 1 :]


def defocus():
    """Reset the playback range to see all shots."""
    timeSliderBookmark.frameAllBookmark()


def extra_defocus(defocus_amount: int = 24):
    """Extend the playback range by defocus_amount frames.

    Args:
        defocus_amount (int, optional): The number of frame to add at each end of the playback range. Defaults to 24.
    """
    current_start = cmds.playbackOptions(query=True, minTime=True)
    current_stop = cmds.playbackOptions(query=True, maxTime=True)
    cmds.playbackOptions(minTime=int(current_start) - defocus_amount)
    cmds.playbackOptions(maxTime=int(current_stop) + defocus_amount)


def is_sequence_focus() -> bool:
    """Return True if a sequence is actually in focus.
    A focus means that the start and the end of a shot
    (or all the shots for a sequence) match the
    current playback range min and max values.

    Returns:
        bool: Sequence focus.
    """
    current_start = cmds.playbackOptions(query=True, minTime=True)
    current_stop = cmds.playbackOptions(query=True, maxTime=True)
    all_shots = get_all_shots()
    if [all_shots[0].start, all_shots[-1].stop] == [current_start, current_stop]:
        return True

    return False


def is_active_shot_focus() -> bool:
    """Return True if the active shot is in focus.
    A focus means that the start and the end of a shot
    (or all the shots for a sequence) match the
    current playback range min and max values.

    Returns:
        bool: Active shot focus.
    """
    current_start = cmds.playbackOptions(query=True, minTime=True)
    current_stop = cmds.playbackOptions(query=True, maxTime=True)
    active_shot = get_active_shot()
    if [active_shot.start, active_shot.stop] == [current_start, current_stop]:
        return True

    return False


def is_sequence_fully_defocus() -> bool:
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
    all_shots = get_all_shots()
    if all_shots[0].start > current_start and all_shots[-1].stop < current_stop:
        return True

    return False


def focus_next():
    """Focus the next bookmark."""
    timeSliderBookmark.frameNextBookmarkAtCurrentTime()


def focus_previous():
    """Focus the previous bookmark."""
    # Maya default function seems to work 1 / 2 times
    # timeSliderBookmark.framePreviousBookmarkAtCurrentTime()

    previous_shots = get_previous_shots()
    if previous_shots:
        cmds.playbackOptions(minTime=previous_shots[-1].start)
        cmds.playbackOptions(maxTime=previous_shots[-1].stop)
        cmds.currentTime(previous_shots[-1].start)


def offset_frame_of_active_shot(total: int = 1):
    """Change the length of a shot and
    move the next shots to avoid overlaps.

    Args:
        total (int, optional): The number of frame to offset. Defaults to 1.
    """
    active_shot = get_active_shot()
    next_shots = get_next_shots()
    active_shot.offset_end_frame(total)
    for shot in next_shots:
        shot.move(total)


def resolve_overlapping_shots():
    """Move shots that are overlapping."""
    all_shots = get_all_shots()

    for i in range(1, len(all_shots)):
        prev_shot = all_shots[i - 1]
        curr_shot = all_shots[i]
        prev_shot.refresh()

        if curr_shot.start < prev_shot.stop:
            offset = prev_shot.stop - curr_shot.start
            curr_shot.move(offset + 1)


def resolve_gaps_between_shots():
    """Move shots that are not connected."""
    all_shots = get_all_shots()

    for i in range(len(all_shots) - 1):
        curr_shot = all_shots[i]
        next_shot = all_shots[i + 1]
        curr_shot.refresh()

        if curr_shot.stop < next_shot.start - 1:
            offset = next_shot.start - curr_shot.stop
            next_shot.move(-offset + 1)


def generate_shot_name() -> str:
    """Generate a simple shot name.

    Returns:
        str: The generated shot name.
    """
    # We assume that the shot name format is SQXXXX_SHXXXX

    all_shots = get_all_shots()

    # If a shot already exists, use that sequence number
    # else don't generate the shot name
    if all_shots:
        sequence = all_shots[0].name.split("_")[0]
    else:
        return None

    all_shots_number = [shot.name[-4:-1] for shot in all_shots]

    all_shots_number.sort()
    last_number = int(all_shots_number[-1])

    return f"{sequence}_SH{last_number+1:03}0"


def export_shots(show_output=True):
    """Export every shots datas into a JSON file and
    export cameras individually into .ma files.
    JSON file structure example:
    {
        "SQ0020_SH0010": {
            "shot_name": "SQ0020_SH0010",
            "shot_sequence": "SQ0020",
            "shot_length": 24,
            "shot_start": 1001,
            "shot_stop": 1025,
            "shot_camera_name": "CAM_SQ0020_SH0010",
            "shot_color": [
                0.9607843160629272,
                0.48627451062202454,
                0.0
            ]
    }

    Args:
        show_output (bool, optional): If True, a file explorer will open to show outputs. Defaults to True.
    """
    confirmation = cmds.confirmDialog(
        title="Confirm",
        message="Do you want to export the current sequence datas ?",
        button=["Yes", "No"],
        defaultButton="No",
        cancelButton="No",
        dismissString="No",
    )
    if confirmation == "No":
        return

    folderpath = cmds.fileDialog2(fileMode=2, dialogStyle=1, hideNameEdit=True)

    if folderpath:
        folderpath = folderpath[0]
        all_shots = get_all_shots()
        response = {}

        for shot in all_shots:
            response[shot.name] = {
                "shot_name": shot.name,
                "shot_sequence": shot.name.split("_")[0],
                "shot_length": int(shot.stop - shot.start),
                "shot_start": 1001,
                "shot_stop": 1001 + int(shot.stop - shot.start),
                "shot_camera_name": shot.cam,
                "shot_color": shot.color,
            }

            cmds.select(shot.cam, replace=True)
            cmds.file(
                os.path.join(folderpath, shot.cam + ".ma"),
                exportSelected=True,
                type="mayaAscii",
                force=True,
            )

            # TODO Create dependency to PIK_maya_quickBlast and
            # export playblast for each shot

        with open(os.path.join(folderpath, "datas.json"), "w") as file:
            json.dump(response, file, indent=4)

    if show_output:
        os.startfile(folderpath)
