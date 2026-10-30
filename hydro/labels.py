"""AIS is the labelling machine: every acoustic detection near an AIS ship's closest approach gets its class.

Ships WITHOUT AIS (small boats) become 'unlabelled' detections, which are exactly what
the classifier must learn to handle, so they are kept, not dropped.
"""
import math


def dist_m(lat1, lon1, lat2, lon2):
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    return 6371000 * math.hypot(dlat, dlon)


def cpa_events(tracks, site, max_range_m=1500):
    """tracks: {mmsi: [(t, lat, lon), ...]} -> [{mmsi, t_cpa, range_m}] for ships passing within max_range_m."""
    out = []
    for mmsi, pts in tracks.items():
        best = min(pts, key=lambda p: dist_m(p[1], p[2], *site))
        r = dist_m(best[1], best[2], *site)
        if r <= max_range_m:
            out.append({"mmsi": mmsi, "t_cpa": best[0], "range_m": round(r)})
    return out


def label_detections(detections, cpas, classes, window_s=180):
    """detections: [{t, ...}] -> adds 'label' (AIS class or 'unlabelled') and 'mmsi'."""
    out = []
    for d in detections:
        near = [c for c in cpas if abs(c["t_cpa"] - d["t"]) <= window_s]
        if near:
            c = min(near, key=lambda c: abs(c["t_cpa"] - d["t"]))
            out.append({**d, "mmsi": c["mmsi"], "label": classes.get(c["mmsi"], "other"), "range_m": c["range_m"]})
        else:
            out.append({**d, "mmsi": None, "label": "unlabelled"})
    return out
