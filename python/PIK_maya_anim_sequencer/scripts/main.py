from maya import cmds
from maya import OpenMaya

from PIK_maya_anim_sequencer.scripts.cameras import (
    get_preview_camera,
)
from PIK_maya_anim_sequencer.scripts.shots import (
    get_active_shot,
)
from PIK_maya_anim_sequencer.ui.sequencer import run as sequencer_ui

callbacks = []


def snap_preview_camera_to_shot_camera(current_time: OpenMaya.MTime, client_data=None):
    """This function takes the preview camera and snap
    it to the active shot camera (postition, rotation,
    focal length).
    """
    preview_camera = get_preview_camera()
    preview_camera_transform = preview_camera[0]
    preview_camera_shape = preview_camera[1]
    current_cam = cmds.getAttr(f"{preview_camera_transform}.currentCam")

    shot = get_active_shot()

    if shot:
        if shot.cam != current_cam:
            # Constrain the position and rotation
            constraint = cmds.listRelatives(
                preview_camera_transform, type="parentConstraint"
            )
            if constraint:
                cmds.delete(constraint[0])
            cmds.setAttr(
                f"{preview_camera_transform}.currentCam", shot.cam, type="string"
            )
            cmds.matchTransform(preview_camera_transform, shot.cam)
            cmds.parentConstraint(shot.cam, preview_camera_transform)

            # Constrain the focal length
            shot_cam_shape = cmds.listRelatives(shot.cam, shapes=True)[0]
            cmds.connectAttr(
                f"{shot_cam_shape}.focalLength",
                f"{preview_camera_shape}.focalLength",
                force=True,
            )


def setup_preview_camera() -> int:
    """This function setup a Maya callback so
    that everytime the time is updated, the
    preview camera will find the right camera
    to snap to.

    Returns:
        int: The ID of the callback.
    """
    callback_id = OpenMaya.MDGMessage.addTimeChangeCallback(
        snap_preview_camera_to_shot_camera
    )

    return callback_id


def run():
    """Runs the PIK_maya_anim_sequencer.
    Displays the UI and add callbacks."""
    sequencer_ui()
    callbacks.append(setup_preview_camera())


def close():
    """Remove sequencer's related callbacks."""
    OpenMaya.MDGMessage.removeCallbacks(callbacks)
