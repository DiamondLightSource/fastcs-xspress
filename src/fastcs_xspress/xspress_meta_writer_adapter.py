from fastcs.methods import command
from fastcs_odin.controllers.odin_data.meta_writer import MetaWriterAdapterController


class XspressMetaWriterAdapterController(MetaWriterAdapterController):
    """Custom adapter controller for Xspress"""

    @command()
    async def stop_acquisition(self):
        await self.connection.put("api/0.1/mw/config/stop", True)
