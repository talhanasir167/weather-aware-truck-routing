#!/usr/bin/env python3
"""Phase 0 spike: how many alternatives does ORS/OSRM return for sample pairs?"""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request

PAIRS = [
    ("Chicago→Detroit", (-87.6298, 41.8781), (-83.0458, 42.3314)),
    ("Dallas→Houston", (-96.7970, 32.7767), (-95.3698, 29.7604)),
    ("Denver→KansasCity", (-104.9903, 39.7392), (-94.5786, 39.0997)),
]


def _ctx() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        return ctx


def osrm_count(o, d) -> int | str:
    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{o[0]},{o[1]};{d[0]},{d[1]}?alternatives=3&overview=false"
    )
    try:
        with urllib.request.urlopen(url, timeout=30, context=_ctx()) as resp:
            data = json.loads(resp.read())
        return len(data.get("routes", []))
    except Exception as exc:
        return f"error:{type(exc).__name__}"


def ors_count(o, d, key: str) -> int | str:
    url = "https://api.openrouteservice.org/v2/directions/driving-hgv/geojson"
    body = json.dumps(
        {
            "coordinates": [[o[0], o[1]], [d[0], d[1]]],
            "alternative_routes": {
                "target_count": 3,
                "share_factor": 0.6,
                "weight_factor": 1.6,
            },
        }
    ).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Authorization": key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30, context=_ctx()) as resp:
            data = json.loads(resp.read())
        return len(data.get("features", []))
    except urllib.error.HTTPError as exc:
        return f"http_{exc.code}"
    except Exception as exc:
        return f"error:{type(exc).__name__}"


def main() -> None:
    key = os.environ.get("ORS_API_KEY", "")
    print("pair | osrm | ors")
    for name, o, d in PAIRS:
        oc = osrm_count(o, d)
        rc = ors_count(o, d, key) if key else "no_key"
        print(f"{name}: OSRM={oc} ORS={rc}")
    print(
        "\nNote: OSRM often returns <3; app uses via-point perturbation to top up. "
        "Set ORS_API_KEY for truck profile + alternative_routes."
    )


if __name__ == "__main__":
    main()
