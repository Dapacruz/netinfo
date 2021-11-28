import json
import os
import time
from netbrain import NetBrain

routing_devices = ["Cisco", "Palo Alto Networks"]

source = "10.129.210.250"  # PAN HA
# source = "10.32.162.250"  # PAN standalone
# source = "192.168.40.245"  # Cisco
destination = "192.168.34.120"


def import_env(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    else:
        return None


def main():
    t1_start = time.process_time()

    env = import_env("env.json")

    nb = NetBrain(
        env["netbrain_url"],
        env["netbrain_user"],
        env["netbrain_password"],
        env["tenant_name"],
        env["domain_name"],
    )

    device_attrs = ""
    # Get the active gateway for the source subnet
    for gw in nb.get_gateway_list(source):
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
        if device_attrs["vendor"] not in routing_devices:
            device_attrs = ""
            continue

        # Skip PAN HA passive member
        if device_attrs["vendor"] == "Palo Alto Networks" and device_attrs["isHA"]:
            if nb.get_pan_ha_state(device_attrs["name"]) == "passive":
                continue

        break

    print(device_attrs)

    t1_stop = time.process_time()
    print(f"\n Took {t1_stop-t1_start :.3f} seconds to complete")


if __name__ == "__main__":
    main()
