import pandas as pd
import xml.etree.ElementTree as ET
import re
import sys
import os
from datetime import datetime, timezone
from collections import defaultdict


def get_namespace(element):
    match = re.match(r'\{.*\}', element.tag)
    return match.group(0) if match else ''


def format_time(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    return f"{date_obj.year:04}/{date_obj.month:02}/{date_obj.day:02} - {date_obj.hour:02}:{date_obj.minute:02}:{date_obj.second:02}"


def to_unix(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return date_obj.timestamp()


def convert_gpx_to_csv(gpx_file, csv_file, sub_per_second=4):
    tree = ET.parse(gpx_file)
    root = tree.getroot()
    namespace = get_namespace(root)

    # Lecture brute des points
    raw = []
    for trk in root.findall(f"{namespace}trk"):
        for trkseg in trk.findall(f"{namespace}trkseg"):
            for trkpt in trkseg.findall(f"{namespace}trkpt"):
                lat = float(trkpt.get("lat"))
                lon = float(trkpt.get("lon"))
                ele_el = trkpt.find(f"{namespace}ele")
                ele = float(ele_el.text) if ele_el is not None else 0.0
                time_el = trkpt.find(f"{namespace}time")
                ts = time_el.text if time_el is not None else None
                raw.append((ts, lat, lon, ele))

    # Regrouper par seconde
    groups = defaultdict(list)
    for ts, lat, lon, ele in raw:
        groups[ts].append((lat, lon, ele))

    sorted_ts = sorted(groups.keys())
    interval = 1.0 / sub_per_second

    rows = []
    for ts in sorted_ts:
        pts = groups[ts]
        avg_lat = sum(p[0] for p in pts) / len(pts)
        avg_lon = sum(p[1] for p in pts) / len(pts)
        unix_base = to_unix(ts)
        utc_str = format_time(ts)

        for i in range(sub_per_second):
            sub_unix = unix_base - 1.0 + (i + 1) * interval
            alt = pts[i][2] if i < len(pts) else sum(p[2] for p in pts) / len(pts)
            rows.append({
                "Timestamp": sub_unix,
                "UTC": utc_str,
                "Latitude": avg_lat,
                "Longitude": avg_lon,
                "Altitude": alt
            })

    df = pd.DataFrame(rows, columns=["Timestamp", "UTC", "Latitude", "Longitude", "Altitude"])
    df.to_csv(csv_file, index=False)
    print(f"Conversion terminée ! {len(df)} lignes enregistrées → {csv_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python3 postprocessing/conversion_gpx.py <fichier.gpx> [fichier.csv]")
        sys.exit(1)

    gpx_file = sys.argv[1]

    if len(sys.argv) >= 3:
        csv_file = sys.argv[2]
    else:
        base = os.path.splitext(gpx_file)[0]
        csv_file = base + ".csv"

    convert_gpx_to_csv(gpx_file, csv_file)