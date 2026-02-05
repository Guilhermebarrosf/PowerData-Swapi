import json
import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import main as main


class FakeRequest:
    def __init__(self, method="GET", args=None):
        self.method = method
        self.args = args or {}


def test_method_not_allowed():
    req = FakeRequest(method="POST", args={})
    body, status, _ = main.swapi(req)
    assert status == 405
    data = json.loads(body)
    assert data["success"] is False
    assert data["error"]["code"] == "METHOD_NOT_ALLOWED"


def test_invalid_resource():
    req = FakeRequest(args={"resource": "abc"})
    body, status, _ = main.swapi(req)
    assert status == 400
    data = json.loads(body)
    assert data["success"] is False


def test_invalid_limit():
    req = FakeRequest(args={"resource": "people", "limit": "x"})
    body, status, _ = main.swapi(req)
    assert status == 400
    data = json.loads(body)
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_PARAMS"


def test_related_characters_mock(monkeypatch):
    # mock SWAPI: film + 2 personagens
    film_payload = {
        "title": "A New Hope",
        "characters": [
            "https://swapi.dev/api/people/1/",
            "https://swapi.dev/api/people/2/",
        ],
    }
    person1 = {"name": "Luke Skywalker", "height": "172"}
    person2 = {"name": "C-3PO", "height": "167"}

    def fake_fetch_swapi(url, params):
        if "/films/1/" in url:
            return film_payload, None, None, None
        if "/people/1/" in url:
            return person1, None, None, None
        if "/people/2/" in url:
            return person2, None, None, None
        return None, "NOT_FOUND", 404, "Item not found"

    monkeypatch.setattr(main, "fetch_swapi", fake_fetch_swapi)

    req = FakeRequest(args={
        "resource": "films",
        "id": "1",
        "related": "characters",
        "fields": "name",
        "limit": "2"
    })

    body, status, _ = main.swapi(req)
    assert status == 200

    data = json.loads(body)
    assert data["success"] is True
    assert "item" in data["data"]
    assert len(data["data"]["related"]) == 2
    assert data["data"]["related"][0]["name"] == "Luke Skywalker"
