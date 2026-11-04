from fastcs.launch import launch

from fastcs_xspress.xspress_controller import XspressController

from . import __version__

launch(controller_classes=[XspressController], version=__version__)
