from maya import cmds
from maya import OpenMaya


def main():
    """Execute actions to setup Maya."""

    # Load the Maya plugin 'timeSliderBookmark'
    try:
        loaded, autoload, _ = cmds.pluginInfo(
            "timeSliderBookmark", query=True, settings=True
        )

        if not loaded:
            cmds.loadPlugin("timeSliderBookmark", quiet=True)
        if not autoload:
            cmds.pluginInfo("timeSliderBookmark", edit=True, autoload=True)

        OpenMaya.MGlobal.displayInfo(
            "# PIK_maya_anim_sequencer - Loaded 'timeSliderBookmark' Maya plugin."
        )

    except RuntimeError:
        OpenMaya.MGlobal.displayError(
            "# PIK_maya_anim_sequencer - The Maya plugin 'timeSliderBookmark' failed to load."
        )


# Execute the main function after the loading of the ui.
cmds.evalDeferred(main, lp=True)
