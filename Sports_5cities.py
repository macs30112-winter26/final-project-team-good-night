### The author is Yuxuan Gou (Rebecca). Team members: Yuxuan Gou and Shoshana Abikzer.


# 1 Introduction

"""This script collects data from the Gaode (Amap) Places API. It counts sports facilitites POIs at the district/county level in Beijing, 
Chengdu, Suzhou, Shanghai, Beijing and Shenzhen."""

# 2 AI use
"""I ran into the Amap (Gaode) Places API limit (max 10 pages × 20 results), 
which can truncate POIs in dense areas, so I used a simple spatial splitting approach: 
for each district/county area, I divided the search box into smaller grids, queried each grid separately, 
and then merged the outputs while de-duplicating POIs by unique POI ID; 
I used AI only to debug my own code and to learn this general tiling + deduplication strategy. 
I did not use AI to generate any code, explanations, or text for this project."""


API_KEY = "f8bbef4167b8979cf7995f3448005a12"

### Shenzhen
import os
import time
import math
import requests
import pandas as pd


CITY_LABEL = "Shenzhen"
CITY_CN = "深圳市"

# Use parent type only 
TYPECODES = ["080100"]

# Throttling
SLEEP_EACH_CALL = 0.20

# Paging
OFFSET = 25          # keep <= 25 to be safe
PAGE_LIMIT = 100     # hard cap

# Quadtree splitting
THRESHOLD = 180      # if count > THRESHOLD, split further
MAX_DEPTH = 8        # recursion depth cap
MIN_LON_SPAN = 0.002 # stop splitting when bbox width is tiny
MIN_LAT_SPAN = 0.002 # stop splitting when bbox height is tiny


# =========================
# HTTP helper
# =========================
def amap_get_json(session, url, params, retries=6, backoff_base=1.5):
    """GET JSON with retries + exponential backoff."""
    last = None
    for i in range(retries):
        try:
            r = session.get(url, params=params, timeout=(10, 30))
            r.raise_for_status()
            js = r.json()
            if js.get("status") == "1":
                return js
            last = js
        except Exception as e:
            last = {"status": "0", "info": repr(e)}
        time.sleep(backoff_base ** (i + 1))
    return last


# =========================
# District list + boundary
# =========================
def list_districts_of_city(session, city_cn):
    """List district-level (区/县) nodes for a given city name."""
    url = "https://restapi.amap.com/v3/config/district"
    params = {
        "key": API_KEY,
        "keywords": city_cn,
        "subdistrict": 2,
        "extensions": "base",
        "offset": 50,
        "page": 1,
    }
    js = amap_get_json(session, url, params)
    ds = js.get("districts", [])
    if not ds:
        raise RuntimeError(f"district api failed for {city_cn}: {js}")

    root = ds[0]
    out = []
    stack = [root]
    seen = set()

    while stack:
        node = stack.pop()
        for ch in (node.get("districts", []) or []):
            lvl = ch.get("level")
            name = ch.get("name")
            adcode = ch.get("adcode")

            if lvl == "district" and adcode and adcode not in seen:
                seen.add(adcode)
                out.append((name, adcode))
            else:
                if ch.get("districts"):
                    stack.append(ch)

    out = sorted(out, key=lambda x: x[1])
    if not out:
        raise RuntimeError(f"no district-level nodes found for {city_cn}")
    return out


def fetch_polyline(session, adcode):
    """Fetch boundary polyline for an administrative adcode."""
    url = "https://restapi.amap.com/v3/config/district"
    params = {
        "key": API_KEY,
        "keywords": adcode,
        "subdistrict": 0,
        "extensions": "all",
    }
    js = amap_get_json(session, url, params)
    ds = js.get("districts", [])
    if not ds:
        return ""
    return ds[0].get("polyline", "") or ""


# =========================
# Polyline -> rings + bbox
# =========================
def polyline_to_rings(polyline):
    """
    Convert AMap polyline to polygon rings.
    - polyline: points separated by ';', multi-part separated by '|'
    - return: list of rings, each ring is [(lon, lat), ...] and closed.
    """
    if not polyline:
        return []

    rings = []
    for part in polyline.split("|"):
        pts = []
        for s in part.split(";"):
            if not s:
                continue
            try:
                lon, lat = s.split(",")
                pts.append((float(lon), float(lat)))
            except Exception:
                continue

        if len(pts) < 3:
            continue

        # Close ring
        if pts[0] != pts[-1]:
            pts.append(pts[0])
        rings.append(pts)

    return rings


def rings_to_bbox(rings):
    """Compute bbox from rings."""
    min_lon = min_lat = float("inf")
    max_lon = max_lat = float("-inf")

    for ring in rings:
        for lon, lat in ring:
            min_lon = min(min_lon, lon)
            max_lon = max(max_lon, lon)
            min_lat = min(min_lat, lat)
            max_lat = max(max_lat, lat)

    if min_lon == float("inf"):
        return None

    return {"min_lon": min_lon, "max_lon": max_lon, "min_lat": min_lat, "max_lat": max_lat}


# Point-in-polygon (ray casting)
def point_in_ring(lon, lat, ring):
    """
    Ray casting algorithm for a single closed ring.
    Assumes ring is a list of (lon, lat) and ring[0] == ring[-1].
    """
    inside = False
    n = len(ring)
    if n < 4:
        return False

    x, y = lon, lat
    for i in range(n - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]

        # Check if ray crosses the segment
        cond = ((y1 > y) != (y2 > y))
        if cond:
            # Compute x coordinate of intersection
            x_int = x1 + (y - y1) * (x2 - x1) / (y2 - y1 + 1e-30)
            if x_int > x:
                inside = not inside
    return inside


def point_in_any_ring(lon, lat, rings):
    """Return True if point is inside any ring (MultiPolygon without holes)."""
    for ring in rings:
        if point_in_ring(lon, lat, ring):
            return True
    return False


# Quadtree helpers

def rect_polygon_str(b):
    """AMap rectangle polygon uses left-top + right-bottom."""
    return f"{b['min_lon']},{b['max_lat']}|{b['max_lon']},{b['min_lat']}"


def split_bbox_2x2(b):
    """Split a bbox into 4 equal sub-bboxes."""
    mid_lon = (b["min_lon"] + b["max_lon"]) / 2.0
    mid_lat = (b["min_lat"] + b["max_lat"]) / 2.0

    return [
        {"min_lon": b["min_lon"], "max_lon": mid_lon, "min_lat": mid_lat, "max_lat": b["max_lat"]},  # NW
        {"min_lon": mid_lon, "max_lon": b["max_lon"], "min_lat": mid_lat, "max_lat": b["max_lat"]},  # NE
        {"min_lon": b["min_lon"], "max_lon": mid_lon, "min_lat": b["min_lat"], "max_lat": mid_lat},  # SW
        {"min_lon": mid_lon, "max_lon": b["max_lon"], "min_lat": b["min_lat"], "max_lat": mid_lat},  # SE
    ]


def bbox_too_small(b):
    """Stop splitting when bbox is already very small."""
    return (b["max_lon"] - b["min_lon"] <= MIN_LON_SPAN) or (b["max_lat"] - b["min_lat"] <= MIN_LAT_SPAN)


def polygon_count_only(session, bbox, typecode, city=None):
    """Fast count query used for splitting decision."""
    url = "https://restapi.amap.com/v3/place/polygon"
    polygon = rect_polygon_str(bbox)
    params = {
        "key": API_KEY,
        "types": typecode,
        "polygon": polygon,
        "offset": 1,
        "page": 1,
        "extensions": "base",
    }
    if city:
        params["city"] = city

    js = amap_get_json(session, url, params)
    time.sleep(SLEEP_EACH_CALL)

    if not isinstance(js, dict) or js.get("status") != "1":
        return 0, js.get("infocode") if isinstance(js, dict) else None, js.get("info") if isinstance(js, dict) else None

    try:
        return int(js.get("count", "0")), js.get("infocode"), js.get("info")
    except Exception:
        return 0, js.get("infocode"), js.get("info")


def fetch_polygon_pois(session, bbox, typecode, city=None):
    """
    Fetch POIs for a bbox (rectangle polygon) by paging.
    Assumes bbox is not too dense after splitting.
    """
    url = "https://restapi.amap.com/v3/place/polygon"
    polygon = rect_polygon_str(bbox)

    out = []
    for page in range(1, PAGE_LIMIT + 1):
        params = {
            "key": API_KEY,
            "types": typecode,
            "polygon": polygon,
            "offset": OFFSET,
            "page": page,
            "extensions": "base",
        }
        if city:
            params["city"] = city

        js = amap_get_json(session, url, params)
        time.sleep(SLEEP_EACH_CALL)

        pois = (js.get("pois") or []) if isinstance(js, dict) and js.get("status") == "1" else []
        if not pois:
            break

        out.extend(pois)

        # If fewer than OFFSET returned, likely last page
        if len(pois) < OFFSET:
            break

    return out


def collect_pois_quadtree(
    session,
    bbox,
    typecode,
    rings,
    city=None,
    district=None,
    depth=0,
    grid_path="R",
    id_map=None,
    debug=False
):
    """
    Quadtree splitting:
      - if count > THRESHOLD or count == 1000 => split bbox into 4 and recurse
      - else => fetch pois and add unique ids (filtered by district boundary rings)
    """
    if id_map is None:
        id_map = {}  # poi_id -> row dict (keeps 1 copy)

    count, infocode, info = polygon_count_only(session, bbox, typecode, city=city)

    if debug:
        print(
            f"{district} | type={typecode} | depth={depth} | path={grid_path} | "
            f"count={count} | infocode={infocode} | span=({bbox['max_lon']-bbox['min_lon']:.4f},{bbox['max_lat']-bbox['min_lat']:.4f})"
        )

    if count <= 0:
        return id_map

    should_split = (count > THRESHOLD) or (count >= 1000)
    if should_split and depth < MAX_DEPTH and (not bbox_too_small(bbox)):
        for idx, child in enumerate(split_bbox_2x2(bbox), start=1):
            collect_pois_quadtree(
                session=session,
                bbox=child,
                typecode=typecode,
                rings=rings,
                city=city,
                district=district,
                depth=depth + 1,
                grid_path=f"{grid_path}.{idx}",
                id_map=id_map,
                debug=debug
            )
        return id_map

    # Fetch POIs for this bbox, then filter by district polygon
    pois = fetch_polygon_pois(session, bbox, typecode, city=city)
    for p in pois:
        pid = p.get("id")
        loc = p.get("location")
        if (not pid) or (pid in id_map) or (not loc):
            continue

        try:
            lon_str, lat_str = loc.split(",")
            lon = float(lon_str)
            lat = float(lat_str)
        except Exception:
            continue

        # Keep only POIs truly inside the district boundary
        if not point_in_any_ring(lon, lat, rings):
            continue

        id_map[pid] = {
            "city": CITY_LABEL,
            "district": district,
            "poi_id": pid,
            "poi_name": p.get("name"),
            "type": p.get("type"),
            "typecode": p.get("typecode"),
            "longitude": lon,
            "latitude": lat,
            "query_typecode": typecode,
            "grid_path": grid_path,
        }

    return id_map



# Main runner

def run_city_quadtree(out_summary_xlsx="shenzhen_sport_summary_quadtree.xlsx",
                      out_poi_xlsx="shenzhen_sport_pois_quadtree.xlsx",
                      debug_first_n=0):
    summary_rows = []
    poi_rows_all = []

    with requests.Session() as session:
        districts = list_districts_of_city(session, CITY_CN)

        for idx, (district_name, adcode) in enumerate(districts):
            print("\n" + "=" * 60)
            print(f"Processing: {CITY_LABEL}-{district_name} (adcode={adcode})")

            polyline = fetch_polyline(session, adcode)
            rings = polyline_to_rings(polyline)
            if not rings:
                print("  WARNING: no rings found, skip.")
                continue

            bbox = rings_to_bbox(rings)
            if not bbox:
                print("  WARNING: bbox failed, skip.")
                continue

            debug = idx < debug_first_n
            id_map = {}

            for tc in TYPECODES:
                collect_pois_quadtree(
                    session=session,
                    bbox=bbox,
                    typecode=tc,
                    rings=rings,
                    city=CITY_CN,
                    district=district_name,
                    depth=0,
                    grid_path="R",
                    id_map=id_map,
                    debug=debug
                )

            # Convert id_map to rows
            district_pois = list(id_map.values())
            poi_rows_all.extend(district_pois)

            summary_rows.append({
                "city": CITY_LABEL,
                "district": district_name,
                "adcode": adcode,
                "sport_facility_count": len(id_map),
                "polygon_parts": len(rings),
                "bbox_span_lon": bbox["max_lon"] - bbox["min_lon"],
                "bbox_span_lat": bbox["max_lat"] - bbox["min_lat"],
            })

            print(f"Done {district_name}: unique={len(id_map)}")

    df_poi = pd.DataFrame(poi_rows_all)
    df_sum = pd.DataFrame(summary_rows).sort_values(["city", "district"]).reset_index(drop=True)

    df_sum.to_excel(out_summary_xlsx, index=False)
    df_poi.to_excel(out_poi_xlsx, index=False)
    print(f"\nSAVED: {out_summary_xlsx}")
    print(f"SAVED: {out_poi_xlsx}")

    return df_sum, df_poi


if __name__ == "__main__":
    run_city_quadtree(debug_first_n=0)








###### The other citites
import os
import time
import math
import requests
import pandas as pd

# =========================
# Multi-city runner (AMap)
# - District boundary polyline (official)
# - BBox from polyline (candidate region)
# - Quadtree split for dense tiles
# - Fetch POI list, deduplicate by poi_id
# - Point-in-polygon filter to keep POIs truly inside the district

# Cities to run
CITY_LIST = [
    ("Suzhou", "苏州市"),
    ("Shanghai", "上海市"),
    ("Chengdu", "成都市"),
    ("Beijing", "北京市"),
]

# Use parent type only (recommended for quadtree + dedup)
TYPECODES = ["080100"]  # sports venues parent

# Throttling
SLEEP_EACH_CALL = 0.20

# Paging
OFFSET = 25          # keep <= 25
PAGE_LIMIT = 100     # hard cap

# Quadtree splitting
THRESHOLD = 180
MAX_DEPTH = 8
MIN_LON_SPAN = 0.002
MIN_LAT_SPAN = 0.002


# HTTP helper
def amap_get_json(session, url, params, retries=6, backoff_base=1.5):
    """GET JSON with retries + exponential backoff."""
    last = None
    for i in range(retries):
        try:
            r = session.get(url, params=params, timeout=(10, 30))
            r.raise_for_status()
            js = r.json()
            if js.get("status") == "1":
                return js
            last = js
        except Exception as e:
            last = {"status": "0", "info": repr(e)}
        time.sleep(backoff_base ** (i + 1))
    return last


# District list + boundary
def list_districts_of_city(session, city_cn):
    """List district-level nodes for a given city name."""
    url = "https://restapi.amap.com/v3/config/district"
    params = {
        "key": API_KEY,
        "keywords": city_cn,
        "subdistrict": 2,
        "extensions": "base",
        "offset": 50,
        "page": 1,
    }
    js = amap_get_json(session, url, params)
    ds = js.get("districts", [])
    if not ds:
        raise RuntimeError(f"district api failed for {city_cn}: {js}")

    root = ds[0]
    out = []
    stack = [root]
    seen = set()

    # DFS through nested admin tree
    while stack:
        node = stack.pop()
        for ch in (node.get("districts", []) or []):
            lvl = ch.get("level")
            name = ch.get("name")
            adcode = ch.get("adcode")

            if lvl == "district" and adcode and adcode not in seen:
                seen.add(adcode)
                out.append((name, adcode))
            else:
                if ch.get("districts"):
                    stack.append(ch)

    out = sorted(out, key=lambda x: x[1])
    if not out:
        raise RuntimeError(f"no district-level nodes found for {city_cn}")
    return out


def fetch_polyline(session, adcode):
    """Fetch boundary polyline for an administrative adcode."""
    url = "https://restapi.amap.com/v3/config/district"
    params = {
        "key": API_KEY,
        "keywords": adcode,
        "subdistrict": 0,
        "extensions": "all",
    }
    js = amap_get_json(session, url, params)
    ds = js.get("districts", [])
    if not ds:
        return ""
    return ds[0].get("polyline", "") or ""


# Polyline -> rings + bbox
def polyline_to_rings(polyline):
    """
    Convert AMap polyline to polygon rings.
    - points separated by ';'
    - multi-part separated by '|'
    """
    if not polyline:
        return []

    rings = []
    for part in polyline.split("|"):
        pts = []
        for s in part.split(";"):
            if not s:
                continue
            try:
                lon, lat = s.split(",")
                pts.append((float(lon), float(lat)))
            except Exception:
                continue

        if len(pts) < 3:
            continue

        if pts[0] != pts[-1]:
            pts.append(pts[0])
        rings.append(pts)

    return rings


def rings_to_bbox(rings):
    """Compute bbox from rings."""
    min_lon = min_lat = float("inf")
    max_lon = max_lat = float("-inf")

    for ring in rings:
        for lon, lat in ring:
            min_lon = min(min_lon, lon)
            max_lon = max(max_lon, lon)
            min_lat = min(min_lat, lat)
            max_lat = max(max_lat, lat)

    if min_lon == float("inf"):
        return None

    return {"min_lon": min_lon, "max_lon": max_lon, "min_lat": min_lat, "max_lat": max_lat}


# Point-in-polygon (ray casting)
def point_in_ring(lon, lat, ring):
    """Ray casting for a single closed ring."""
    inside = False
    n = len(ring)
    if n < 4:
        return False

    x, y = lon, lat
    for i in range(n - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]

        cond = ((y1 > y) != (y2 > y))
        if cond:
            x_int = x1 + (y - y1) * (x2 - x1) / (y2 - y1 + 1e-30)
            if x_int > x:
                inside = not inside
    return inside


def point_in_any_ring(lon, lat, rings):
    """True if point is inside any ring (no hole handling)."""
    for ring in rings:
        if point_in_ring(lon, lat, ring):
            return True
    return False


# Quadtree helpers
def rect_polygon_str(b):
    """AMap rectangle polygon uses left-top + right-bottom."""
    return f"{b['min_lon']},{b['max_lat']}|{b['max_lon']},{b['min_lat']}"


def split_bbox_2x2(b):
    """Split bbox into 4 equal sub-bboxes."""
    mid_lon = (b["min_lon"] + b["max_lon"]) / 2.0
    mid_lat = (b["min_lat"] + b["max_lat"]) / 2.0

    return [
        {"min_lon": b["min_lon"], "max_lon": mid_lon, "min_lat": mid_lat, "max_lat": b["max_lat"]},  # NW
        {"min_lon": mid_lon, "max_lon": b["max_lon"], "min_lat": mid_lat, "max_lat": b["max_lat"]},  # NE
        {"min_lon": b["min_lon"], "max_lon": mid_lon, "min_lat": b["min_lat"], "max_lat": mid_lat},  # SW
        {"min_lon": mid_lon, "max_lon": b["max_lon"], "min_lat": b["min_lat"], "max_lat": mid_lat},  # SE
    ]


def bbox_too_small(b):
    """Stop splitting when bbox is already very small."""
    return (b["max_lon"] - b["min_lon"] <= MIN_LON_SPAN) or (b["max_lat"] - b["min_lat"] <= MIN_LAT_SPAN)


def polygon_count_only(session, bbox, typecode, city=None):
    """Count query used for splitting decision."""
    url = "https://restapi.amap.com/v3/place/polygon"
    polygon = rect_polygon_str(bbox)
    params = {
        "key": API_KEY,
        "types": typecode,
        "polygon": polygon,
        "offset": 1,
        "page": 1,
        "extensions": "base",
    }
    if city:
        params["city"] = city

    js = amap_get_json(session, url, params)
    time.sleep(SLEEP_EACH_CALL)

    if not isinstance(js, dict) or js.get("status") != "1":
        return 0, js.get("infocode") if isinstance(js, dict) else None, js.get("info") if isinstance(js, dict) else None

    try:
        return int(js.get("count", "0")), js.get("infocode"), js.get("info")
    except Exception:
        return 0, js.get("infocode"), js.get("info")


def fetch_polygon_pois(session, bbox, typecode, city=None):
    """Fetch POIs for a bbox by paging (assumes bbox is not too dense)."""
    url = "https://restapi.amap.com/v3/place/polygon"
    polygon = rect_polygon_str(bbox)

    out = []
    for page in range(1, PAGE_LIMIT + 1):
        params = {
            "key": API_KEY,
            "types": typecode,
            "polygon": polygon,
            "offset": OFFSET,
            "page": page,
            "extensions": "base",
        }
        if city:
            params["city"] = city

        js = amap_get_json(session, url, params)
        time.sleep(SLEEP_EACH_CALL)

        pois = (js.get("pois") or []) if isinstance(js, dict) and js.get("status") == "1" else []
        if not pois:
            break

        out.extend(pois)

        if len(pois) < OFFSET:
            break

    return out


def collect_pois_quadtree(
    session,
    bbox,
    typecode,
    rings,
    city=None,
    city_label=None,
    district=None,
    adcode=None,
    depth=0,
    grid_path="R",
    id_map=None,
):
    """
    Quadtree splitting:
      - if count > THRESHOLD or count >= 1000: split bbox into 4 and recurse
      - else: fetch pois and add unique ids (filtered by district boundary rings)
    """
    if id_map is None:
        id_map = {}  # poi_id -> row

    count, infocode, info = polygon_count_only(session, bbox, typecode, city=city)

    if count <= 0:
        return id_map

    should_split = (count > THRESHOLD) or (count >= 1000)
    if should_split and depth < MAX_DEPTH and (not bbox_too_small(bbox)):
        for idx, child in enumerate(split_bbox_2x2(bbox), start=1):
            collect_pois_quadtree(
                session=session,
                bbox=child,
                typecode=typecode,
                rings=rings,
                city=city,
                city_label=city_label,
                district=district,
                adcode=adcode,
                depth=depth + 1,
                grid_path=f"{grid_path}.{idx}",
                id_map=id_map,
            )
        return id_map

    # Leaf: fetch POIs and filter by boundary
    pois = fetch_polygon_pois(session, bbox, typecode, city=city)
    for p in pois:
        pid = p.get("id")
        loc = p.get("location")
        if (not pid) or (pid in id_map) or (not loc):
            continue

        try:
            lon_str, lat_str = loc.split(",")
            lon = float(lon_str)
            lat = float(lat_str)
        except Exception:
            continue

        if not point_in_any_ring(lon, lat, rings):
            continue

        id_map[pid] = {
            "city": city_label,
            "district": district,
            "adcode": adcode,
            "poi_id": pid,
            "poi_name": p.get("name"),
            "type": p.get("type"),
            "typecode": p.get("typecode"),
            "longitude": lon,
            "latitude": lat,
            "query_typecode": typecode,
            "grid_path": grid_path,
        }

    return id_map


# Main: run one city
def run_one_city(city_label, city_cn, out_dir="output"):
    os.makedirs(out_dir, exist_ok=True)

    summary_rows = []
    poi_rows_all = []

    with requests.Session() as session:
        districts = list_districts_of_city(session, city_cn)

        for district_name, adcode in districts:
            print("\n" + "=" * 60)
            print(f"Processing: {city_label}-{district_name} (adcode={adcode})")

            polyline = fetch_polyline(session, adcode)
            rings = polyline_to_rings(polyline)
            if not rings:
                print("  WARNING: no rings found, skip.")
                continue

            bbox = rings_to_bbox(rings)
            if not bbox:
                print("  WARNING: bbox failed, skip.")
                continue

            id_map = {}
            for tc in TYPECODES:
                collect_pois_quadtree(
                    session=session,
                    bbox=bbox,
                    typecode=tc,
                    rings=rings,
                    city=city_cn,
                    city_label=city_label,
                    district=district_name,
                    adcode=adcode,
                    depth=0,
                    grid_path="R",
                    id_map=id_map,
                )

            district_pois = list(id_map.values())
            poi_rows_all.extend(district_pois)

            summary_rows.append({
                "city": city_label,
                "district": district_name,
                "adcode": adcode,
                "sport_facility_count": len(id_map),
                "polygon_parts": len(rings),
                "bbox_span_lon": bbox["max_lon"] - bbox["min_lon"],
                "bbox_span_lat": bbox["max_lat"] - bbox["min_lat"],
            })

            print(f"Done {district_name}: unique={len(id_map)}")

    df_poi = pd.DataFrame(poi_rows_all)
    df_sum = pd.DataFrame(summary_rows).sort_values(["city", "district"]).reset_index(drop=True)

    sum_path = os.path.join(out_dir, f"{city_label.lower()}_sport_summary_quadtree.xlsx")
    poi_path = os.path.join(out_dir, f"{city_label.lower()}_sport_pois_quadtree.xlsx")

    df_sum.to_excel(sum_path, index=False)
    df_poi.to_excel(poi_path, index=False)

    print(f"\nSAVED: {sum_path}")
    print(f"SAVED: {poi_path}")

    return df_sum, df_poi


# Main: run all cities
if __name__ == "__main__":
    all_summaries = []
    for city_label, city_cn in CITY_LIST:
        df_sum, df_poi = run_one_city(city_label, city_cn, out_dir="output")
        all_summaries.append(df_sum)

    df_all = pd.concat(all_summaries, ignore_index=True)
    df_all.to_excel("output/all_cities_sport_summary_quadtree.xlsx", index=False)
    print("\nSAVED: output/all_cities_sport_summary_quadtree.xlsx")

















