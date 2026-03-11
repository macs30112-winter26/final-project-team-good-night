# Exploratory Analysis of Stress, Sleep Quality, and Residential Contexts in Urban China

# Project Description

## Summary

Project Goodnight (P_GN) looks at how sleep quality varies across districts in several large Chinese cities and how this relates to individual stress and neighborhood conditions.

We combine individual survey responses with district-level environmental indicators collected through APIs and satellite datasets. These environmental indicators include vegetation levels (NDVI), nighttime light intensity, and sports facility density.

The goal of the project is to connect survey respondents to the environmental conditions of the district they live in and explore how stress and urban environment characteristics relate to sleep outcomes.

Main steps in the project include:

- linking PBICR survey respondents to district identifiers
- collecting environmental indicators using APIs
- extracting satellite indicators using the Google Earth Engine API
- building district-level measures of sports facility density
- merging environmental data with survey data
- running exploratory analysis and visualizations

This project is exploratory and focuses on identifying patterns across cities rather than making causal claims.

---

## Additional Info

**Total lines of code:** approx **1600 lines of Python code** across scripts used for data collection, cleaning, and analysis.

**Methods and Analysis**

This project links PBICR 2023 survey data with environmental indicators measured at the district level. NDVI vegetation values and nighttime light intensity were collected using the Google Earth Engine API. Sports facility locations were collected through the Gaode Maps API and converted into district-level density measures.

These environmental indicators were aggregated to district boundaries and merged with the survey dataset using district identifiers. The final dataset was used to generate descriptive visualizations and run regression models examining how stress and environmental conditions relate to sleep quality.

**Project Strength**

P_GN relied on data wrangling and integration as well as cleaning and restructuring the PBICR survey data, aggregating satellite indicators to district boundaries, and converting API-derived point-of-interest data into district-level measures. These datasets were standardized and merged using shared district identifiers so that environmental indicators could be directly compared with individual sleep survey responses in the final analysis.

---

# Data

This project uses both survey data and environmental data collected through APIs.

### PBICR 2023 Survey Data
- link: dataset accessed through course project resources
- **Collection Method:** download
- **Description:** survey responses containing sleep quality, perceived stress, and demographic variables.

### Gaode Maps API – Sports Facilities
- **Link:** https://lbs.amap.com/
- **Collection Method:** API request
- **Description:** point-of-interest data used to count sports facilities and calculate facility density for each district.

### Google Earth Engine – VIIRS Nighttime Lights
- **Link:** https://developers.google.com/earth-engine/datasets
- **Collection Method:** API
- **Description:** satellite data measuring nighttime light intensity, used as a proxy for urban development intensity.

### Google Earth Engine – MODIS NDVI
- **Link:** https://developers.google.com/earth-engine/datasets
- **Collection Method:** API
- **Description:** satellite vegetation index used as a proxy for green space in each district.

---

# Repository Structure

```
final-project-team-good-night/
│
├── code/
│   ├── Data cleaning.py
│   ├── Data_analysis.ipynb
│   ├── Sports_5cities.py
│   └── ndvi_viirs_5cities_2023_summer.py
│
├── data/
│   └── processed/
│       ├── Beijing_means_table - Sheet1.csv
│       ├── Chengdu_table - Sheet1.csv
│       ├── Shanghai_table - Sheet1.csv
│       ├── Shenzhen_means_table - Sheet1.csv
│       ├── Suzhou_means_table - Sheet1.csv
│       ├── all_cities_sport_density.xlsx
│       ├── environment variables.xlsx
│       └── sports.xlsx
│
└── README.md
```

---

# Libraries

The following Python libraries were used:

- pandas 2.2.0
- numpy 1.26.4
- geopandas 0.14.3
- earthengine-api 0.1.387
- geemap 0.32.0
- matplotlib 3.8.2
- seaborn 0.13.2
- statsmodels 0.14.1

---

# Contributions

## Rebecca Gou

- developed the research design for the project  
- collected sports facility data using the Gaode Maps API  
- created district-level sports facility density measures  
- explored hospital facility data as an additional variable  
- merged environmental indicators with Chinese survey and did data cleaning  
- implemented regression models analyzing sleep outcomes  
- completed all of the data analysis and produced data visualizationss  
- delivered the in-class presentation and contributed to slideshow modification  
- recorded 6-minute explanation of the statistical analysis for the final video  

## Shoshana Abikzer

- collected environmental indicators using the Google Earth Engine API  
- wrote the script `ndvi_viirs_5cities_2023_summer.py` to extract NDVI and nighttime light data  
- aggregated satellite indicators to district-level administrative boundaries  
- generated summary tables used in the analysis  
- aligned environmental indicators with PBICR survey data using district identifiers  
- created validation figures for environmental indicators  
- helped organize the GitHub repository structure  
- wrote and organized the README documentation  
- recorded a 4-minute explanation of environmental data collection for the final project video
- completed slide presentation 

Both members collaborated on **Check-in 1**, **Check-in 2**, and discussion of additional variables and datasets.

---

# AI Usage Statement

The following AI tools were used during this project:

**GitHub Copilot**  
Used for syntax debugging and code suggestions while writing Python scripts and troubleshooting API requests for GEE and Goade.

**Jupyter AI tools**  
Used to help interpret error messages and debug Python code inside the notebook environment.

**OpenAI tools**  
Used to troubleshoot API configuration issues, debug errors, and help organize the README and repo formatting.

**Grammarly**  
Used for spell checking and minor grammar corrections.

All project design, data collection, coding, analysis, and interpretation were completed by the authors, **Shoshana Abikzer and Rebecca Gou**.

---

# Project Links

**Slides used for the in the in-class presentation**

[(link)](https://drive.google.com/file/d/15ZkO6mH8B8EfQjd0j9jbMIVqoZD-o9CG/view)

**Final slides**

[(link)](https://drive.google.com/file/d/1BKIHngTdICLiF_xSSAqNlt_B2oTuDkBO/view?usp=sharing )

**Presentation video**

(link)
