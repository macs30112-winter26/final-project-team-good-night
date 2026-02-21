# Exploratory Analysis of Stress, Sleep Quality, and Residential Contexts in Urban China

## Project Description

Project Goodnight examines how sleep quality varies across urban districts within major Chinese cities and how individual-level stress interacts with neighborhood-level environmental and infrastructure conditions.

Our primary outcome is `sleep_quality`, measured using survey data. Our main individual-level predictor is perceived stress (`pss4_total`). We link survey respondents to district-level contextual indicators to examine whether environmental and infrastructure characteristics are associated with sleep and whether they moderate the relationship between stress and sleep.

District-level variables include:

- Mean NDVI (June 30 – August 31, 2023; green space proxy)
- Mean VIIRS nighttime light radiance (June 30 – August 31, 2023; urban intensity proxy)
- Sports facility density per 100,000 residents

The project is descriptive and exploratory. We focus on identifying patterns and cross-city variation rather than making causal claims.

Our central question is:

How does individual stress relate to sleep quality, and do district-level environmental or infrastructure characteristics moderate that relationship?


## Data

### PBICR-2023 Survey
Individual-level data on perceived stress, sleep quality, and district identifiers.  
Retrieved via download.

### MODIS NDVI (Google Earth Engine API)
Satellite-derived vegetation index aggregated to ADM3 district boundaries for June 30 – August 31, 2023.  
Collected via API using Python.

### VIIRS Nighttime Lights (Google Earth Engine API)
Satellite-derived nighttime radiance aggregated to ADM3 district boundaries for June 30 – August 31, 2023.  
Collected via API using Python.

### Gaode (Amap) Places API – Sports Facilities
Point-of-interest data used to compute district-level sports facility density (facilities per 100,000 residents).  
Collected via API and aggregated to district level.


## Libraries

Python libraries used:

- earthengine-api
- geemap
- pandas
- numpy
- geopandas
- matplotlib
- seaborn


## Repo Structure

- `code/` contains environmental extraction and aggregation scripts. ndvi_viirs_5cities_2023_summer.py
- `data/processed/` contains cleaned district-level summary tables used for merging. [district-level NDVI and VIIRS summary tables]
- `figs/` stores exploratory and presentation-ready visualizations. [plots and visualizations]


## Contributions

### Shoshana Abikzer
- Remote sensing extraction (NDVI and VIIRS)
- District-level aggregation and validation
- Repository organization and documentation
- Environmental data standardization across five cities

### Rebecca Gou
- Survey cleaning and variable construction
- Sports facility density integration
- Exploratory data analysis and visualization
- Merging environmental and infrastructure variables for modeling

