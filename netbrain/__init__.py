import requests

# Disable SSL certificate verification warnings
requests.packages.urllib3.disable_warnings()


class NetBrain:
    def __init__(self, url, username, password, tenant_name, domain_name, verify=False):
        self.base_url = f"{url}/ServicesAPI/API/V1"
        self.verify = verify

        payload = {
            "username": username,
            "password": password,
        }

        response = requests.get(
            f"{self.base_url}/Session", json=payload, verify=self.verify
        )
        response.raise_for_status()

        # Capture the session token
        self.token = response.json()["token"]
        self.base_headers = {"Token": self.token}

        self.tenant_id = next(
            dict["tenantId"]
            for dict in self.get_tenants()
            if dict["tenantName"] == tenant_name
        )
        self.domain_id = next(
            dict["domainId"]
            for dict in self.get_domains()
            if dict["domainName"] == domain_name
        )
        self.set_current_domain()

    def get_tenants(self):
        response = requests.get(
            f"{self.base_url}/CMDB/Tenants",
            headers=self.base_headers,
            verify=self.verify,
        )
        response.raise_for_status()
        return response.json()["tenants"]

    def get_domains(self):
        response = requests.get(
            f"{self.base_url}/CMDB/Domains",
            params={"tenantid": self.tenant_id},
            headers=self.base_headers,
            verify=self.verify,
        )
        response.raise_for_status()
        return response.json()["domains"]

    def set_current_domain(self):
        payload = {
            "tenantId": self.tenant_id,
            "domainId": self.domain_id,
        }
        response = requests.put(
            f"{self.base_url}/Session/CurrentDomain",
            json=payload,
            headers=self.base_headers,
            verify=self.verify,
        )
        response.raise_for_status()

    def get_gateway(self, src_ip):
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
        }
        headers.update(self.base_headers)
        response = requests.get(
            f"{self.base_url}/CMDB/Path/Gateways",
            params={"ipOrHost": src_ip},
            headers=headers,
            verify=self.verify,
        )
        response.raise_for_status()
        return response.json()["gatewayList"]
