import json
import os
import time
from netbrain import NetBrain

source = "10.171.68.10"
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

    for gw in nb.get_gateway(source):
        gw = json.loads(gw["payload"])
        print(gw["ip"])
        print(gw["device"])

    t1_stop = time.process_time()
    print(f"\n Took {t1_stop-t1_start :.3f} seconds to complete")


if __name__ == "__main__":
    main()
