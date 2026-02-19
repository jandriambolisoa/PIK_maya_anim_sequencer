from maya import cmds

from PIK_maya_anim_sequencer.scripts.constants import (
    PREVIEW_VIEWPORT_SIZE,
    DEFAULT_FAR_CLIP,
    DEFAULT_NEAR_CLIP,
    DEFAULT_GATEMASK_COLOR,
    DEFAULT_OVERSCAN,
)


class SequencerCamera:
    """
    A camera object in the sequencer tool.
    """

    def __init__(self, transform: str, shape: str):
        self.transform = transform
        self.shape = shape

    @classmethod
    def create(cls, name: str):
        """
        Create a sequencer camera.
        Args:
            name (str): The name of the camera

        Returns:
            :class:`SequencerCamera`: A class instance.
        """
        if cls.get(name):
            raise RuntimeError(f"Camera {name} already exists")

        # Create a camera and rename it properly
        transform, _ = cmds.camera()
        transform = cmds.rename(transform, name)
        shape = cmds.listRelatives(transform, shapes=True)[0]

        # Setup camera default attributes
        cmds.setAttr(
            f"{shape}.displayGateMaskColor",
            DEFAULT_GATEMASK_COLOR,
            DEFAULT_GATEMASK_COLOR,
            DEFAULT_GATEMASK_COLOR,
        )
        cmds.setAttr(f"{shape}.displayGateMaskOpacity", 1.0)
        cmds.setAttr(f"{shape}.displayResolution", 1)
        cmds.setAttr(f"{shape}.overscan", DEFAULT_OVERSCAN)
        cmds.setAttr(f"{shape}.nearClipPlane", DEFAULT_NEAR_CLIP)
        cmds.setAttr(f"{shape}.farClipPlane", DEFAULT_FAR_CLIP)

        return cls(transform, shape)

    @classmethod
    def get(cls, transform_name: str):
        """
        Get a camera from its transform name.
        Args:
            transform_name (str): the name of the camera transform

        Returns:
            :class:`SequencerCamera`: A class instance.
        """
        camera_shape = cmds.ls(transform_name + "|*", type="camera", l=True)

        if camera_shape:
            return cls(
                transform=cmds.listRelatives(camera_shape[0], parent=True, f=True)[0],
                shape=camera_shape[0],
            )
        else:
            return None

    def get_attr(self, attr: str) -> any:
        """
        Return the value of a camera's attribute.
        This function will look for a shape's attribute, if not existing,
        it will look for a transform's attribute.
        Args:
            attr (str): the name of the attribute

        Returns:
            any: the value of the attribute or None if the attribute isn't found.
        """
        shape_attr = cmds.listAttr(self.shape)
        transform_attr = cmds.listAttr(self.transform)
        if attr in shape_attr:
            return cmds.getAttr(self.shape + "." + attr)
        elif attr in transform_attr:
            return cmds.getAttr(self.transform + "." + attr)
        else:
            return None

    def set_attr(self, attr: str, value) -> None:
        """
        Set the value of a camera's attribute if it exists.
        Args:
            attr (str): the name of the attribute
            value (any): the value of the attribute

        Returns:
            None
        """
        shape_attr = cmds.listAttr(self.shape)
        transform_attr = cmds.listAttr(self.transform)
        if attr in shape_attr:
            cmds.setAttr(self.shape + "." + attr, value)
        elif attr in transform_attr:
            cmds.setAttr(self.transform + "." + attr, value)

    def move(self, offset: int) -> None:
        """
        Move the camera in time
        Args:
            offset (int): The amount of time unit to move.

        Returns:
            None
        """
        cmds.keyframe(self.transform, relative=True, timeChange=int(offset))

    def snap_to_another_camera(self, camera_to_snap_to: str = "persp") -> None:
        """
        Snap camera to another camera (including position, rotation, focal length and DOF attributes).
        Args:
            camera_to_snap_to (str): A camera transform name

        Returns:
            None
        """
        camera_to_snap_to = self.get(camera_to_snap_to)

        # Snap pos and rot, focal and DOF
        cmds.matchTransform(
            self.transform, camera_to_snap_to.transform, pos=True, rot=True
        )

        self.set_attr("focalLength", camera_to_snap_to.get_attr("focalLength"))
        self.set_attr("depthOfField", camera_to_snap_to.get_attr("depthOfField"))
        self.set_attr("focusDistance", camera_to_snap_to.get_attr("focusDistance"))
        self.set_attr("fStop", camera_to_snap_to.get_attr("fStop"))
        self.set_attr(
            "focusRegionScale", camera_to_snap_to.get_attr("focusRegionScale")
        )

    def set_as_camera_viewport(self, panel: str) -> None:
        """
        Set this camera as the viewport's camera.
        Args:
            panel (str): The model panel (viewport) to edit

        Returns:
            None
        """
        cmds.modelEditor(panel, edit=True, camera=self.shape)

    def hide(self):
        """
        Hide the camera in the viewport.
        """
        # Hide on the camera shape because the camera transform might have keyframes.
        cmds.setAttr(self.shape + ".visibility", 0)

    def show(self):
        """
        Show the camera in the viewport.
        """
        # Show on the camera shape because the camera transform might have keyframes.
        cmds.setAttr(self.shape + ".visibility", 1)

def get_all_cameras():
    """
    Return all cameras as a list of SequencerCamera objects
    Returns:
        list[:class:`SequencerCamera`] : List of class instances for all the cameras in the scene.
    """
    return [
        SequencerCamera.get(cmds.listRelatives(shape, parent=True)[0])
        for shape in cmds.ls(cameras=True)
    ]
