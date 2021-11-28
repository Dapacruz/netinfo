#!/usr/bin/env python3

import argparse
import json
import os
import time
from netbrain import NetBrain

router_types = ["Cisco", "Palo Alto Networks"]


def import_env(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    else:
        return None


def get_active_gateway(nb, src_ip):
    """Get the active gateway for the source subnet"""
    for gw in nb.get_gateway_list(src_ip):
        gw = json.loads(gw["payload"])

        # Skip if no device key
        if device := gw.get("device"):
            # Strip firewall vsys from hostname
            if "/" in device:
                device = device.split("/")[0]

            device_attrs = nb.get_device_attrs(device)
        else:
            continue

        # Skip unknown routing devices
        if device_attrs["vendor"] not in router_types:
            device_attrs = ""
            continue

        # Skip PAN HA passive member
        if device_attrs["vendor"] == "Palo Alto Networks" and device_attrs["isHA"]:
            if nb.get_pan_ha_state(device_attrs["name"]) == "passive":
                continue

        return device_attrs


def parse_args():
    parser = argparse.ArgumentParser(
        description="Trace route from source to destination"
    )
    parser.add_argument(
        "-s", "--source", metavar="", type=str, required=True, help="Source IP address"
    )
    parser.add_argument(
        "-d",
        "--destination",
        metavar="",
        type=str,
        required=True,
        help="Destination IP address",
    )

    return parser.parse_args()


def main():
    t1_start = time.process_time()

    args = parse_args()

    env = import_env("env.json")

    nb = NetBrain(
        env["netbrain_url"],
        env["netbrain_user"],
        env["netbrain_password"],
        env["tenant_name"],
        env["domain_name"],
    )

    device_attrs = get_active_gateway(nb, args.source)

    print(json.dumps(device_attrs, indent=2, sort_keys=True))

    t1_stop = time.process_time()
    print(f"\n Took {t1_stop-t1_start :.3f} seconds to complete")


if __name__ == "__main__":
    main()
