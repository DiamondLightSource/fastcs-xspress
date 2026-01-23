import asyncio
import json
from pathlib import Path

import pytest
from fastcs.connections.ip_connection import IPConnectionSettings
from pytest_mock import MockerFixture

from fastcs_xspress.xspress_adapter_controller import ParamTreeHandler
from fastcs_xspress.xspress_controller import (
    XspressController,
)

_lock = asyncio.Lock()
HERE = Path(__file__).parent


@pytest.mark.asyncio
async def test_xspress_controller_creates_subcontroller(mocker: MockerFixture):
    with (HERE / "input/xspress.json").open() as f:
        response = json.loads(f.read())

    xsp_controller = XspressController(IPConnectionSettings("127.0.0.1", 80))

    connection = mocker.patch.object(xsp_controller, "connection")
    connection.get = mocker.AsyncMock()
    connection.close = mocker.AsyncMock()

    mock_response = mocker.Mock()
    mock_response.json.return_value = response
    connection.get.return_value = response

    await xsp_controller.initialise()

    assert list(xsp_controller.get_sub_controllers().keys()) == ["XSPRESS"]


@pytest.mark.asyncio
async def test_xspress_handler_update_updates_value(mocker: MockerFixture):
    dummy_uri = "subsystem/api/1.8.0/dummy_mode/dummy_uri"
    updater = ParamTreeHandler(dummy_uri)
    controller = mocker.AsyncMock()
    attr = mocker.Mock()

    controller.connection.get.return_value = {"value": 5}

    await updater.update(controller, attr)
    attr.set.assert_called_once_with(5)


@pytest.mark.asyncio
async def test_xspress_handler_update_updates_value_exception(mocker: MockerFixture):
    dummy_uri = "valid/value"
    controller = mocker.AsyncMock()
    attr = mocker.Mock()

    controller.connection.get.return_value = {"not_value": 5}

    error_mock = mocker.patch("fastcs_xspress.xspress_adapter_controller.logging.error")

    await ParamTreeHandler(dummy_uri).update(controller, attr)
    error_mock.assert_called_once_with(
        "Update loop failed for %s:\n%s", "valid/value", mocker.ANY
    )


@pytest.mark.asyncio
async def test_xspress_handler_put(mocker: MockerFixture):
    dummy_uri = "config/num_images"
    controller = mocker.AsyncMock()
    await ParamTreeHandler(dummy_uri).put(controller, mocker.Mock(), 1)
    controller.connection.put.assert_awaited_once_with(dummy_uri, 1)


@pytest.mark.asyncio
async def test_param_tree_handler_put_exception(mocker: MockerFixture):
    controller = mocker.AsyncMock()
    attr = mocker.MagicMock()

    dummy_url = "hdf/frames"

    controller.connection.put.return_value = {"error": "No, you can't do that"}
    error_mock = mocker.patch("fastcs_xspress.xspress_adapter_controller.logging.error")
    await ParamTreeHandler(dummy_url).put(controller, attr, -1)
    error_mock.assert_called_once_with(
        "Put %s = %s failed:\n%s", "hdf/frames", -1, mocker.ANY
    )
