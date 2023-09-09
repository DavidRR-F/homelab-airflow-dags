import requests


def get_geolocation(street, city, state, zip):
    url = "https://nominatim.openstreetmap.org/search"
    payload = {
        "format": "json",
        "street": street,
        "city": city,
        "state": state,
        "postalcode": zip,
    }
    try:
        res = requests.get(url=url, params=payload)
        res = res.json()
        return res[0]["lat"], res[0]["lon"]
    except:
        return None, None
