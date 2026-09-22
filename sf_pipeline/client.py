from __future__ import annotations

import base64
import json
from pathlib import Path
import urllib.request
from typing import Iterable, List


API_ROOT = "https://www.spritefusion.com/api/v1"


class SpriteFusionClient:
    def __init__(self, api_key: str, user_agent: str = "RNG-Clothing-Generator/2"):
        if not api_key.strip():
            raise ValueError("Sprite Fusion API key is required")
        self.api_key = api_key.strip()
        self.user_agent = user_agent

    def _headers(self, accept: str = "application/json") -> dict:
        return {
            "Authorization": "Bearer " + self.api_key,
            "User-Agent": self.user_agent,
            "Accept": accept,
        }


    def credits(self) -> dict:
        req=urllib.request.Request(
            API_ROOT + "/credits",
            headers=self._headers(),
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())

    def generate(self, body: dict, timeout: int = 240) -> List[dict]:
        data=json.dumps(body).encode()
        headers=self._headers("text/event-stream")
        headers["Content-Type"]="application/json"
        req=urllib.request.Request(
            API_ROOT + "/generate",
            data=data,
            headers=headers,
            method="POST",
        )
        events=[]
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw in resp:
                line=raw.decode("utf-8","replace").strip()
                if not line.startswith("data:"):
                    continue
                payload=line[5:].strip()
                if payload:
                    events.append(json.loads(payload))
        return events


    def download(self, asset_url: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        req=urllib.request.Request(
            asset_url,
            headers=self._headers("image/png,*/*"),
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            destination.write_bytes(resp.read())


def data_url(path: Path) -> str:
    suffix=path.suffix.lower()
    mime="image/png" if suffix==".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()
