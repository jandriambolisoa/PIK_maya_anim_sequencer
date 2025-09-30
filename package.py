name = "PIK_maya_anim_sequencer"

version = "0.0.1"

authors = [
    "Jeremy Andriambolisoa",
]

description = \
    """
    An alternative for the Maya's Camera Sequencer to create layout sequences.
    """

requires = [
    "python-3+",
    "maya-2026",
    "PIK_maya_quickBlast-0.0.2"
]

uuid = "piktura.PIK_maya_anim_sequencer"

build_command = 'python {root}/build.py {install}'

def commands():
    env.PYTHONPATH.append("{root}/python")
    env.MAYA_MODULE_PATH.append("{root}/python/PIK_maya_anim_sequencer")