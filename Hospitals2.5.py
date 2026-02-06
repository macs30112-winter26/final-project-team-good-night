#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  5 21:27:53 2026

@author: rebecca
"""
### Created by Yuxuan Gou (Rebecca). Team members: Yuxuan Gou and Shoshana Abikzer.


# 1 Introduction

"""This script collects data from the Gaode (Amap) Places API. It counts hospital POIs at the district/county level in Beijing, 
Chengdu, Suzhou, and Shenzhen (four large cities in China)."""

# 2 AI use
"""I ran into the Amap (Gaode) Places API limit (max 10 pages × 20 results), 
which can truncate POIs in dense areas, so I used a simple spatial splitting approach: 
for each district/county area, I divided the search box into four smaller grids, queried each grid separately, 
and then merged the outputs while de-duplicating POIs by unique POI ID; 
I used AI only to debug my own code and to learn this general tiling + deduplication strategy."""





###########################  beijing hosptital facility
import requests
import time
import pandas as pd

# 1. API KEY
API_KEY = "b4c8ec0a57a187677abce86fd5a022f5"


# 2. Districts in Beijing bbox
BEIJING_DISTRICT_BBOX = {
    "东城区": {"min_lon": 116.38, "max_lon": 116.45, "min_lat": 39.88, "max_lat": 39.95},
    "西城区": {"min_lon": 116.32, "max_lon": 116.40, "min_lat": 39.88, "max_lat": 39.95},
    "朝阳区": {"min_lon": 116.38, "max_lon": 116.65, "min_lat": 39.85, "max_lat": 40.05},
    "丰台区": {"min_lon": 116.20, "max_lon": 116.45, "min_lat": 39.75, "max_lat": 39.95},
    "石景山区": {"min_lon": 116.10, "max_lon": 116.30, "min_lat": 39.85, "max_lat": 40.00},
    "海淀区": {"min_lon": 116.15, "max_lon": 116.40, "min_lat": 39.90, "max_lat": 40.10},
    "门头沟区": {"min_lon": 115.70, "max_lon": 116.10, "min_lat": 39.90, "max_lat": 40.15},
    "房山区": {"min_lon": 115.75, "max_lon": 116.35, "min_lat": 39.50, "max_lat": 39.85},
    "通州区": {"min_lon": 116.55, "max_lon": 116.85, "min_lat": 39.75, "max_lat": 40.05},
    "顺义区": {"min_lon": 116.55, "max_lon": 116.95, "min_lat": 40.00, "max_lat": 40.25},
    "昌平区": {"min_lon": 116.00, "max_lon": 116.45, "min_lat": 40.00, "max_lat": 40.35},
    "大兴区": {"min_lon": 116.20, "max_lon": 116.65, "min_lat": 39.60, "max_lat": 39.90},
    "怀柔区": {"min_lon": 116.40, "max_lon": 116.95, "min_lat": 40.20, "max_lat": 40.60},
    "平谷区": {"min_lon": 117.00, "max_lon": 117.45, "min_lat": 39.60, "max_lat": 40.05},
    "密云区": {"min_lon": 116.75, "max_lon": 117.40, "min_lat": 40.20, "max_lat": 40.90},
    "延庆区": {"min_lon": 115.85, "max_lon": 116.45, "min_lat": 40.30, "max_lat": 40.85}
}


# 3. POI 
HOSPITAL_TYPES = [
    "090101",  
    "090102"]


# 4. bbox → grid
def split_bbox(bbox, n=2):
    grids = []
    lon_step = (bbox["max_lon"] - bbox["min_lon"]) / n
    lat_step = (bbox["max_lat"] - bbox["min_lat"]) / n
    
    for i in range(n):
        for j in range(n):
            grids.append({
                "min_lon": bbox["min_lon"] + i * lon_step,
                "max_lon": bbox["min_lon"] + (i + 1) * lon_step,
                "min_lat": bbox["min_lat"] + j * lat_step,
                "max_lat": bbox["min_lat"] + (j + 1) * lat_step
            })
    return grids


# 5. polygon 
def query_polygon(polygon_bbox, poi_type, district, api_key, sleep_sec=0.2):
    page = 1
    results = []
    
    polygon = (
        f"{polygon_bbox['min_lon']},{polygon_bbox['min_lat']}|"
        f"{polygon_bbox['max_lon']},{polygon_bbox['max_lat']}"
    )
    
    while True:
        params = {
            "key": api_key,
            "types": poi_type,
            "polygon": polygon,
            "offset": 20,
            "page": page,
            "extensions": "base"
        }
        
        r = requests.get(
            "https://restapi.amap.com/v3/place/polygon",
            params=params
        )
        data = r.json()
        pois = data.get("pois", [])
        
        print(
            f"{district} | polygon {polygon} | type {poi_type} | "
            f"page {page} | count {len(pois)}"
        )
        
        if len(pois) == 0:
            break
        
        results.extend(pois)
        page += 1
        time.sleep(sleep_sec)
    
    return results


# 6. 
def run_beijing_all_districts():
    results = []
    
    for district, bbox in BEIJING_DISTRICT_BBOX.items():
        print("\n==============================")
        print(f"Start：{district}")
        print("==============================")
        
        grids = split_bbox(bbox, n=2)
        all_pois = {}
        
        for grid in grids:
            for poi_type in HOSPITAL_TYPES:
                pois = query_polygon(
                    polygon_bbox=grid,
                    poi_type=poi_type,
                    district=district,
                    api_key=API_KEY
                )
                for p in pois:
                    all_pois[p["id"]] = p  # POI id 
        
        district_count = len(all_pois)
        print(f"{district} Hospital POI：{district_count}")
        
        results.append({
            "city": "Beijing",
            "district": district,
            "hospital_count": district_count
        })
    
    return pd.DataFrame(results)


# 7. Output
if __name__ == "__main__":
    df_beijing_hospitals = run_beijing_all_districts()
    df_beijing_hospitals.to_csv(
        "beijing_district_hospital_count.csv",
        index=False,
        encoding="utf-8-sig"
    )
    
    




############################ suzhou Hospital


import requests
import time
import pandas as pd

# 1. API KEY
API_KEY = "6a959d23bdcb586180ca103a2c6344df"


# 2. Districts/County-level cities in Suzhou bbox (research-grade approximations)
SUZHOU_DISTRICT_BBOX = {
    # 市辖区
    "姑苏区": {"min_lon": 120.56, "max_lon": 120.68, "min_lat": 31.26, "max_lat": 31.36},
    "虎丘区": {"min_lon": 120.40, "max_lon": 120.60, "min_lat": 31.27, "max_lat": 31.45},  
    "吴中区": {"min_lon": 120.44, "max_lon": 120.85, "min_lat": 31.06, "max_lat": 31.35},
    "相城区": {"min_lon": 120.55, "max_lon": 120.82, "min_lat": 31.28, "max_lat": 31.48},
    "吴江区": {"min_lon": 120.49, "max_lon": 120.85, "min_lat": 30.70, "max_lat": 31.12},

    # 功能区
    "苏州工业园区": {"min_lon": 120.65, "max_lon": 120.85, "min_lat": 31.26, "max_lat": 31.38},

    # 县级市
    "昆山市": {"min_lon": 120.86, "max_lon": 121.20, "min_lat": 31.18, "max_lat": 31.50},
    "太仓市": {"min_lon": 121.00, "max_lon": 121.30, "min_lat": 31.36, "max_lat": 31.64},
    "常熟市": {"min_lon": 120.65, "max_lon": 121.05, "min_lat": 31.50, "max_lat": 31.80},
    "张家港市": {"min_lon": 120.35, "max_lon": 120.75, "min_lat": 31.72, "max_lat": 31.98},
}


# 3. POI 
HOSPITAL_TYPES = [
    "090101",  
    "090102"

]


# 4. bbox → grid
def split_bbox(bbox, n=2):
    grids = []
    lon_step = (bbox["max_lon"] - bbox["min_lon"]) / n
    lat_step = (bbox["max_lat"] - bbox["min_lat"]) / n
    
    for i in range(n):
        for j in range(n):
            grids.append({
                "min_lon": bbox["min_lon"] + i * lon_step,
                "max_lon": bbox["min_lon"] + (i + 1) * lon_step,
                "min_lat": bbox["min_lat"] + j * lat_step,
                "max_lat": bbox["min_lat"] + (j + 1) * lat_step
            })
    return grids


# 5. polygon 
def query_polygon(polygon_bbox, poi_type, district, api_key, sleep_sec=0.2):
    page = 1
    results = []
    
    polygon = (
        f"{polygon_bbox['min_lon']},{polygon_bbox['min_lat']}|"
        f"{polygon_bbox['max_lon']},{polygon_bbox['max_lat']}"
    )
    
    while True:
        params = {
            "key": api_key,
            "types": poi_type,
            "polygon": polygon,
            "offset": 20,
            "page": page,
            "extensions": "base"
        }
        
        r = requests.get(
            "https://restapi.amap.com/v3/place/polygon",
            params=params
        )
        data = r.json()
        pois = data.get("pois", [])
        
        print(
            f"{district} | polygon {polygon} | type {poi_type} | "
            f"page {page} | count {len(pois)}"
        )
        
        if len(pois) == 0:
            break
        
        results.extend(pois)
        page += 1
        time.sleep(sleep_sec)
    
    return results


# 6. 
def run_suzhou_all_districts():
    results = []
    
    for district, bbox in SUZHOU_DISTRICT_BBOX.items():
        print("\n==============================")
        print(f"Start：{district}")
        print("==============================")
        
        grids = split_bbox(bbox, n=2)
        all_pois = {}
        
        for grid in grids:
            for poi_type in HOSPITAL_TYPES:
                pois = query_polygon(
                    polygon_bbox=grid,
                    poi_type=poi_type,
                    district=district,
                    api_key=API_KEY
                )
                for p in pois:
                    all_pois[p["id"]] = p  # POI id 
        
        district_count = len(all_pois)
        print(f"{district} Hospital POI：{district_count}")
        
        results.append({
            "city": "Suzhou",
            "district": district,
            "hospital_count": district_count
        })
    
    return pd.DataFrame(results)


# 7. Output
if __name__ == "__main__":
    df_suzhou_hospitals = run_suzhou_all_districts()
    df_suzhou_hospitals.to_csv(
        "suzhou_district_hospital_count.csv",
        index=False,
        encoding="utf-8-sig"
    )


################   Shenzhen Hospital


import requests
import time
import pandas as pd

# 1. API KEY
API_KEY = "6a959d23bdcb586180ca103a2c6344df"


# 2. Districts in Shenzhen bbox (research-grade approximations)
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


# 3. POI 
HOSPITAL_TYPES = [
    "090101",  
    "090102"
]


# 4. bbox → grid
def split_bbox(bbox, n=2):
    grids = []
    lon_step = (bbox["max_lon"] - bbox["min_lon"]) / n
    lat_step = (bbox["max_lat"] - bbox["min_lat"]) / n
    
    for i in range(n):
        for j in range(n):
            grids.append({
                "min_lon": bbox["min_lon"] + i * lon_step,
                "max_lon": bbox["min_lon"] + (i + 1) * lon_step,
                "min_lat": bbox["min_lat"] + j * lat_step,
                "max_lat": bbox["min_lat"] + (j + 1) * lat_step
            })
    return grids


# 5. polygon 
def query_polygon(polygon_bbox, poi_type, district, api_key, sleep_sec=0.2):
    page = 1
    results = []
    
    polygon = (
        f"{polygon_bbox['min_lon']},{polygon_bbox['min_lat']}|"
        f"{polygon_bbox['max_lon']},{polygon_bbox['max_lat']}"
    )
    
    while True:
        params = {
            "key": api_key,
            "types": poi_type,
            "polygon": polygon,
            "offset": 20,
            "page": page,
            "extensions": "base"
        }
        
        r = requests.get(
            "https://restapi.amap.com/v3/place/polygon",
            params=params
        )
        data = r.json()
        pois = data.get("pois", [])
        
        print(
            f"{district} | polygon {polygon} | type {poi_type} | "
            f"page {page} | count {len(pois)}"
        )
        
        if len(pois) == 0:
            break
        
        results.extend(pois)
        page += 1
        time.sleep(sleep_sec)
    
    return results


# 6. 
def run_shenzhen_all_districts():
    results = []
    
    for district, bbox in SHENZHEN_DISTRICT_BBOX.items():
        print("\n==============================")
        print(f"Start：{district}")
        print("==============================")
        
        grids = split_bbox(bbox, n=2)
        all_pois = {}
        
        for grid in grids:
            for poi_type in HOSPITAL_TYPES:
                pois = query_polygon(
                    polygon_bbox=grid,
                    poi_type=poi_type,
                    district=district,
                    api_key=API_KEY
                )
                for p in pois:
                    all_pois[p["id"]] = p  # POI id 
        
        district_count = len(all_pois)
        print(f"{district} Hospital POI：{district_count}")
        
        results.append({
            "city": "Shenzhen",
            "district": district,
            "hospital_count": district_count
        })
    
    return pd.DataFrame(results)


# 7. Output
if __name__ == "__main__":
    df_shenzhen_hospitals = run_shenzhen_all_districts()
    df_shenzhen_hospitals.to_csv(
        "shenzhen_district_hospital_count.csv",
        index=False,
        encoding="utf-8-sig"
    )






################   Chengdu Hospital

import requests
import time
import pandas as pd

API_KEY = "d570d444d489aa71e34d08abdb989330"

CHENGDU_DISTRICT_BBOX = {
    "锦江区": {"min_lon": 104.05, "max_lon": 104.14, "min_lat": 30.58, "max_lat": 30.70},
    "青羊区": {"min_lon": 103.98, "max_lon": 104.10, "min_lat": 30.62, "max_lat": 30.73},
    "金牛区": {"min_lon": 103.96, "max_lon": 104.10, "min_lat": 30.66, "max_lat": 30.78},
    "武侯区": {"min_lon": 103.98, "max_lon": 104.12, "min_lat": 30.56, "max_lat": 30.70},
    "成华区": {"min_lon": 104.06, "max_lon": 104.22, "min_lat": 30.64, "max_lat": 30.78},

    "龙泉驿区": {"min_lon": 104.16, "max_lon": 104.36, "min_lat": 30.52, "max_lat": 30.78},
    "青白江区": {"min_lon": 104.16, "max_lon": 104.40, "min_lat": 30.78, "max_lat": 31.06},
    "新都区": {"min_lon": 103.92, "max_lon": 104.22, "min_lat": 30.70, "max_lat": 30.96},
    "温江区": {"min_lon": 103.72, "max_lon": 103.96, "min_lat": 30.60, "max_lat": 30.80},
    "双流区": {"min_lon": 103.84, "max_lon": 104.18, "min_lat": 30.40, "max_lat": 30.66},
    "郫都区": {"min_lon": 103.78, "max_lon": 104.06, "min_lat": 30.66, "max_lat": 30.90},
    "新津区": {"min_lon": 103.74, "max_lon": 104.06, "min_lat": 30.34, "max_lat": 30.56},

    "金堂县": {"min_lon": 104.18, "max_lon": 104.72, "min_lat": 30.52, "max_lat": 30.98},
    "大邑县": {"min_lon": 103.30, "max_lon": 103.74, "min_lat": 30.44, "max_lat": 30.78},
    "蒲江县": {"min_lon": 103.26, "max_lon": 103.74, "min_lat": 30.08, "max_lat": 30.36},

    "都江堰市": {"min_lon": 103.44, "max_lon": 103.92, "min_lat": 30.82, "max_lat": 31.22},
    "彭州市": {"min_lon": 103.62, "max_lon": 104.14, "min_lat": 30.90, "max_lat": 31.32},
    "邛崃市": {"min_lon": 103.08, "max_lon": 103.74, "min_lat": 30.18, "max_lat": 30.58},
    "崇州市": {"min_lon": 103.30, "max_lon": 103.88, "min_lat": 30.44, "max_lat": 30.86},
    "简阳市": {"min_lon": 104.20, "max_lon": 105.12, "min_lat": 30.16, "max_lat": 30.70},
}

HOSPITAL_TYPES = ["090101", "090102", "090103", "090104", "090105", "090106"]


def split_bbox(bbox, n=2):
    grids = []
    lon_step = (bbox["max_lon"] - bbox["min_lon"]) / n
    lat_step = (bbox["max_lat"] - bbox["min_lat"]) / n

    for i in range(n):
        for j in range(n):
            grids.append({
                "min_lon": bbox["min_lon"] + i * lon_step,
                "max_lon": bbox["min_lon"] + (i + 1) * lon_step,
                "min_lat": bbox["min_lat"] + j * lat_step,
                "max_lat": bbox["min_lat"] + (j + 1) * lat_step
            })
    return grids


def query_polygon(polygon_bbox, poi_type, district, api_key, sleep_sec=0.2):
    page = 1
    results = []

    polygon = (
        f"{polygon_bbox['min_lon']},{polygon_bbox['min_lat']}|"
        f"{polygon_bbox['max_lon']},{polygon_bbox['max_lat']}"
    )

    while True:
        params = {
            "key": api_key,
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
            f"{district} | polygon {polygon} | type {poi_type} | "
            f"page {page} | count {len(pois)}"
        )

        if len(pois) == 0:
            break

        results.extend(pois)
        page += 1
        time.sleep(sleep_sec)

    return results


def run_chengdu_all_districts():
    results = []

    for district, bbox in CHENGDU_DISTRICT_BBOX.items():
        print("\n==============================")
        print(f"Start：{district}")
        print("==============================")

        grids = split_bbox(bbox, n=2)
        all_pois = {}

        for grid in grids:
            for poi_type in HOSPITAL_TYPES:
                pois = query_polygon(
                    polygon_bbox=grid,
                    poi_type=poi_type,
                    district=district,
                    api_key=API_KEY
                )
                for p in pois:
                    all_pois[p["id"]] = p

        district_count = len(all_pois)
        print(f"{district} Hospital POI：{district_count}")

        results.append({
            "city": "Chengdu",
            "district": district,
            "hospital_count": district_count
        })

    return pd.DataFrame(results)


if __name__ == "__main__":
    df_chengdu_hospitals = run_chengdu_all_districts()
    df_chengdu_hospitals.to_csv(
        "chengdu_district_hospital_count.csv",
        index=False,
        encoding="utf-8-sig"
    )












