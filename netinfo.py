#!/usr/bin/env python3

import argparse
import json
import os
import time
from netbrain import NetBrain
from netmiko import ConnectHandler

cwd = os.getcwd()
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

        device_attrs.update({"srcIP": gw["ip"]})

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


def analyze_path(mgmt_ip, src_ip, dst_ip, credentials, vendor):
    """Analyze the path between the source and destination"""

    vendors = {
        "Cisco": {
            "ssh": {
                "device_type": "cisco_ios",
                "host": mgmt_ip,
                "username": credentials["Cisco"]["username"],
                "password": credentials["Cisco"]["password"],
            },
            "ttp_template": fr"{cwd}\cisco.ttp",
            "commands": [
                f"ping {dst_ip} source {src_ip}",
                f"traceroute {dst_ip} source {src_ip}",
            ],
        },
        "Palo Alto Networks": {
            "ssh": {
                "device_type": "paloalto_panos",
                "host": mgmt_ip,
                "username": credentials["Palo Alto Networks"]["username"],
                "password": credentials["Palo Alto Networks"]["password"],
            },
            "ttp_template": fr"{cwd}\pan.ttp",
            "commands": [
                f"ping count 4 source {src_ip} host {dst_ip}",
                f"traceroute source {src_ip} host {dst_ip}",
            ],
        },
    }

    output = list()
    with ConnectHandler(**vendors[vendor]["ssh"]) as net_connect:
        for cmd in vendors[vendor]["commands"]:
            output.append(
                net_connect.send_command_timing(
                    cmd,
                    strip_prompt=True,
                    strip_command=True,
                    use_ttp=False,
                    ttp_template=vendors[vendor]["ttp_template"],
                )
            )

    return output


def main():
    t1_start = time.time()

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
    # print(json.dumps(device_attrs, indent=2, sort_keys=True))

    results = analyze_path(
        device_attrs["mgmtIP"],
        device_attrs["srcIP"],
        args.destination,
        env["credentials"],
        device_attrs["vendor"],
    )
    print("\n".join(results))

    t1_stop = time.time()
    print(f"\n Took {t1_stop-t1_start :.3f} seconds to complete")


if __name__ == "__main__":
    main()
