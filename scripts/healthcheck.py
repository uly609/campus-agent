from __future__ import annotations

import json
import urllib.request


def main() -> None:
    with urllib.request.urlopen("http://localhost:8000/ready", timeout=3) as response:
        body = json.loads(response.read().decode("utf-8"))
    if body.get("status") != "ready":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

