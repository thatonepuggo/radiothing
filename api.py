import json
import requests
from urllib.parse import quote_plus

HOST = "https://radio.garden/api"

def get_id(url):
    return list(filter(None, url.split('/')))[2]

def _get_req(url):
    return json.loads(requests.get(HOST + url).content)

def all_countries():
    return _get_req("/ara/content/places")

def stations_in_city(id):
    return _get_req("/ara/content/page/" + id)

def station(id):
    return _get_req("/ara/content/channel/" + id)

def listen_url(id):
    return HOST + "/ara/content/listen/" + id + "/channel.mp3"

def search(query):
    return _get_req(f"/search?q={quote_plus(query, safe='')}")