from maya import cmds


from PIK_maya_anim_sequencer.scripts.constants import PREVIEW_CAMERA_NAME
from PIK_maya_anim_sequencer.scripts.constants import PREVIEW_VIEWPORT_SIZE


def create_sequencer_camera(
    camera_name: str, preview_camera: bool = False
) -> list[str]:
    """Create a camera designed for the sequencer tool.
    The camera will be created as a copy of the persp
    cam.

    Args:
        camera_name (str): The name of the created camera.
        preview_camera (bool, optional): If true, create an invisble camera with 'currentCam' attribute. Defaults to False.

    Returns:
        list[str]: Camera transform and shape name.
    """
    # Create a camera and get the shape name.
    camera = cmds.camera(n=camera_name)
    camera_transform, camera_shape = camera
    camera_transform = cmds.rename(camera_transform, camera_name, ignoreShape=True)

    if preview_camera:
        # If this is a preview camera, we want to hide it and
        # make sure the user is not able to select it
        cmds.setAttr(f"{camera_transform}.visibility", 0)
        cmds.setAttr(f"{camera_transform}.overrideEnabled", 1)
        cmds.setAttr(f"{camera_transform}.overrideDisplayType", 2)
        cmds.addAttr(camera_transform, longName="currentCam", dataType="string")
    else:
        # Detect the active working camera (default to persp)
        # and match its position, rotation and focal length.
        active_camera = "persp"
        for viewport in cmds.getPanel(type="modelPanel"):
            is_active = cmds.modelEditor(viewport, query=True, activeView=True)

            if is_active:
                active_camera = cmds.modelEditor(viewport, query=True, camera=True)
                break

        cmds.matchTransform(camera_transform, active_camera, pos=True, rot=True)

        active_camera_shape = cmds.listRelatives(active_camera, shapes=True)[0]
        active_camera_focal = cmds.getAttr(f"{active_camera_shape}.focalLength")
        cmds.setAttr(f"{camera_shape}.focalLength", active_camera_focal)

    # Standard camera settings
    cmds.setAttr(f"{camera_shape}.displayGateMaskColor", 0.0, 0.0, 0.0)
    cmds.setAttr(f"{camera_shape}.displayGateMaskOpacity", 1.0)

    return [camera_transform, camera_shape]


def get_all_cameras() -> list[str]:
    """Returns all cameras transforms names.

    Returns:
        list[str]: Cameras transform names
    """
    return [
        cmds.listRelatives(shape, parent=True)[0] for shape in cmds.ls(cameras=True)
    ]


def get_preview_camera(camera_name: str = PREVIEW_CAMERA_NAME) -> list[str]:
    """Get the preview camera of the current scene.
    If the preview camera does not exist, it will be created.

    Args:
        camera_name (str, optional): Name of the preview camera. Defaults to PREVIEW_CAMERA_NAME.

    Returns:
        list[str]: Camera transform and shape name.
    """
    if camera_name not in get_all_cameras():
        return create_sequencer_camera(camera_name, preview_camera=True)
    else:
        return [camera_name, cmds.listRelatives(camera_name, shapes=True)[0]]


def create_preview_viewport() -> str:
    """Create a new viewport dockable window that will show the preview camera view.

    Returns:
        str: The full path name to the workspaceControl
    """
    preview_camera = get_preview_camera()
    dock_name = "PIK_previewViewportDock"

    workspace = cmds.workspaceControl(
        dock_name + "WorkspaceControl",
        label="Preview Viewport",
        floating=True,
        initialWidth=PREVIEW_VIEWPORT_SIZE[0],
        initialHeight=PREVIEW_VIEWPORT_SIZE[1],
        retain=False,
    )

    cmds.setParent(workspace)

    cmds.paneLayout()
    preview_panel = cmds.modelPanel(camera=preview_camera[1])

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
    )

    return workspace


def generate_camera_name(shot_name: str) -> str:
    """Returns a generated camera name from a shot name.

    Args:
        shot_name (str): The shot name

    Returns:
        str: The generated camera name.
    """
    return f"{shot_name}"
