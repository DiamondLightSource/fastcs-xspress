import logging
from dataclasses import dataclass
from typing import Any

from fastcs.attributes import AttrR, AttrRW, AttrW, Handler
from fastcs.datatypes import Bool, Float, Int, String
from fastcs.util import snake_to_pascal
from fastcs_odin.odin_adapter_controller import OdinAdapterController
from fastcs_odin.util import unpack_status_arrays

uri_list = [
    ["status", "scalar_0"],
    ["status", "scalar_1"],
    ["status", "scalar_2"],
    ["status", "scalar_3"],
    ["status", "scalar_4"],
    ["status", "scalar_5"],
    ["status", "scalar_6"],
    ["status", "scalar_7"],
    ["status", "scalar_8"],
    ["status", "dtc"],
    ["status", "inp_est"],
]

types = {"float": Float(), "int": Int(), "bool": Bool(), "str": String()}


class AdapterResponseError(Exception): ...


@dataclass
class ParamTreeHandler(Handler):
    path: str
    update_period: float = 0.2
    allowed_values: dict[int, str] | None = None

    async def put(
        self,
        controller: "OdinAdapterController",
        attr: AttrW[Any],
        value: Any,
    ) -> None:
        try:
            response = await controller.connection.put(self.path, value)
            match response:
                case {"error": error}:
                    raise AdapterResponseError(error)
        except Exception as e:
            logging.error("Put %s = %s failed:\n%s", self.path, value, e)

    async def update(
        self,
        controller: "OdinAdapterController",
        attr: AttrR[Any],
    ) -> None:
        try:
            response = await controller.connection.get(self.path)

            # TODO: This would be nicer if the key was 'value' so we could match
            parameter = "value"
            if parameter not in response:
                raise ValueError(f"{parameter} not found in response:\n{response}")

            value = response.get(parameter)
            await attr.set(value)
        except Exception as e:
            logging.error("Update loop failed for %s:\n%s", self.path, e)


class XspressAdapterController(OdinAdapterController):
    """SubController for an Xspress adapter in an odin control server."""

    def _process_parameters(self):
        self.parameters = unpack_status_arrays(parameter=self.parameters, uri=uri_list)

    def _create_attributes(self):
        """Create controller ``Attributes`` from ``OdinParameters``."""
        for parameter in self.parameters:
            if "writeable" in parameter.metadata and parameter.metadata["writeable"]:
                attr_class = AttrRW
            else:
                attr_class = AttrR

            if parameter.metadata["type"] not in types:
                logging.warning(f"Could not handle parameter {parameter}")
                # this is really something I should handle here
                continue

            allowed = (
                parameter.metadata["allowed_values"]
                if "allowed_values" in parameter.metadata
                else None
            )

            if len(parameter.path) >= 2:
                group = snake_to_pascal(f"{parameter.path[0]}")
            else:
                group = None

            attr_handler = ParamTreeHandler(
                "/".join([self._api_prefix] + parameter.uri),
                update_period=0.2,
                allowed_values=allowed,
            )

            attr = attr_class(
                types[parameter.metadata["type"]],
                handler=attr_handler,
                group=group,
            )

            setattr(self, parameter.name.replace(".", "").replace("-", ""), attr)
