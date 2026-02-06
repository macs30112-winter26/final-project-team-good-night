#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 21:01:00 2026

@author: rebecca
"""

### Created by Yuxuan Gou (Rebecca). Team members: Yuxuan Gou and Shoshana Abikzer.


# 1 Introduction

"""This script collects data from the Gaode (Amap) Places API. It counts sports facilitites POIs at the district/county level in Beijing, 
Chengdu, Suzhou, and Shenzhen (four large cities in China)."""

# 2 AI use
"""I ran into the Amap (Gaode) Places API limit (max 10 pages × 20 results), 
which can truncate POIs in dense areas, so I used a simple spatial splitting approach: 
for each district/county area, I divided the search box into four smaller grids, queried each grid separately, 
and then merged the outputs while de-duplicating POIs by unique POI ID; 
I used AI only to debug my own code and to learn this general tiling + deduplication strategy."""


######### Shenzhen sports

import requests
import time
import pandas as pd

# 1. API KEY
API_KEY = "40a23e0f57d1dce959314462237b3c95"

# 2. Shenzhen district bounding boxes 
SHENZHEN_DISTRICT_BBOX = {
    "福田区":   {"min_lon": 114.02, "max_lon": 114.09, "min_lat": 22.50, "max_lat": 22.56},
    "罗湖区":   {"min_lon": 114.08, "max_lon": 114.18, "min_lat": 22.53, "max_lat": 22.62},
    "南山区":   {"min_lon": 113.88, "max_lon": 114.06, "min_lat": 22.48, "max_lat": 22.60},
    "盐田区":   {"min_lon": 114.20, "max_lon": 114.35, "min_lat": 22.53, "max_lat": 22.66},
    "宝安区":   {"min_lon": 113.78, "max_lon": 114.12, "min_lat": 22.54, "max_lat": 22.86},
    "龙岗区":   {"min_lon": 114.08, "max_lon": 114.45, "min_lat": 22.54, "max_lat": 22.84},
    "龙华区":   {"min_lon": 113.90, "max_lon": 114.10, "min_lat": 22.58, "max_lat": 22.76},
    "坪山区":   {"min_lon": 114.30, "max_lon": 114.47, "min_lat": 22.62, "max_lat": 22.78},
    "光明区":   {"min_lon": 113.83, "max_lon": 114.02, "min_lat": 22.70, "max_lat": 22.86},
    "大鹏新区": {"min_lon": 114.35, "max_lon": 114.62, "min_lat": 22.48, "max_lat": 22.75},
}

# 3. POI type codes for sports facilities
SPORT_TYPES_CORE = ["080100", "080101", "080102", "080103"]
SPORT_TYPES_PUBLIC = ["110101", "110102", "110103"]

# 4. Split a bbox into a grid (2x2 => 4 grids)
def split_bbox(bbox, n=2):
    grids = []
    lon_step = (bbox["max_lon"] - bbox["min_lon"]) / n
    lat_step = (bbox["max_lat"] - bbox["min_lat"]) / n

    for i in range(n):
        for j in range(n):
            grid = {
                "min_lon": bbox["min_lon"] + i * lon_step,
                "max_lon": bbox["min_lon"] + (i + 1) * lon_step,
                "min_lat": bbox["min_lat"] + j * lat_step,
                "max_lat": bbox["min_lat"] + (j + 1) * lat_step
            }
            grids.append(grid)

    return grids

# 5. Query POIs within a polygon bbox (with progress printing)
def query_polygon(polygon_bbox, poi_type, city, district, grid_id, total_grids, sleep_sec=0.2):
    page = 1
    results = []

    polygon = (
        f"{polygon_bbox['min_lon']},{polygon_bbox['min_lat']}|"
        f"{polygon_bbox['max_lon']},{polygon_bbox['max_lat']}"
    )

    while True:
        params = {
            "key": API_KEY,
            "types": poi_type,
            "polygon": polygon,
            "offset": 20,
            "page": page,
            "extensions": "base"
        }

        r = requests.get("https://restapi.amap.com/v3/place/polygon", params=params)
        data = r.json()
        pois = data.get("pois", [])

        print(
            f"{city}-{district} | "
            f"grid {grid_id}/{total_grids} | "
            f"polygon {polygon} | "
            f"type {poi_type} | "
            f"page {page} | "
            f"count {len(pois)}"
        )

        if not pois:
            break

        results.extend(pois)
        page += 1
        time.sleep(sleep_sec)

    return results

# 6. Main runner for a given POI type list (raw + district summary)
def run_shenzhen_sport_resources(poi_types, label):
    poi_rows = []
    summary_rows = []

    for district, bbox in SHENZHEN_DISTRICT_BBOX.items():
        print("\n" + "=" * 40)
        print(f"Processing district: {district} [{label}]")
        print("=" * 40)

        grids = split_bbox(bbox, n=2)
        total_grids = len(grids)
        unique_ids = set()

        # Print grid boundaries
        for idx, g in enumerate(grids, start=1):
            print(
                f"{district} | GRID {idx}/{total_grids} | "
                f"{g['min_lon']},{g['min_lat']} → {g['max_lon']},{g['max_lat']}"
            )

        for grid_id, grid in enumerate(grids, start=1):
            for poi_type in poi_types:
                pois = query_polygon(
                    polygon_bbox=grid,
                    poi_type=poi_type,
                    city="Shenzhen",
                    district=district,
                    grid_id=grid_id,
                    total_grids=total_grids,
                    sleep_sec=1.0
                )

                for p in pois:
                    poi_id = p.get("id")
                    if not poi_id or poi_id in unique_ids:
                        continue

                    unique_ids.add(poi_id)

                    lon, lat = (None, None)
                    if p.get("location"):
                        lon, lat = p["location"].split(",")

                    poi_rows.append({
                        "city": "Shenzhen",
                        "district": district,
                        "grid_id": grid_id,
                        "poi_id": poi_id,
                        "poi_name": p.get("name"),
                        "type": p.get("type"),
                        "typecode": p.get("typecode"),
                        "longitude": lon,
                        "latitude": lat
                    })


        summary_rows.append({
            "city": "Shenzhen",
            "district": district,
            "sport_facility_count": len(unique_ids)
        })

    df_poi = pd.DataFrame(poi_rows)
    df_summary = pd.DataFrame(summary_rows)

    # Rebuild a deduplicated summary from POI_raw (safety check)
    df_summary_rebuilt = (
        df_poi.groupby(["city", "district"])["poi_id"]
        .nunique()
        .reset_index(name="sport_facility_count")
    )

    return df_poi, df_summary, df_summary_rebuilt


if __name__ == "__main__":
    # 1) Run CORE 
    df_poi_core, df_summary_core, df_summary_core_rebuilt = run_shenzhen_sport_resources(
        poi_types=SPORT_TYPES_CORE,
        label="CORE"
    )

    # 2) Run PUBLIC 
    df_poi_public, df_summary_public, df_summary_public_rebuilt = run_shenzhen_sport_resources(
        poi_types=SPORT_TYPES_PUBLIC,
        label="PUBLIC"
    )

    # 3) Merge CORE + PUBLIC summaries into ONE table
    core_sum = df_summary_core_rebuilt.rename(columns={"sport_facility_count": "core_facility_count"})
    public_sum = df_summary_public_rebuilt.rename(columns={"sport_facility_count": "public_facility_count"})

    df_one = core_sum.merge(public_sum, on=["city", "district"], how="outer")

    # Fill missing with 0 
    df_one[["core_facility_count", "public_facility_count"]] = (
        df_one[["core_facility_count", "public_facility_count"]].fillna(0).astype(int)
    )

    # Optional: keep a consistent order
    df_one = df_one.sort_values(["city", "district"]).reset_index(drop=True)

    # 4) Save ONLY ONE Excel
    df_one.to_excel("shenzhen_sport_summary_core_public_one_table.xlsx", index=False)
    
    
    
    
    

######### Beijing sports

import requests
import time
import pandas as pd

# 1. API KEY
API_KEY = "6a959d23bdcb586180ca103a2c6344df"

# 2. Beijing district bounding boxes 
BEIJING_DISTRICT_BBOX = {
    "东城区": {"min_lon": 116.38, "max_lon": 116.45, "min_lat": 39.88, "max_lat": 39.95},
    "西城区": {"min_lon": 116.32, "max_lon": 116.40, "min_lat": 39.88, "max_lat": 39.95},
    "朝阳区": {"min_lon": 116.38, "max_lon": 116.65, "min_lat": 39.85, "max_lat": 40.05},
    "海淀区": {"min_lon": 116.10, "max_lon": 116.45, "min_lat": 39.85, "max_lat": 40.10},
    "丰台区": {"min_lon": 116.20, "max_lon": 116.45, "min_lat": 39.75, "max_lat": 39.95},
    "石景山区": {"min_lon": 116.10, "max_lon": 116.25, "min_lat": 39.85, "max_lat": 39.98},
    "通州区": {"min_lon": 116.60, "max_lon": 116.90, "min_lat": 39.70, "max_lat": 40.00},
    "顺义区": {"min_lon": 116.55, "max_lon": 116.95, "min_lat": 40.00, "max_lat": 40.25},
    "昌平区": {"min_lon": 116.05, "max_lon": 116.50, "min_lat": 40.00, "max_lat": 40.35},
    "大兴区": {"min_lon": 116.20, "max_lon": 116.55, "min_lat": 39.60, "max_lat": 39.85},
    "房山区": {"min_lon": 115.70, "max_lon": 116.20, "min_lat": 39.50, "max_lat": 39.90},
    "门头沟区": {"min_lon": 115.70, "max_lon": 116.10, "min_lat": 39.80, "max_lat": 40.10},
    "平谷区": {"min_lon": 116.90, "max_lon": 117.25, "min_lat": 40.05, "max_lat": 40.25},
    "怀柔区": {"min_lon": 116.35, "max_lon": 116.85, "min_lat": 40.25, "max_lat": 40.60},
    "密云区": {"min_lon": 116.75, "max_lon": 117.20, "min_lat": 40.35, "max_lat": 40.75},
    "延庆区": {"min_lon": 115.85, "max_lon": 116.45, "min_lat": 40.35, "max_lat": 40.75},
}

# 3. POI type codes for sports facilities
SPORT_TYPES_CORE = ["080100", "080101", "080102", "080103"]
SPORT_TYPES_PUBLIC = ["110101", "110102", "110103"]

# 4. Split a bbox into a grid (2x2 => 4 grids)
def split_bbox(bbox, n=2):
    grids = []
    lon_step = (bbox["max_lon"] - bbox["min_lon"]) / n
    lat_step = (bbox["max_lat"] - bbox["min_lat"]) / n

    for i in range(n):
        for j in range(n):
            grid = {
                "min_lon": bbox["min_lon"] + i * lon_step,
                "max_lon": bbox["min_lon"] + (i + 1) * lon_step,
                "min_lat": bbox["min_lat"] + j * lat_step,
                "max_lat": bbox["min_lat"] + (j + 1) * lat_step
            }
            grids.append(grid)

    return grids

# 5. Query POIs within a polygon bbox (with progress printing)
def query_polygon(polygon_bbox, poi_type, city, district, grid_id, total_grids, sleep_sec=0.2):
    page = 1
    results = []

    polygon = (
        f"{polygon_bbox['min_lon']},{polygon_bbox['min_lat']}|"
        f"{polygon_bbox['max_lon']},{polygon_bbox['max_lat']}"
    )

    while True:
        params = {
            "key": API_KEY,
            "types": poi_type,
            "polygon": polygon,
            "offset": 20,
            "page": page,
            "extensions": "base"
        }

        r = requests.get("https://restapi.amap.com/v3/place/polygon", params=params)
        data = r.json()
        pois = data.get("pois", [])

        print(
            f"{city}-{district} | "
            f"grid {grid_id}/{total_grids} | "
            f"polygon {polygon} | "
            f"type {poi_type} | "
            f"page {page} | "
            f"count {len(pois)}"
        )

        if not pois:
            break

        results.extend(pois)
        page += 1
        time.sleep(sleep_sec)

    return results

# 6. Main runner for a given POI type list (raw + district summary)
def run_beijing_sport_resources(poi_types, label):
    poi_rows = []
    summary_rows = []

    for district, bbox in BEIJING_DISTRICT_BBOX.items():
        print("\n" + "=" * 40)
        print(f"Processing district: {district} [{label}]")
        print("=" * 40)

        grids = split_bbox(bbox, n=2)
        total_grids = len(grids)
        unique_ids = set()

        # Print grid boundaries
        for idx, g in enumerate(grids, start=1):
            print(
                f"{district} | GRID {idx}/{total_grids} | "
                f"{g['min_lon']},{g['min_lat']} → {g['max_lon']},{g['max_lat']}"
            )

        for grid_id, grid in enumerate(grids, start=1):
            for poi_type in poi_types:
                pois = query_polygon(
                    polygon_bbox=grid,
                    poi_type=poi_type,
                    city="Beijing",
                    district=district,
                    grid_id=grid_id,
                    total_grids=total_grids,
                    sleep_sec=1.0
                )

                for p in pois:
                    poi_id = p.get("id")
                    if not poi_id or poi_id in unique_ids:
                        continue

                    unique_ids.add(poi_id)

                    lon, lat = (None, None)
                    if p.get("location"):
                        lon, lat = p["location"].split(",")

                    poi_rows.append({
                        "city": "Beijing",
                        "district": district,
                        "grid_id": grid_id,
                        "poi_id": poi_id,
                        "poi_name": p.get("name"),
                        "type": p.get("type"),
                        "typecode": p.get("typecode"),
                        "longitude": lon,
                        "latitude": lat
                    })


        summary_rows.append({
            "city": "Beijing",
            "district": district,
            "sport_facility_count": len(unique_ids)
        })

    df_poi = pd.DataFrame(poi_rows)
    df_summary = pd.DataFrame(summary_rows)

    # Rebuild a deduplicated summary from POI_raw (safety check)
        df_poi.groupby(["city", "district"])["poi_id"]
        .nunique()
        .reset_index(name="sport_facility_count")
    )

    return df_poi, df_summary, df_summary_rebuilt




if __name__ == "__main__":
    # 1) Run CORE 
    df_poi_core, df_summary_core, df_summary_core_rebuilt = run_beijing_sport_resources(
        poi_types=SPORT_TYPES_CORE,
        label="CORE"
    )

    # 2) Run PUBLIC 
    df_poi_public, df_summary_public, df_summary_public_rebuilt = run_beijing_sport_resources(
        poi_types=SPORT_TYPES_PUBLIC,
        label="PUBLIC"
    )

    # 3) Merge CORE + PUBLIC summaries into ONE table
    core_sum = df_summary_core_rebuilt.rename(columns={"sport_facility_count": "core_facility_count"})
    public_sum = df_summary_public_rebuilt.rename(columns={"sport_facility_count": "public_facility_count"})

    df_one = core_sum.merge(public_sum, on=["city", "district"], how="outer")

    # Fill missing with 0 (in case some district has none in one category)
    df_one[["core_facility_count", "public_facility_count"]] = (
        df_one[["core_facility_count", "public_facility_count"]].fillna(0).astype(int)
    )

    # 3.5) Build ALL (CORE + PUBLIC, deduplicated)
    df_poi_all = pd.concat([df_poi_core, df_poi_public], ignore_index=True)

    # Deduplicate POIs that appear in both CORE and PUBLIC
    # (AMap POI "id" is globally unique, so this is safe)
    df_poi_all = df_poi_all.drop_duplicates(subset=["poi_id"]).reset_index(drop=True)

    # District-level ALL count (deduplicated)
    df_all_rebuilt = (
        df_poi_all.groupby(["city", "district"])["poi_id"]
        .nunique()
        .reset_index(name="all_facility_count")
    )

    # Merge ALL count into the final summary table
    df_one = df_one.merge(df_all_rebuilt, on=["city", "district"], how="outer")
    df_one["all_facility_count"] = df_one["all_facility_count"].fillna(0).astype(int)

    # Optional: keep a consistent order
    df_one = df_one.sort_values(["city", "district"]).reset_index(drop=True)

    # 4) Save ONLY ONE Excel
    df_one.to_excel("beijing_sport_summary_core_public_all_one_table.xlsx", index=False)







######### Chengdu sports

import requests
import time
import pandas as pd

# ======================
# 1. API KEY
# ======================
API_KEY = "6a959d23bdcb586180ca103a2c6344df"

# ======================
# 2. Chengdu district bounding boxes (research-grade approximations)
# ======================
CHENGDU_DISTRICT_BBOX = {
    # 5 central urban districts
    "锦江区":   {"min_lon": 104.05, "max_lon": 104.15, "min_lat": 30.57, "max_lat": 30.68},
    "青羊区":   {"min_lon": 103.95, "max_lon": 104.05, "min_lat": 30.60, "max_lat": 30.73},
    "金牛区":   {"min_lon": 103.97, "max_lon": 104.10, "min_lat": 30.68, "max_lat": 30.82},
    "武侯区":   {"min_lon": 103.90, "max_lon": 104.08, "min_lat": 30.55, "max_lat": 30.70},
    "成华区":   {"min_lon": 104.10, "max_lon": 104.25, "min_lat": 30.64, "max_lat": 30.80},

    # 7 suburban districts
    "龙泉驿区": {"min_lon": 104.15, "max_lon": 104.45, "min_lat": 30.52, "max_lat": 30.78},
    "青白江区": {"min_lon": 104.10, "max_lon": 104.45, "min_lat": 30.85, "max_lat": 31.15},
    "新都区":   {"min_lon": 103.95, "max_lon": 104.25, "min_lat": 30.75, "max_lat": 31.05},
    "温江区":   {"min_lon": 103.75, "max_lon": 103.98, "min_lat": 30.62, "max_lat": 30.85},
    "双流区":   {"min_lon": 103.85, "max_lon": 104.20, "min_lat": 30.35, "max_lat": 30.65},
    "郫都区":   {"min_lon": 103.75, "max_lon": 104.05, "min_lat": 30.70, "max_lat": 31.00},
    "新津区":   {"min_lon": 103.70, "max_lon": 103.95, "min_lat": 30.28, "max_lat": 30.50},

    # 5 county-level cities
    "都江堰市": {"min_lon": 103.45, "max_lon": 103.85, "min_lat": 30.85, "max_lat": 31.20},
    "彭州市":   {"min_lon": 103.70, "max_lon": 104.25, "min_lat": 30.95, "max_lat": 31.35},
    "邛崃市":   {"min_lon": 103.20, "max_lon": 103.75, "min_lat": 30.25, "max_lat": 30.70},
    "崇州市":   {"min_lon": 103.35, "max_lon": 103.85, "min_lat": 30.35, "max_lat": 30.85},
    "简阳市":   {"min_lon": 104.35, "max_lon": 105.15, "min_lat": 30.20, "max_lat": 30.85},

    # 3 counties
    "金堂县":   {"min_lon": 104.15, "max_lon": 104.85, "min_lat": 30.70, "max_lat": 31.20},
    "大邑县":   {"min_lon": 103.35, "max_lon": 103.85, "min_lat": 30.38, "max_lat": 30.85},
    "蒲江县":   {"min_lon": 103.35, "max_lon": 103.75, "min_lat": 30.10, "max_lat": 30.45},
}

# 3. POI type codes for sports facilities
SPORT_TYPES_CORE = ["080100", "080101", "080102", "080103"]
SPORT_TYPES_PUBLIC = ["110101", "110102", "110103"]

# 4. Split a bbox into a grid (2x2 => 4 grids)
def split_bbox(bbox, n=2):
    grids = []
    lon_step = (bbox["max_lon"] - bbox["min_lon"]) / n
    lat_step = (bbox["max_lat"] - bbox["min_lat"]) / n

    for i in range(n):
        for j in range(n):
            grid = {
                "min_lon": bbox["min_lon"] + i * lon_step,
                "max_lon": bbox["min_lon"] + (i + 1) * lon_step,
                "min_lat": bbox["min_lat"] + j * lat_step,
                "max_lat": bbox["min_lat"] + (j + 1) * lat_step
            }
            grids.append(grid)

    return grids

# 5. Query POIs within a polygon bbox 
def query_polygon(polygon_bbox, poi_type, city, district, grid_id, total_grids, sleep_sec=0.2):
    page = 1
    results = []

    polygon = (
        f"{polygon_bbox['min_lon']},{polygon_bbox['min_lat']}|"
        f"{polygon_bbox['max_lon']},{polygon_bbox['max_lat']}"
    )

    while True:
        params = {
            "key": API_KEY,
            "types": poi_type,
            "polygon": polygon,
            "offset": 20,
            "page": page,
            "extensions": "base"
        }

        r = requests.get("https://restapi.amap.com/v3/place/polygon", params=params)
        data = r.json()
        pois = data.get("pois", [])

        print(
            f"{city}-{district} | "
            f"grid {grid_id}/{total_grids} | "
            f"polygon {polygon} | "
            f"type {poi_type} | "
            f"page {page} | "
            f"count {len(pois)}"
        )

        if not pois:
            break

        results.extend(pois)
        page += 1
        time.sleep(sleep_sec)

    return results

# 6. Main runner for a given POI type list (raw + district summary)
def run_chengdu_sport_resources(poi_types, label):
    poi_rows = []
    summary_rows = []

    for district, bbox in CHENGDU_DISTRICT_BBOX.items():
        print("\n" + "=" * 40)
        print(f"Processing district: {district} [{label}]")
        print("=" * 40)

        grids = split_bbox(bbox, n=2)
        total_grids = len(grids)
        unique_ids = set()

        # Print grid boundaries
        for idx, g in enumerate(grids, start=1):
            print(
                f"{district} | GRID {idx}/{total_grids} | "
                f"{g['min_lon']},{g['min_lat']} → {g['max_lon']},{g['max_lat']}"
            )

        for grid_id, grid in enumerate(grids, start=1):
            for poi_type in poi_types:
                pois = query_polygon(
                    polygon_bbox=grid,
                    poi_type=poi_type,
                    city="Chengdu",
                    district=district,
                    grid_id=grid_id,
                    total_grids=total_grids,
                    sleep_sec=1.0
                )

                for p in pois:
                    poi_id = p.get("id")
                    if not poi_id or poi_id in unique_ids:
                        continue

                    unique_ids.add(poi_id)

                    lon, lat = (None, None)
                    if p.get("location"):
                        lon, lat = p["location"].split(",")

                    poi_rows.append({
                        "city": "Chengdu",
                        "district": district,
                        "grid_id": grid_id,
                        "poi_id": poi_id,
                        "poi_name": p.get("name"),
                        "type": p.get("type"),
                        "typecode": p.get("typecode"),
                        "longitude": lon,
                        "latitude": lat
                    })

        summary_rows.append({
            "city": "Chengdu",
            "district": district,
            "sport_facility_count": len(unique_ids)
        })

    df_poi = pd.DataFrame(poi_rows)
    df_summary = pd.DataFrame(summary_rows)

    # Rebuild a deduplicated summary from POI_raw 
    df_summary_rebuilt = (
        df_poi.groupby(["city", "district"])["poi_id"]
        .nunique()
        .reset_index(name="sport_facility_count")
    )

    return df_poi, df_summary, df_summary_rebuilt








if __name__ == "__main__":
    # 1) Run CORE 
    df_poi_core, df_summary_core, df_summary_core_rebuilt = run_chengdu_sport_resources(
        poi_types=SPORT_TYPES_CORE,
        label="CORE"
    )

    # 2) Run PUBLIC 
    df_poi_public, df_summary_public, df_summary_public_rebuilt = run_chengdu_sport_resources(
        poi_types=SPORT_TYPES_PUBLIC,
        label="PUBLIC"
    )

    # 3) Merge CORE + PUBLIC summaries into ONE table
    core_sum = df_summary_core_rebuilt.rename(columns={"sport_facility_count": "core_facility_count"})
    public_sum = df_summary_public_rebuilt.rename(columns={"sport_facility_count": "public_facility_count"})

    df_one = core_sum.merge(public_sum, on=["city", "district"], how="outer")

    # Fill missing with 0 (in case some district has none in one category)
    df_one[["core_facility_count", "public_facility_count"]] = (
        df_one[["core_facility_count", "public_facility_count"]].fillna(0).astype(int)
    )

    # 3.5) Build ALL (CORE + PUBLIC, deduplicated)
    df_poi_all = pd.concat([df_poi_core, df_poi_public], ignore_index=True)
    df_poi_all = df_poi_all.drop_duplicates(subset=["poi_id"]).reset_index(drop=True)

    df_all_rebuilt = (
        df_poi_all.groupby(["city", "district"])["poi_id"]
        .nunique()
        .reset_index(name="all_facility_count")
    )

    df_one = df_one.merge(df_all_rebuilt, on=["city", "district"], how="outer")
    df_one["all_facility_count"] = df_one["all_facility_count"].fillna(0).astype(int)

    df_one = df_one.sort_values(["city", "district"]).reset_index(drop=True)

    # 4) Save ONLY ONE Excel
    df_one.to_excel("chengdu_sport_summary_core_public_all_one_table.xlsx", index=False)


















################# Shanghai sports


import requests
import time
import pandas as pd

# ======================
# 1. API KEY
# ======================
API_KEY = "40a23e0f57d1dce959314462237b3c95"

# ======================
# 2. Shanghai district bounding boxes 
# ======================
SHANGHAI_DISTRICT_BBOX = {
    # 16 districts
    "黄浦区": {"min_lon": 121.45, "max_lon": 121.52, "min_lat": 31.20, "max_lat": 31.25},
    "徐汇区": {"min_lon": 121.40, "max_lon": 121.50, "min_lat": 31.16, "max_lat": 31.22},
    "长宁区": {"min_lon": 121.36, "max_lon": 121.44, "min_lat": 31.18, "max_lat": 31.24},
    "静安区": {"min_lon": 121.42, "max_lon": 121.49, "min_lat": 31.22, "max_lat": 31.29},
    "普陀区": {"min_lon": 121.36, "max_lon": 121.44, "min_lat": 31.22, "max_lat": 31.29},
    "虹口区": {"min_lon": 121.46, "max_lon": 121.52, "min_lat": 31.25, "max_lat": 31.30},
    "杨浦区": {"min_lon": 121.49, "max_lon": 121.58, "min_lat": 31.25, "max_lat": 31.33},
    "闵行区": {"min_lon": 121.30, "max_lon": 121.60, "min_lat": 31.00, "max_lat": 31.25},
    "宝山区": {"min_lon": 121.30, "max_lon": 121.60, "min_lat": 31.30, "max_lat": 31.50},
    "嘉定区": {"min_lon": 121.10, "max_lon": 121.40, "min_lat": 31.20, "max_lat": 31.45},
    "浦东新区": {"min_lon": 121.50, "max_lon": 121.95, "min_lat": 31.00, "max_lat": 31.35},
    "金山区": {"min_lon": 121.10, "max_lon": 121.40, "min_lat": 30.60, "max_lat": 30.90},
    "松江区": {"min_lon": 121.10, "max_lon": 121.40, "min_lat": 30.90, "max_lat": 31.15},
    "青浦区": {"min_lon": 120.90, "max_lon": 121.20, "min_lat": 31.05, "max_lat": 31.25},
    "奉贤区": {"min_lon": 121.40, "max_lon": 121.80, "min_lat": 30.85, "max_lat": 31.10},
    "崇明区": {"min_lon": 121.25, "max_lon": 121.95, "min_lat": 31.45, "max_lat": 31.85},
}

# 3. POI type codes for sports facilities
SPORT_TYPES_CORE = ["080100", "080101", "080102", "080103"]
SPORT_TYPES_PUBLIC = ["110101", "110102", "110103"]

# 4. Split a bbox into a grid (2x2 => 4 grids)
def split_bbox(bbox, n=2):
    grids = []
    lon_step = (bbox["max_lon"] - bbox["min_lon"]) / n
    lat_step = (bbox["max_lat"] - bbox["min_lat"]) / n

    for i in range(n):
        for j in range(n):
            grid = {
                "min_lon": bbox["min_lon"] + i * lon_step,
                "max_lon": bbox["min_lon"] + (i + 1) * lon_step,
                "min_lat": bbox["min_lat"] + j * lat_step,
                "max_lat": bbox["min_lat"] + (j + 1) * lat_step
            }
            grids.append(grid)

    return grids

# 5. Query POIs within a polygon bbox (with progress printing)

def query_polygon(polygon_bbox, poi_type, city, district, grid_id, total_grids, sleep_sec=0.2):
    page = 1
    results = []

    polygon = (
        f"{polygon_bbox['min_lon']},{polygon_bbox['min_lat']}|"
        f"{polygon_bbox['max_lon']},{polygon_bbox['max_lat']}"
    )

    while True:
        params = {
            "key": API_KEY,
            "types": poi_type,
            "polygon": polygon,
            "offset": 20,
            "page": page,
            "extensions": "base"
        }

        r = requests.get("https://restapi.amap.com/v3/place/polygon", params=params)
        data = r.json()
        pois = data.get("pois", [])

        print(
            f"{city}-{district} | "
            f"grid {grid_id}/{total_grids} | "
            f"polygon {polygon} | "
            f"type {poi_type} | "
            f"page {page} | "
            f"count {len(pois)}"
        )

        if not pois:
            break

        results.extend(pois)
        page += 1
        time.sleep(sleep_sec)

    return results

# 6. Main runner for a given POI type list (raw + district summary)
def run_shanghai_sport_resources(poi_types, label):
    poi_rows = []
    summary_rows = []

    for district, bbox in SHANGHAI_DISTRICT_BBOX.items():
        print("\n" + "=" * 40)
        print(f"Processing district: {district} [{label}]")
        print("=" * 40)

        grids = split_bbox(bbox, n=2)
        total_grids = len(grids)
        unique_ids = set()

        # Print grid boundaries
        for idx, g in enumerate(grids, start=1):
            print(
                f"{district} | GRID {idx}/{total_grids} | "
                f"{g['min_lon']},{g['min_lat']} → {g['max_lon']},{g['max_lat']}"
            )

        for grid_id, grid in enumerate(grids, start=1):
            for poi_type in poi_types:
                pois = query_polygon(
                    polygon_bbox=grid,
                    poi_type=poi_type,
                    city="Shanghai",
                    district=district,
                    grid_id=grid_id,
                    total_grids=total_grids,
                    sleep_sec=1.0
                )

                for p in pois:
                    poi_id = p.get("id")
                    if not poi_id or poi_id in unique_ids:
                        continue

                    unique_ids.add(poi_id)

                    lon, lat = (None, None)
                    if p.get("location"):
                        lon, lat = p["location"].split(",")

                    poi_rows.append({
                        "city": "Shanghai",
                        "district": district,
                        "grid_id": grid_id,
                        "poi_id": poi_id,
                        "poi_name": p.get("name"),
                        "type": p.get("type"),
                        "typecode": p.get("typecode"),
                        "longitude": lon,
                        "latitude": lat
                    })

        summary_rows.append({
            "city": "Shanghai",
            "district": district,
            "sport_facility_count": len(unique_ids)
        })

    df_poi = pd.DataFrame(poi_rows)
    df_summary = pd.DataFrame(summary_rows)

    # Rebuild a deduplicated summary from POI_raw (safety check)
    df_summary_rebuilt = (
        df_poi.groupby(["city", "district"])["poi_id"]
        .nunique()
        .reset_index(name="sport_facility_count")
    )

    return df_poi, df_summary, df_summary_rebuilt








if __name__ == "__main__":
    # 1) Run CORE
    df_poi_core, df_summary_core, df_summary_core_rebuilt = run_shanghai_sport_resources(
        poi_types=SPORT_TYPES_CORE,
        label="CORE"
    )

    # 2) Run PUBLIC 
    df_poi_public, df_summary_public, df_summary_public_rebuilt = run_shanghai_sport_resources(
        poi_types=SPORT_TYPES_PUBLIC,
        label="PUBLIC"
    )

    # 3) Merge CORE + PUBLIC summaries into ONE table
    core_sum = df_summary_core_rebuilt.rename(columns={"sport_facility_count": "core_facility_count"})
    public_sum = df_summary_public_rebuilt.rename(columns={"sport_facility_count": "public_facility_count"})

    df_one = core_sum.merge(public_sum, on=["city", "district"], how="outer")

    # Fill missing with 0 (in case some district has none in one category)
    df_one[["core_facility_count", "public_facility_count"]] = (
        df_one[["core_facility_count", "public_facility_count"]].fillna(0).astype(int)
    )

    # 3.5) Build ALL (CORE + PUBLIC, deduplicated)
    df_poi_all = pd.concat([df_poi_core, df_poi_public], ignore_index=True)
    df_poi_all = df_poi_all.drop_duplicates(subset=["poi_id"]).reset_index(drop=True)

    df_all_rebuilt = (
        df_poi_all.groupby(["city", "district"])["poi_id"]
        .nunique()
        .reset_index(name="all_facility_count")
    )

    df_one = df_one.merge(df_all_rebuilt, on=["city", "district"], how="outer")
    df_one["all_facility_count"] = df_one["all_facility_count"].fillna(0).astype(int)

    # Optional: keep a consistent order
    df_one = df_one.sort_values(["city", "district"]).reset_index(drop=True)

    # 4) Save ONLY ONE Excel
    df_one.to_excel("shanghai_sport_summary_core_public_all_one_table.xlsx", index=False)




#########Su zhou Sports




import json
import time
from pathlib import Path
import requests
import pandas as pd

# 1. API KEY
API_KEY = "6a959d23bdcb586180ca103a2c6344df"  

# 2. POI type codes for sports facilities
SPORT_TYPES_CORE = ["080100", "080101", "080102", "080103"]
SPORT_TYPES_PUBLIC = ["110101", "110102", "110103"]

# 3. Config
CITY_CN = "苏州市"
CITY_EN = "Suzhou"
BBOX_CACHE_PATH = Path("suzhou_district_bbox_cache.json")

# Whether to filter POIs by adname/cityname to reduce cross-border noise
FILTER_BY_ADMIN_NAME = False


# 4. 
def get_json_with_retries(url: str, params: dict, retries: int = 4, backoff: float = 1.2, timeout: int = 20):
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            return data
        except Exception as e:
            last_err = e
            sleep_s = backoff ** attempt
            print(f"[WARN] Request failed (attempt {attempt}/{retries}): {e}. Sleep {sleep_s:.1f}s")
            time.sleep(sleep_s)
    raise RuntimeError(f"Request failed after {retries} attempts. Last error: {last_err}")


# 5. District API: get children (districts/counties) under a city
def get_district_children_adcodes(city_name: str, level_subdistrict: int = 1):
    """
    Returns list of (name, adcode) for the city's children.
    For 苏州市, subdistrict=1 typically returns districts + county-level cities.
    """
    url = "https://restapi.amap.com/v3/config/district"
    params = {
        "key": API_KEY,
        "keywords": city_name,
        "subdistrict": level_subdistrict,
        "extensions": "base",
        "output": "JSON",
    }
    data = get_json_with_retries(url, params=params)

    if data.get("status") != "1":
        raise ValueError(f"District API error: {data}")

    districts = data.get("districts", [])
    if not districts:
        raise ValueError(f"District API no result for {city_name}: {data}")

    children = districts[0].get("districts", [])
    out = []
    for d in children:
        name = d.get("name")
        adcode = d.get("adcode")
        if name and adcode:
            out.append((name, adcode))
    return out


def get_bbox_from_adcode(adcode: str):
    """
    Fetch polygon boundary polyline by adcode and convert to bbox (min/max lon/lat).
    """
    url = "https://restapi.amap.com/v3/config/district"
    params = {
        "key": API_KEY,
        "keywords": adcode,
        "subdistrict": 0,
        "extensions": "all",  
        "output": "JSON",
    }
    data = get_json_with_retries(url, params=params)

    if data.get("status") != "1":
        raise ValueError(f"District API error for adcode={adcode}: {data}")

    districts = data.get("districts", [])
    if not districts:
        raise ValueError(f"District API no result for adcode={adcode}: {data}")

    polyline = districts[0].get("polyline", "")
    if not polyline:
        # Some areas might return empty polyline; fail clearly
        raise ValueError(f"No polyline returned for adcode={adcode}: {data}")

    # polyline: "lon,lat;lon,lat;...|lon,lat;..."
    parts = polyline.split("|")
    lons, lats = [], []
    for part in parts:
        for pt in part.split(";"):
            if not pt.strip():
                continue
            lon_str, lat_str = pt.split(",")
            lons.append(float(lon_str))
            lats.append(float(lat_str))

    return {
        "min_lon": min(lons),
        "max_lon": max(lons),
        "min_lat": min(lats),
        "max_lat": max(lats),
    }


def build_city_bbox_dict(city_name: str, cache_path: Path | None = None, sleep_sec: float = 0.2):
    """
    Build {district_name: bbox} using District API.
    Uses cache if available.
    """
    if cache_path and cache_path.exists():
        print(f"[INFO] Using cached bbox dict: {cache_path}")
        with cache_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    print(f"[INFO] Fetching district list for {city_name} ...")
    children = get_district_children_adcodes(city_name, level_subdistrict=1)

    bbox_dict = {}
    for name, adcode in children:
        print(f"[INFO] Fetching boundary for: {name} (adcode={adcode})")
        bbox = get_bbox_from_adcode(adcode)
        bbox_dict[name] = bbox
        time.sleep(sleep_sec)

    if cache_path:
        with cache_path.open("w", encoding="utf-8") as f:
            json.dump(bbox_dict, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Saved bbox cache to: {cache_path}")

    return bbox_dict


# 6. Split a bbox into a grid (2x2 => 4 grids)
def split_bbox(bbox, n=2):
    grids = []
    lon_step = (bbox["max_lon"] - bbox["min_lon"]) / n
    lat_step = (bbox["max_lat"] - bbox["min_lat"]) / n

    for i in range(n):
        for j in range(n):
            grid = {
                "min_lon": bbox["min_lon"] + i * lon_step,
                "max_lon": bbox["min_lon"] + (i + 1) * lon_step,
                "min_lat": bbox["min_lat"] + j * lat_step,
                "max_lat": bbox["min_lat"] + (j + 1) * lat_step
            }
            grids.append(grid)

    return grids


# 7. Query POIs within a polygon bbox (rectangle polygon) with progress printing
def query_polygon(polygon_bbox, poi_type, city, district, grid_id, total_grids, sleep_sec=0.2):
    page = 1
    results = []

    polygon = (
        f"{polygon_bbox['min_lon']},{polygon_bbox['min_lat']}|"
        f"{polygon_bbox['max_lon']},{polygon_bbox['max_lat']}"
    )

    while True:
        params = {
            "key": API_KEY,
            "types": poi_type,
            "polygon": polygon,
            "offset": 20,
            "page": page,
            "extensions": "base"
        }

        data = get_json_with_retries("https://restapi.amap.com/v3/place/polygon", params=params)

        pois = data.get("pois", [])

        print(
            f"{city}-{district} | "
            f"grid {grid_id}/{total_grids} | "
            f"polygon {polygon} | "
            f"type {poi_type} | "
            f"page {page} | "
            f"count {len(pois)}"
        )

        if not pois:
            break

        results.extend(pois)
        page += 1
        time.sleep(sleep_sec)

    return results


# 8. Main runner for Suzhou (raw + district summary)
def run_suzhou_sport_resources(poi_types, label, district_bbox_dict):
    poi_rows = []
    summary_rows = []

    for district, bbox in district_bbox_dict.items():
        print("\n" + "=" * 40)
        print(f"Processing district: {district} [{label}]")
        print("=" * 40)

        grids = split_bbox(bbox, n=2)
        total_grids = len(grids)
        unique_ids = set()

        # Print grid boundaries
        for idx, g in enumerate(grids, start=1):
            print(
                f"{district} | GRID {idx}/{total_grids} | "
                f"{g['min_lon']},{g['min_lat']} → {g['max_lon']},{g['max_lat']}"
            )

        for grid_id, grid in enumerate(grids, start=1):
            for poi_type in poi_types:
                pois = query_polygon(
                    polygon_bbox=grid,
                    poi_type=poi_type,
                    city=CITY_EN,
                    district=district,
                    grid_id=grid_id,
                    total_grids=total_grids,
                    sleep_sec=1.0
                )

                for p in pois:
                    poi_id = p.get("id")
                    if not poi_id or poi_id in unique_ids:
                        continue

                    if FILTER_BY_ADMIN_NAME:
                        adname = (p.get("adname") or "").strip()
                        cityname = (p.get("cityname") or "").strip()
                        # Keep if matches district or at least within the same city.
                        if (district not in adname) and (CITY_CN not in cityname) and (CITY_EN not in cityname):
                            continue

                    unique_ids.add(poi_id)

                    lon, lat = (None, None)
                    if p.get("location"):
                        try:
                            lon, lat = p["location"].split(",")
                        except Exception:
                            lon, lat = (None, None)

                    poi_rows.append({
                        "city": CITY_EN,
                        "district": district,
                        "grid_id": grid_id,
                        "poi_id": poi_id,
                        "poi_name": p.get("name"),
                        "type": p.get("type"),
                        "typecode": p.get("typecode"),
                        "longitude": lon,
                        "latitude": lat
                    })

        summary_rows.append({
            "city": CITY_EN,
            "district": district,
            "sport_facility_count": len(unique_ids)
        })

    df_poi = pd.DataFrame(poi_rows)
    df_summary = pd.DataFrame(summary_rows)

    # Rebuild a deduplicated summary from POI_raw (safety check)
    if len(df_poi) > 0:
        df_summary_rebuilt = (
            df_poi.groupby(["city", "district"])["poi_id"]
            .nunique()
            .reset_index(name="sport_facility_count")
        )
    else:
        df_summary_rebuilt = pd.DataFrame(columns=["city", "district", "sport_facility_count"])

    return df_poi, df_summary, df_summary_rebuilt


if __name__ == "__main__":
    # 0) Build Suzhou district bbox dict from District API 
    SUZHOU_DISTRICT_BBOX = build_city_bbox_dict(CITY_CN, cache_path=BBOX_CACHE_PATH, sleep_sec=0.15)

    # 1) Run CORE 
    df_poi_core, df_summary_core, df_summary_core_rebuilt = run_suzhou_sport_resources(
        poi_types=SPORT_TYPES_CORE,
        label="CORE",
        district_bbox_dict=SUZHOU_DISTRICT_BBOX
    )

    # 2) Run PUBLIC 
    df_poi_public, df_summary_public, df_summary_public_rebuilt = run_suzhou_sport_resources(
        poi_types=SPORT_TYPES_PUBLIC,
        label="PUBLIC",
        district_bbox_dict=SUZHOU_DISTRICT_BBOX
    )

    # 3) Merge CORE + PUBLIC summaries into ONE table
    core_sum = df_summary_core_rebuilt.rename(columns={"sport_facility_count": "core_facility_count"})
    public_sum = df_summary_public_rebuilt.rename(columns={"sport_facility_count": "public_facility_count"})

    df_one = core_sum.merge(public_sum, on=["city", "district"], how="outer")

    # Fill missing with 0 (in case some district has none in one category)
    df_one[["core_facility_count", "public_facility_count"]] = (
        df_one[["core_facility_count", "public_facility_count"]].fillna(0).astype(int)
    )
    df_one["total_facility_count"] = df_one["core_facility_count"] + df_one["public_facility_count"]

    # Optional: keep a consistent order
    df_one = df_one.sort_values(["city", "district"]).reset_index(drop=True)

    # 4) Save ONLY ONE Excel
    df_one.to_excel("suzhou_sport_summary_core_public_one_table.xlsx", index=False)

    print("\n[DONE] Saved:", "suzhou_sport_summary_core_public_one_table.xlsx")






df_all = pd.concat([df_poi_core, df_poi_public], ignore_index=True)

df_total = (
    df_all.groupby(["city", "district"])["poi_id"]
    .nunique()
    .reset_index(name="total_facility_count")
)


df_total = df_total.sort_values(["city", "district"]).reset_index(drop=True)

df_total.to_excel("suzhou_sport_total_facility_count.xlsx", index=False)

print("[DONE] Saved: suzhou_sport_total_facility_count.xlsx")




