import asyncio
import json
from pathlib import Path

import pytest
from fastcs.connections.ip_connection import IPConnectionSettings
from fastcs_odin.util import create_odin_parameters
from pytest_mock import MockerFixture

from fastcs_xspress.xspress_adapter_controller import XspressAdapterController
from fastcs_xspress.xspress_controller import XspressController

_lock = asyncio.Lock()
HERE = Path(__file__).parent


@pytest.mark.asyncio
async def test_xspress_controller_creates_subcontroller(mocker: MockerFixture):
    xsp_controller = XspressController(IPConnectionSettings("127.0.0.1", 80))

    connection = mocker.patch.object(xsp_controller, "connection")
    connection.get = mocker.AsyncMock()
    connection.get.return_value = {
        "adapters": ["xspress"],
        "module": {"value": "XspressAdapter"},
    }

    await xsp_controller.initialise()

    assert list(xsp_controller.sub_controllers.keys()) == ["xspress"]
    assert isinstance(
        xsp_controller.sub_controllers["xspress"], XspressAdapterController
    )


@pytest.mark.asyncio
async def test_xspress_parameter_creation():
    with (HERE / "input/xspress.json").open() as f:
        response = json.loads(f.read())

    parameters = create_odin_parameters(response)
    assert len(parameters) == 185
