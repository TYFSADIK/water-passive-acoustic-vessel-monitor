"""Minimal AIS NMEA (!AIVDM) decoder for message types 1/2/3 (position) and 5 (static/voyage).

rtl-ais / AIS-catcher emit NMEA over UDP (default 10110). Multi-fragment
messages (type 5) are reassembled by sequence id.
"""
from dataclasses import dataclass
import socket

SHIP_TYPES = {range(30, 31): "fishing", range(31, 33): "towing", range(36, 37): "sailing", range(37, 38): "pleasure",
              range(40, 50): "high_speed", range(52, 53): "tug", range(60, 70): "passenger", range(70, 80): "cargo",
              range(80, 90): "tanker"}


def ship_class(code: int) -> str:
    for r, name in SHIP_TYPES.items():
        if code in r:
            return name
    return "other"


def _bits(payload: str, fill: int) -> str:
    out = []
    for ch in payload:
        v = ord(ch) - 48
        if v > 40:
            v -= 8
        out.append(format(v, "06b"))
    b = "".join(out)
    return b[:len(b) - fill] if fill else b


def _u(b, s, n):
    return int(b[s:s + n], 2)


def _i(b, s, n):
    v = _u(b, s, n)
    return v - (1 << n) if v & (1 << (n - 1)) else v


def _txt(b, s, n):
    chars = "@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_ !\"#$%&'()*+,-./0123456789:;<=>?"
    return "".join(chars[_u(b, s + i, 6)] for i in range(0, n, 6)).strip("@ ").strip()


def checksum_ok(line: str) -> bool:
    if "*" not in line:
        return False
    body, cs = line[1:].split("*", 1)
    x = 0
    for c in body:
        x ^= ord(c)
    return f"{x:02X}" == cs[:2].upper()


@dataclass
class Position:
    mmsi: int
    lat: float
    lon: float
    sog_kn: float
    cog: float
    heading: int


@dataclass
class Static:
    mmsi: int
    name: str
    ship_type: int
    length_m: int

    @property
    def cls(self):
        return ship_class(self.ship_type)


class Decoder:
    def __init__(self):
        self.frags = {}

    def feed(self, line: str):
        line = line.strip()
        if not line.startswith(("!AIVDM", "!AIVDO")) or not checksum_ok(line):
            return None
        f = line.split(",")
        total, num, seq, payload, fill = int(f[1]), int(f[2]), f[3], f[5], int(f[6].split("*")[0])
        if total > 1:
            self.frags.setdefault(seq, {})[num] = payload
            if len(self.frags[seq]) < total:
                return None
            payload = "".join(self.frags.pop(seq)[i] for i in range(1, total + 1))
        b = _bits(payload, fill)
        t = _u(b, 0, 6)
        if t in (1, 2, 3):
            return Position(_u(b, 8, 30), _i(b, 89, 27) / 600000, _i(b, 61, 28) / 600000,
                            _u(b, 50, 10) / 10, _u(b, 116, 12) / 10, _u(b, 128, 9))
        if t == 5:
            return Static(_u(b, 8, 30), _txt(b, 112, 120), _u(b, 232, 8), _u(b, 240, 9) + _u(b, 249, 9))
        return None


def listen(port=10110):
    """Yield decoded messages from rtl-ais / AIS-catcher UDP output."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", port))
    d = Decoder()
    while True:
        for line in s.recv(4096).decode(errors="ignore").splitlines():
            m = d.feed(line)
            if m:
                yield m
