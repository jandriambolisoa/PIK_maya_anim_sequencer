from maya import cmds
from maya import OpenMaya, OpenMayaAnim

from PIK_maya_anim_sequencer.scripts.constants import (
    PREVIEW_CAMERA_NAME,
    PREVIEW_VIEWPORT_SIZE,
)
from PIK_maya_anim_sequencer.ui.sequencer import run as sequencer_ui
from PIK_maya_anim_sequencer.ui.windows import (
    create_viewport,
    maya_dock_control_to_window,
)

from PIK_maya_anim_sequencer.scripts.sequence import (
    SequencerSequence,
    get_sequencer_sequence,
)
from PIK_maya_anim_sequencer.scripts.cameras import SequencerCamera


callbacks = list()


def update_preview_viewport_camera(
    current_time: OpenMaya.MTime, sequencer_sequence: SequencerSequence
):
    """
    Change the given Sequencer's Sequence viewport camera to the current shot camera.
    Args:
        current_time (:class:`OpenMaya.MTime`): The current time.
        sequencer_sequence (:class:`SequencerSequence`): The current sequence.

    Returns:
        None
    """
    shots = sequencer_sequence.get_shots_at_time(current_time.value())

    if shots and sequencer_sequence.preview_viewport:
        shot = shots[0]
        if shot.cam.shape != cmds.modelEditor(
            sequencer_sequence.preview_viewport, query=True, camera=True
        ):
            shot.cam.set_as_camera_viewport(sequencer_sequence.preview_viewport)


def update_shots_start_and_stop_datas(
    current_time: OpenMaya.MTime, sequencer_sequence: SequencerSequence
):
    """
    Update the shots of the given Sequencer Sequence.
    Args:
        current_time (:class:`OpenMaya.MTime`): The current time.
        sequencer_sequence (:class:`SequencerSequence`): The current sequence.

    Returns:
        None
    """
    # When dragging a bookmark in the time slider to change its length
    # or its time placement, Maya does not consider this as a
    # scrubbing action.
    # sequencer_sequence = clientData
    if not OpenMayaAnim.MAnimControl.isScrubbing():
        sequencer_sequence.update_range_of_shots()


def setup_preview_viewport(sequencer_sequence: SequencerSequence) -> int:
    """
    Setup a time changed callback to dynamically update the preview viewport of a given Sequencer Sequence.
    Args:
        sequencer_sequence (:class:`SequencerSequence`): The current sequence.

    Returns:
        int: The callback id used to remove it.
    """
    callback_id = OpenMaya.MDGMessage.addTimeChangeCallback(
        update_preview_viewport_camera, sequencer_sequence
    )
    return callback_id


def setup_shot_length_updater(sequencer_sequence: SequencerSequence) -> int:
    """
    Setup a time changed callback to dynamically update all shots' length of a given Sequencer Sequence.
    Args:
        sequencer_sequence (:class:`SequencerSequence`): The current sequence.

    Returns:
        int: The callback id used to remove it.
    """
    callback_id = OpenMaya.MDGMessage.addTimeChangeCallback(
        update_shots_start_and_stop_datas, sequencer_sequence
    )
    return callback_id


def setup_sequence_reset_if_scene_open(window: str) -> int:
    """
    Setup a callback whenever a scene is opened to close the sequencer window.
    Args:
        window (str): The workspace control (maya window) to close.

    Returns:
        int: The callback id used to remove it.
    """
    callback_id = OpenMaya.MSceneMessage.addCallback(
        OpenMaya.MSceneMessage.kBeforeOpen, close_sequencer, window
    )
    return callback_id


def setup_sequence_reset_if_new_scene(window: str) -> int:
    """
    Setup a callback whenever a new scene is created to close the sequencer window.
    Args:
        window (str): The workspace control (maya window) to close.

    Returns:
        int: The callback id used to remove it.
    """
    callback_id = OpenMaya.MSceneMessage.addCallback(
        OpenMaya.MSceneMessage.kBeforeNew, close_sequencer, window
    )
    return callback_id


def run():
    """Runs the PIK_maya_anim_sequencer.
    Displays the UI and add callbacks."""
    if callbacks:
        remove_callbacks()

    sequencer_sequence = get_sequencer_sequence(reset=True)
    sequencer_sequence.preview_viewport = create_viewport(
        label="Preview Viewport", viewport_size=PREVIEW_VIEWPORT_SIZE
    )
    window = sequencer_ui()

    maya_dock_control_to_window(window, sequencer_sequence.preview_viewport)

    # Add callbacks
    callbacks.append(setup_preview_viewport(sequencer_sequence))
    callbacks.append(setup_shot_length_updater(sequencer_sequence))
    callbacks.append(setup_sequence_reset_if_scene_open(window))
    callbacks.append(setup_sequence_reset_if_new_scene(window))


def close_sequencer(window: str):
    """
    Close the sequencer.
    Args:
        window (str): The workspace control (maya window) to close.

    Returns:
        None
    """
    remove_callbacks()

    # window = clientData
    cmds.workspaceControl(window, edit=True, close=True)

    sequencer_sequence = get_sequencer_sequence()
    preview_viewport_control = cmds.modelPanel(
        sequencer_sequence.preview_viewport, query=True, control=True
    )
    if preview_viewport_control:
        preview_viewport_control = preview_viewport_control.split("|")[0]
        cmds.workspaceControl(preview_viewport_control, edit=True, close=True)


def remove_callbacks():
    """Remove sequencer's related callbacks."""
    for callback_id in callbacks:
        OpenMaya.MDGMessage.removeCallback(callback_id)
    callbacks.clear()
