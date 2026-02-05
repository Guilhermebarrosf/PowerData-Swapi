import requests

class SwapiClient:
    BASE_URL = "https://swapi.dev/api"

    def get(self, resource, params=None, item_id=None):
        if item_id:
            url = f"{self.BASE_URL}/{resource}/{item_id}/"
        else:
            url = f"{self.BASE_URL}/{resource}/"

        response = requests.get(url, params=params, timeout=5)

        if response.status_code == 404:
            return None

        response.raise_for_status()
        return response.json()
