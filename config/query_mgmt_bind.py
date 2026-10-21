"""Query a Zigbee device Binding Table with ZDO Mgmt_Bind_req.

Run this script inside the same Home Assistant container that owns the ZHA
coordinator. Stop Home Assistant first so this script can open /dev/ha-itead.
It is read-only for the DUT: it sends Mgmt_Bind_req and prints Mgmt_Bind_rsp.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import logging
import sys
import traceback
from typing import Any

import zigpy.types as t
from zigpy.config import CONF_DATABASE, CONF_DEVICE, CONF_DEVICE_BAUDRATE, CONF_DEVICE_PATH
from zigpy.zdo.types import ZDOCmd
from zigpy_znp.zigbee.application import ControllerApplication

DEFAULT_DATABASE = "/config/zigbee.db"
DEFAULT_SERIAL = "/dev/ha-itead"
DEFAULT_BAUDRATE = 115200
DEFAULT_DUT_IEEE = "a4:c1:38:3d:c5:87:18:b3"


def _format_ieee(value: Any) -> str:
    """Return a readable IEEE address for decoded zigpy values."""
    try:
        return str(value)
    except Exception:  # pragma: no cover - diagnostic best effort only
        return repr(value)


def _format_nwk(value: int | None) -> str:
    """Return a readable NWK address without hiding missing values."""
    if value is None:
        return "unknown"
    return f"0x{int(value):04X}"


def _extract_bind_entries(response: Any) -> list[Any]:
    """Best-effort extraction of binding records across zigpy versions."""
    if response is None:
        return []

    candidates: list[Any] = []

    if hasattr(response, "binding_table_list"):
        candidates.append(getattr(response, "binding_table_list"))
    if hasattr(response, "binding_table"):
        candidates.append(getattr(response, "binding_table"))
    if hasattr(response, "records"):
        candidates.append(getattr(response, "records"))

    if isinstance(response, (tuple, list)):
        candidates.extend(response)

    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, (bytes, bytearray, str)):
            continue
        try:
            items = list(candidate)
        except TypeError:
            continue
        if items and not all(isinstance(item, int) for item in items):
            return items

    return []


def _print_bind_entry(index: int, entry: Any) -> None:
    """Print one binding table entry using known zigpy field names when present."""
    print(f"  Entry[{index}]: {entry!r}")

    field_names = (
        "SrcAddress",
        "SrcEndpoint",
        "ClusterId",
        "DstAddrMode",
        "DstAddress",
        "DstEndpoint",
        "src_address",
        "src_endpoint",
        "cluster_id",
        "dst_addr_mode",
        "dst_address",
        "dst_endpoint",
    )

    for name in field_names:
        if hasattr(entry, name):
            print(f"    {name}: {getattr(entry, name)!r}")


def _print_response_summary(response: Any) -> None:
    """Print decoded Mgmt_Bind_rsp details in a human-checkable form."""
    print("\nRaw Mgmt_Bind_rsp object:")
    print(repr(response))

    print("\nDecoded fields, if available:")
    for name in (
        "Status",
        "BindingTableEntries",
        "StartIndex",
        "BindingTableListCount",
        "binding_table_entries",
        "start_index",
        "binding_table_list_count",
    ):
        if hasattr(response, name):
            print(f"  {name}: {getattr(response, name)!r}")

    if isinstance(response, (tuple, list)):
        for index, item in enumerate(response):
            print(f"  response[{index}]: {item!r}")

    entries = _extract_bind_entries(response)
    print(f"\nExtracted binding entries: {len(entries)}")
    for index, entry in enumerate(entries):
        _print_bind_entry(index, entry)

    if not entries:
        print("\nRESULT: No binding entries extracted. Check Ubiqua Mgmt_Bind_rsp for list_count=0.")
    else:
        print("\nRESULT: Binding entries present. Check for Cluster ID 0x0201 and coordinator destination.")


async def _new_controller(config: dict[str, Any]) -> ControllerApplication:
    """Create a zigpy-znp controller across known zigpy API signatures."""
    new_sig = inspect.signature(ControllerApplication.new)
    kwargs: dict[str, Any] = {}

    if "auto_form" in new_sig.parameters:
        kwargs["auto_form"] = False
    if "start_radio" in new_sig.parameters:
        kwargs["start_radio"] = True

    # In current Home Assistant/zigpy, ControllerApplication.new() already
    # starts the radio. Calling startup() a second time can leave zigpy-znp with
    # self._znp cleared, which later breaks send_packet().
    return await ControllerApplication.new(config, **kwargs)


async def query_binding_table(args: argparse.Namespace) -> int:
    """Send Mgmt_Bind_req(start_index) to the selected DUT and print the response."""
    dut_ieee = t.EUI64.convert(args.ieee)
    config = {
        CONF_DEVICE: {
            CONF_DEVICE_PATH: args.serial,
            CONF_DEVICE_BAUDRATE: args.baudrate,
        },
        CONF_DATABASE: args.database,
    }

    app = await _new_controller(config)
    try:
        device = app.get_device(dut_ieee)
        # zigpy devices restored from the standalone database can lack the live
        # controller back-reference; reattach it before issuing a ZDO request.
        if getattr(device, "_application", None) is None:
            device._application = app
        print(f"DUT IEEE: {_format_ieee(device.ieee)}")
        print(f"DUT NWK : {_format_nwk(getattr(device, 'nwk', None))}")
        print(f"Device application attached: {getattr(device, '_application', None) is app}")
        print(f"ZDO device attached: {getattr(device.zdo, '_device', None) is device}")
        print(f"Sending ZDO Mgmt_Bind_req start_index={args.start_index} ...")
        print(f"ZDO request cluster: 0x{int(ZDOCmd.Mgmt_Bind_req):04X}")

        response = await device.zdo.Mgmt_Bind_req(args.start_index)
        _print_response_summary(response)
        return 0
    finally:
        if hasattr(app, "shutdown"):
            await app.shutdown()


def parse_args() -> argparse.Namespace:
    """Parse CLI options for repeatable local certification checks."""
    parser = argparse.ArgumentParser(description="Query DUT binding table via ZDO Mgmt_Bind_req")
    parser.add_argument("--ieee", default=DEFAULT_DUT_IEEE, help="DUT IEEE address")
    parser.add_argument("--serial", default=DEFAULT_SERIAL, help="Coordinator serial path inside container")
    parser.add_argument("--baudrate", default=DEFAULT_BAUDRATE, type=int, help="Coordinator serial baudrate")
    parser.add_argument("--database", default=DEFAULT_DATABASE, help="ZHA zigpy database path inside container")
    parser.add_argument("--start-index", default=0, type=int, help="Mgmt_Bind_req start index")
    parser.add_argument("--debug", action="store_true", help="Enable zigpy debug logging")
    return parser.parse_args()


def main() -> int:
    """Program entry point with concise error reporting for lab use."""
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    try:
        return asyncio.run(query_binding_table(args))
    except KeyError:
        print(
            "ERROR: DUT IEEE is not in zigbee.db. Pair the device with this HA/ZHA network first, "
            "then run the script again.",
            file=sys.stderr,
        )
        return 2
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
