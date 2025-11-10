from maya import cmds
from maya import OpenMaya, OpenMayaAnim

from PIK_maya_anim_sequencer.scripts.constants import PREVIEW_CAMERA_NAME
from PIK_maya_anim_sequencer.ui.sequencer import run as sequencer_ui

from PIK_maya_anim_sequencer.scripts.sequence import get_sequencer_sequence
from PIK_maya_anim_sequencer.scripts.cameras import SequencerCamera

callbacks = list()


def update_preview_viewport_camera(current_time: OpenMaya.MTime, clientData):
    sequencer_sequence = clientData
    shots = sequencer_sequence.get_shots_at_time(current_time.value())

    if shots and sequencer_sequence.preview_viewport:
        shot = shots[0]
        if shot.cam.shape != cmds.modelEditor(
            sequencer_sequence.preview_viewport, query=True, camera=True
        ):
            shot.cam.set_as_camera_viewport(sequencer_sequence.preview_viewport)


def update_shots_start_and_stop_datas(current_time: OpenMaya.MTime, clientData):
    # When dragging a bookmark in the time slider to change its length
    # or its time placement, Maya does not consider this as a
    # scrubbing action.
    sequencer_sequence = clientData
    if not OpenMayaAnim.MAnimControl.isScrubbing():
        sequencer_sequence.update_range_of_shots()


def setup_preview_viewport(clientData=None) -> int:
    """This function setup a Maya callback so
    that everytime the time is updated, the
    preview camera will find the right camera
    to snap to.

    Returns:
        int: The ID of the callback.
    """
    callback_id = OpenMaya.MDGMessage.addTimeChangeCallback(
        update_preview_viewport_camera, clientData
    )
    return callback_id


def setup_shot_length_updater(clientData=None) -> int:
    callback_id = OpenMaya.MDGMessage.addTimeChangeCallback(
        update_shots_start_and_stop_datas, clientData
    )
    return callback_id


def setup_sequence_reset_if_scene_open(clientData=None) -> int:
    callback_id = OpenMaya.MSceneMessage.addCallback(
        OpenMaya.MSceneMessage.kBeforeOpen, close_sequencer, clientData
    )
    return callback_id


def setup_sequence_reset_if_new_scene(clientData=None) -> int:
    callback_id = OpenMaya.MSceneMessage.addCallback(
        OpenMaya.MSceneMessage.kBeforeNew, close_sequencer, clientData
    )
    return callback_id


def run():
    """Runs the PIK_maya_anim_sequencer.
    Displays the UI and add callbacks."""
    if callbacks:
        remove_callbacks()

    sequencer_sequence = get_sequencer_sequence(reset=True)
    sequencer_sequence.preview_viewport = sequencer_sequence.create_preview_viewport()

    # Display UI and dock controls to preview viewport
    window = sequencer_ui()
    try:
        preview_viewport_control = cmds.modelPanel(
            sequencer_sequence.preview_viewport, query=True, control=True
        )
        if preview_viewport_control:
            preview_viewport_control = preview_viewport_control.split("|")[0]
            cmds.workspaceControl(
                window, edit=True, dockToControl=(preview_viewport_control, "bottom")
            )
    except RuntimeError:
        # If the viewport is already docked, Maya will raise an error.
        pass

    # Add callbacks
    callbacks.append(setup_preview_viewport(clientData=sequencer_sequence))
    callbacks.append(setup_shot_length_updater(clientData=sequencer_sequence))
    callbacks.append(setup_sequence_reset_if_scene_open(clientData=window))
    callbacks.append(setup_sequence_reset_if_new_scene(clientData=window))


def close_sequencer(clientData):
    remove_callbacks()

    window = clientData
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
