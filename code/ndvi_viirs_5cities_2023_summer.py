"""
Shoshana Abikzer, Rebecca Gou 

Objective:
- For each of our 5 cities, compute mean NDVI (MODIS) + mean nightlights (VIIRS)
  for every ADM3 unit (district/county) inside that city.
- Export ONE CSV per city to Google Drive (same export style as our Chengdu run).
- AI USE: AI use was necessary for debugging and syntax suggestions. Jupyter Notebook's AI assistance and OpenAI were used for syntax help, but NOT use to produce original code or structure. 

Window we’re using:
- 2023-06-30 to 2023-08-31
AI Use: Used for some syntax config and debugging for Google Earth Engine.
"""

import json
import time
import ee


# --------------------
# Config
# --------------------
GADM_ADM3_ASSET = "projects/project-goodnight-485705/assets/gadm41_CHN_3"

DATE_START = "2023-06-30"
DATE_END_EXCLUSIVE = "2023-09-01"  # includes 2023-08-31

# NDVI (MODIS)
MODIS_COLLECTION = "MODIS/061/MOD13Q1"
MODIS_BAND = "NDVI"
MODIS_SCALE_FACTOR = 0.0001
MODIS_SCALE_M = 250

# VIIRS (nightlights)
VIIRS_COLLECTION = "NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG"
VIIRS_BAND = "avg_rad"

# Export
EXPORT_FOLDER = "GEE_Exports"
EXPORT_FORMAT = "CSV"
TILE_SCALE = 4

# Our 5 cities (same filtering as our Check in 1 Chengdu notebook)
CITIES = [
    {"COUNTRY": "China", "NAME_1": "Beijing",   "NAME_2": "Beijing"},
    {"COUNTRY": "China", "NAME_1": "Shanghai",  "NAME_2": "Shanghai"},
    {"COUNTRY": "China", "NAME_1": "Guangdong", "NAME_2": "Shenzhen"},
    {"COUNTRY": "China", "NAME_1": "Jiangsu",   "NAME_2": "Suzhou"},
    {"COUNTRY": "China", "NAME_1": "Sichuan",   "NAME_2": "Chengdu"},
]


def init_ee() -> None:
    try:
        ee.Initialize()
    except Exception:
        ee.Authenticate()
        ee.Initialize()


def apply_filters(fc: ee.FeatureCollection, filters: dict) -> ee.FeatureCollection:
    out = fc
    for k, v in filters.items():
        out = out.filter(ee.Filter.eq(k, v))
    return out


def ndvi_window(date_start: str, date_end_exclusive: str) -> ee.Image:
    start = ee.Date(date_start)
    end = ee.Date(date_end_exclusive)

    col = (
        ee.ImageCollection(MODIS_COLLECTION)
        .filterDate(start, end)
        .select(MODIS_BAND)
        .map(lambda img: img.multiply(MODIS_SCALE_FACTOR).copyProperties(img, img.propertyNames()))
    )

    return col.mean().rename("ndvi_mean")


def viirs_window(date_start: str, date_end_exclusive: str) -> ee.Image:
    start = ee.Date(date_start)
    end = ee.Date(date_end_exclusive)

    col = (
        ee.ImageCollection(VIIRS_COLLECTION)
        .filterDate(start, end)
        .select(VIIRS_BAND)
    )

    return col.mean().rename("viirs_mean_avg_rad")


def add_labels(fc: ee.FeatureCollection, filters: dict, date_start: str, date_end: str) -> ee.FeatureCollection:
    def _f(feat: ee.Feature) -> ee.Feature:
        return (
            feat.set("country", filters["COUNTRY"])
                .set("province", filters["NAME_1"])
                .set("city", filters["NAME_2"])
                .set("date_start", date_start)
                .set("date_end", date_end)
        )
    return fc.map(_f)


def reduce_to_admin_units(units: ee.FeatureCollection, ndvi_img: ee.Image, viirs_img: ee.Image) -> ee.FeatureCollection:
    img = ee.Image.cat([ndvi_img, viirs_img])

    reduced = img.reduceRegions(
        collection=units,
        reducer=ee.Reducer.mean(),
        scale=MODIS_SCALE_M,
        tileScale=TILE_SCALE,
    )

    keep = [
        "date_start", "date_end", "country", "province", "city",
        "GID_0", "GID_1", "GID_2", "GID_3",
        "NAME_0", "NAME_1", "NAME_2", "NAME_3",
        "VARNAME_3", "TYPE_3", "ENGTYPE_3",
        "ndvi_mean", "viirs_mean_avg_rad",
    ]

    def _select(f: ee.Feature) -> ee.Feature:
        props = ee.Dictionary.fromLists(
            ee.List(keep),
            ee.List(keep).map(lambda k: f.get(ee.String(k)))
        )
        return ee.Feature(None, props)

    return reduced.map(_select)


def export_to_drive(fc: ee.FeatureCollection, description: str) -> ee.batch.Task:
    task = ee.batch.Export.table.toDrive(
        collection=fc,
        description=description,
        folder=EXPORT_FOLDER,
        fileFormat=EXPORT_FORMAT,
    )
    task.start()
    return task


def wait_for_task(task: ee.batch.Task, poll_seconds: int = 10, timeout_minutes: int = 60) -> None:
    deadline = time.time() + timeout_minutes * 60
    last_state = None

    while True:
        status = task.status()
        state = status.get("state", "UNKNOWN")

        if state != last_state:
            print(json.dumps(status, indent=2))
            last_state = state

        if state in {"COMPLETED", "FAILED", "CANCELLED"}:
            if state != "COMPLETED":
                raise RuntimeError(f"Export ended in state={state}. Status:\n{json.dumps(status, indent=2)}")
            print("Export completed.\n")
            return

        if time.time() > deadline:
            raise TimeoutError("Timed out waiting for export. Check the GEE Tasks tab / Google Drive.")

        time.sleep(poll_seconds)


def main() -> None:
    init_ee()

    adm3 = ee.FeatureCollection(GADM_ADM3_ASSET)

    ndvi = ndvi_window(DATE_START, DATE_END_EXCLUSIVE)
    viirs = viirs_window(DATE_START, DATE_END_EXCLUSIVE)

    print("\n=== Team Good Night: ADM3 NDVI + VIIRS (June 30–Aug 31, 2023) ===\n")

    for filters in CITIES:
        city = filters["NAME_2"]
        province = filters["NAME_1"]

        units = apply_filters(adm3, filters)
        n = units.size().getInfo()
        print(f"{city} ({province}) matched ADM3 units: {n}")

        if n == 0:
            print("-> skipping (no matches)\n")
            continue

        units = add_labels(units, filters, DATE_START, "2023-08-31")
        out = reduce_to_admin_units(units, ndvi, viirs)

        # sanity sample (first 3 districts)
        print("Sample rows:")
        print(json.dumps(out.limit(3).getInfo(), indent=2))

        desc = f"{city}_NDVI_VIIRS_ADM3_{DATE_START}_to_2023-08-31"
        task = export_to_drive(out, desc)
        print(f"Started export task: {task.id}")

        wait_for_task(task, poll_seconds=10, timeout_minutes=60)

    print("All city exports launched/completed.\n")


if __name__ == "__main__":
    main()
  Add NDVI+VIIRS extraction script for 5 cities (Jun30–Aug31 2023)                          
