from __future__ import annotations

import json
import urllib.request


def request(method: str, url: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    health = request("GET", "http://api:8000/health")
    chat = request(
        "POST",
        "http://api:8000/api/v1/chat",
        {"session_id": "smoke", "user_id": "demo-user", "message": "图书馆今天几点关门？"},
    )
    if health.get("status") != "ok" or not chat.get("citations"):
        raise SystemExit("smoke check failed")
    print("smoke passed")


if __name__ == "__main__":
    main()
