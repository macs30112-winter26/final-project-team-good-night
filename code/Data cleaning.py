### Author: Yuxuan Gou (Rebecca). Team: Yuxuan Gou and Shoshana Abikzer


### Description of the script 
"""
This code implements a data cleaning and merging pipeline for the project. 
First, it calculates sport facility density per 100,000 residents using district-level population data from the 2020 Census. 
These district-level measures are then merged with individual survey responses. The survey data are further cleaned, and key variables are constructed, 
including a partial PSQI sleep quality score, a PSS-4 stress score, and recoded demographic variables. 
This script prepares the final analytic dataset for subsequent descriptive and regression analyses.
"""


##### AI DISCLOSURE
"""
This script follows the course AI policy. Generative AI (ChatGPT, OpenAI) was used only 
for limited assistance with documentation and code clarity.

Specifically, AI was used to:
- improve code comments and script documentation
- check Python syntax and suggest minor debugging ideas
- help refine descriptions of the data cleaning and data merging workflow

All core code in this script—including data cleaning procedures, data merging steps, 
variable construction, and dataset preparation—was written by the author. 
AI was not used to generate first drafts of the code or to replace course learning objectives.

All AI use has been explicitly disclosed in accordance with the course policy.
"""



### data wrangling
import pandas as pd

### INPUT

SUMMARY_PATH = "sports.xlsx"  


"""
Construct district-level sport facility density measures.

This code merges district-level sport facility counts with population data from the 
2020 China’s Seventh National Population Census using city and district identifiers. 
It then calculates the number of sport facilities per 100,000 residents, checks for 
unmatched districts with missing population data, and exports the resulting dataset 
to an Excel file for subsequent analysis.
"""
### 2020 China’s Seventh National Population Census (2020)
POP_2020 = {
    # ------- Shenzhen -------
    ("Shenzhen","福田区"): 1553225,
    ("Shenzhen","罗湖区"): 1143801,
    ("Shenzhen","南山区"): 1795826,
    ("Shenzhen","盐田区"): 214225,
    ("Shenzhen","宝安区"): 4476554,
    ("Shenzhen","龙岗区"): 3979037,
    ("Shenzhen","龙华区"): 2528872,
    ("Shenzhen","坪山区"): 551333,
    ("Shenzhen","光明区"): 1095289,
    ("Shenzhen","大鹏新区"): 156236,

    # ------- Suzhou  -------
    ("Suzhou","张家港市"): 1432044,
    ("Suzhou","常熟市"):   1677050,
    ("Suzhou","太仓市"):   831113,
    ("Suzhou","昆山市"):   2092496,
    ("Suzhou","吴江区"):   1545023,
    ("Suzhou","吴中区"):   1388972,
    ("Suzhou","相城区"):   891055,
    ("Suzhou","姑苏区"):   924083,
    ("Suzhou","虎丘区"):   832499,  # 高新区、虎丘区

    # ------- Shanghai -------
    ("Shanghai","黄浦区"):  662030,
    ("Shanghai","徐汇区"):  1113078,
    ("Shanghai","长宁区"):  693051,
    ("Shanghai","静安区"):  975707,
    ("Shanghai","普陀区"):  1239800,
    ("Shanghai","虹口区"):  757498,
    ("Shanghai","杨浦区"):  1242548,
    ("Shanghai","闵行区"):  2653489,
    ("Shanghai","宝山区"):  2235218,
    ("Shanghai","嘉定区"):  1834258,
    ("Shanghai","浦东新区"): 5681512,
    ("Shanghai","金山区"):  822776,
    ("Shanghai","松江区"):  1909713,
    ("Shanghai","青浦区"):  1271424,
    ("Shanghai","奉贤区"):  1140872,
    ("Shanghai","崇明区"):  637921,

    # ------- Beijing -------
    ("Beijing","东城区"):   708829,
    ("Beijing","西城区"):  1106214,
    ("Beijing","朝阳区"):  3452460,
    ("Beijing","丰台区"):  2019764,
    ("Beijing","石景山区"): 567851,
    ("Beijing","海淀区"):  3133469,
    ("Beijing","门头沟区"): 392606,
    ("Beijing","房山区"):  1312778,
    ("Beijing","通州区"):  1840295,
    ("Beijing","顺义区"):  1324044,
    ("Beijing","昌平区"):  2269487,
    ("Beijing","大兴区"):  1993591,
    ("Beijing","怀柔区"):  441040,
    ("Beijing","平谷区"):  457313,
    ("Beijing","密云区"):  527683,
    ("Beijing","延庆区"):  345671,

    # ------- Chengdu -------
    ("Chengdu","锦江区"):  902933,
    ("Chengdu","青羊区"):  955954,
    ("Chengdu","金牛区"):  1265398,
    ("Chengdu","武侯区"):  1855186,
    ("Chengdu","成华区"):  1381894,
    ("Chengdu","龙泉驿区"): 1266954 + 79256,
    ("Chengdu","青白江区"):  374800 + 115291,
    ("Chengdu","新都区"):    1233274 + 325192,
    ("Chengdu","温江区"):    755015 + 212853,
    ("Chengdu","双流区"):    2044765 + 615064,
    ("Chengdu","郫都区"):    1277576 + 394449,
    ("Chengdu","新津区"):    254608 + 108983,
    ("Chengdu","金堂县"):    419000 + 381371,
    ("Chengdu","大邑县"):    259291 + 256671,
    ("Chengdu","蒲江县"):    121044 + 134519,
    ("Chengdu","都江堰市"):  436619 + 273437,
    ("Chengdu","彭州市"):    383409 + 396990,
    ("Chengdu","邛崃市"):    322777 + 280196,
    ("Chengdu","崇州市"):    391259 + 344464,
    ("Chengdu","简阳市"):    591224 + 526041,
}

# Load + merge + compute density

df = pd.read_excel(SUMMARY_PATH)

# city, district
df["population_2020"] = df.apply(lambda r: POP_2020.get((r["city"], r["district"])), axis=1)

# facility number per 100000 people
df["facility_per_100k_pop"] = (df["sport_facility_count"] / df["population_2020"] * 100000).round(2)

missing = df[df["population_2020"].isna()][["city", "district", "sport_facility_count"]]
print("Missing population rows:", len(missing))
if len(missing) > 0:
    print(missing)

# save the file
with pd.ExcelWriter("all_cities_sport_density_per_pop_2020.xlsx", engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="density_per_pop_2020")
    if len(missing) > 0:
        missing.to_excel(writer, index=False, sheet_name="missing_population")

print("SAVED: all_cities_sport_density_per_pop_2020.xlsx")
















#################### data cleaning for Chinese survey


"""
Clean the survey data and merge them with district-level sport facility data.

This code restricts the survey sample to respondents from the five target cities,
cleans residence-related variables, keeps only urban respondents, and extracts
province, city, and district information from the reported address. It also
standardizes city and district names in the sport facility dataset and performs
a left join to create the matched analytic dataset for later analysis.
"""
import pandas as pd
import numpy as np
import re

### 1) Read data
data1 = pd.read_excel("survey_China.xlsx")
POI_sports = pd.read_excel("all_cities_sport_density_per_pop_2020.xlsx")
### 2) Quick address substring (first 3 chars)
data1["address"] = data1["17、您现在居住地"].astype(str).str.slice(0, 3)

target_address = ["上海-", "北京-", "广东-", "浙江-", "江苏-", "四川-"]
sub_data = data1[data1["address"].isin(target_address)].copy()

tab = sub_data["34、近三个月您的常住地:"].value_counts(dropna=False)


target_cities = ["上海", "北京", "深圳", "苏州", "成都"]
pattern = "|".join(map(re.escape, target_cities))

sub_data = data1[
    data1["17、您现在居住地"].astype(str).str.contains(pattern, regex=True, na=False)
].copy()

### Clean spaces
sub_data["34、近三个月您的常住地:"] = sub_data["34、近三个月您的常住地:"].astype(str).str.strip()

tab = sub_data["34、近三个月您的常住地:"].value_counts(dropna=False)

### Merge "城镇/城鎮"(towns)
urban = tab.get("城镇", 0) + tab.get("城鎮", 0)
rural = tab.get("农村", 0)

urban_rural_table = {"农村": rural, "城镇": urban}



# 4) Keep only urban samples; normalize label to "城镇"(town))
data1 = sub_data[sub_data["34、近三个月您的常住地:"].isin(["城镇", "城鎮"])].copy()
data1["34、近三个月您的常住地:"] = "城镇"

# 5) Split address into province / city_cn / district_cn
#    Match various dash chars: - – — －
addr = data1["17、您现在居住地"].astype(str).str.replace(r"\s+", " ", regex=True).str.strip()

# split into at most 3 parts
parts = addr.str.split(r"\s*[-–—－]\s*", n=2, expand=True)
data1["province"] = parts[0]
data1["city_cn"] = parts[1] if parts.shape[1] > 1 else np.nan
data1["district_cn"] = parts[2] if parts.shape[1] > 2 else np.nan

# remove trailing "市"(city)
data1["city_cn"] = data1["city_cn"].astype(str).str.replace(r"市$", "", regex=True)
data1["district_cn"] = data1["district_cn"].astype(str).str.strip()

survey2 = data1.copy()

# 6) Recode POI_sports city names + clean district
   

city_map = {
    "Beijing": "北京",
    "Chengdu": "成都",
    "Shenzhen": "深圳",
    "Suzhou": "苏州",
    "Shanghai": "上海",
}

poi2 = POI_sports.copy()
poi2["city_cn"] = poi2["city"].astype(str).map(city_map).fillna(poi2["city"].astype(str))
poi2["district_cn"] = poi2["district"].astype(str).str.strip()

### 7) Left join: survey2 LEFT JOIN poi2 by district
#    (R: left_join(poi2, by = c("district_cn" = "district")))
survey_matched = survey2.merge(
    poi2,
    how="left",
    left_on="district_cn",
    right_on="district",
    suffixes=("", "_poi"),
)













#### 10. Merge environmental data
"""
Merge environmental data and construct key analytic variables.

This code merges the matched survey dataset with district-level environmental data,
then recodes a set of demographic and socioeconomic variables for analysis, including
income, education, gender, hukou status, marital status, living arrangement, age,
and life event exposure. It also constructs the main outcome and predictor measures:
a partial PSQI-based sleep quality score and a PSS-4 perceived stress score.

The resulting dataset contains the individual-, district-, and environmental-level
variables used in subsequent descriptive analysis and regression modeling.
"""
data_envi = pd.read_excel("ndvi.xlsx")

survey_matched["district_cn"] = survey_matched["district_cn"].astype(str).str.strip()
data_envi["unit_zh"] = data_envi["unit_zh"].astype(str).str.strip()

survey_matched = survey_matched.merge(
    data_envi,
    how="left",
    left_on="district_cn",
    right_on="unit_zh"
)


#### recode two variables


col = "52、目前您家庭的人均月收入是:（元）"

survey_matched[col] = survey_matched[col].astype(str).str.strip()

income_map = {
    "≤1000": 1,
    "1001-2000": 2,
    "2001-3000": 3,
    "3001-4000": 4,
    "4001-5000": 5,
    "5001-6000": 6,
    "6001-9000": 7,
    "9001-12000": 8,
    "12001-15000": 9,
    "≥15001": 10,
}

survey_matched["income_code"] = survey_matched[col].map(income_map)

survey_matched["income_code"]



edu_levels = [
    "未接受过正规教育",
    "小学",
    "初中",
    "高中",
    "中专",
    "大专",
    "大学本科",
    "硕士研究生",
    "博士研究生",
]

survey_matched["edu_ord"] = (
    pd.Categorical(
        survey_matched["11、您的最高文化程度（所获得的最高学历）:"],
        categories=edu_levels,
        ordered=True,
    )
    .codes
)

survey_matched.loc[survey_matched["edu_ord"] == -1, "edu_ord"] = np.nan
survey_matched["edu_ord"] = survey_matched["edu_ord"] + 1


list(survey_matched.columns)


###### recode
survey_matched["gender"] = survey_matched['3、您的性别:'].replace({
    "男": "Male",
    "女": "Female"
})

survey_matched["hukou"] = survey_matched["35、您的户口性质:"].replace({
    "农业": "Rural",
    "非农业": "Urban"
})

survey_matched["marital"] = survey_matched["36、您的婚姻情况:"].replace({
    "已婚（包括初婚有配偶、再婚有配偶、复婚有配偶）": "Married",
    "未婚（单身）": "Never married (single)",
    "未婚（非单身）": "Never married (non-single)",
    "离异": "Divorced",
    "丧偶": "Widowed"
})

survey_matched["living_alone_3m"] = survey_matched["39、近三个月内，您是否独居"].replace({
    "是": "Yes",
    "否": "No"
})

survey_matched["age"] = survey_matched["年龄"]



col = '33、您近一年内是否经历以下生活事件?'

s = survey_matched[col].astype("string").str.strip()

# Create binary indicator:
# 0 if exactly "无"
# 1 if non-missing and not "无"
# NA stays NA
survey_matched["life_event_any"] = np.where(
    s.isna(),
    np.nan,
    np.where(s.eq("无"), 0, 1)
).astype("float")

survey_matched['life_event_any'].value_counts()


### 8) PSQI partial score (0-15, higher = worse)


import pandas as pd
import numpy as np

def num(s):
    return pd.to_numeric(s, errors="coerce")

def clean(s):
    return s.astype(str).str.strip().str.replace("/", "／", regex=False)

q116 = "116、近1个月，您晚上上床睡觉通常是几点钟？"
q117 = "117、近1个月，您早上起床通常是几点钟？"
q118 = "118、近1个月，您从上床到入睡通常需要多少分钟?"
q119 = "119、近1个月，您每夜通常实际睡眠多少小时（不等于卧床时间）？"
q120 = "120、您是否因为半夜或清晨醒来而难以入睡?"
q121 = "121、您如何评价您的整体睡眠质量?"

bed = num(survey_matched[q116]).mask(lambda x: x == 24, 0)
wake = num(survey_matched[q117]).mask(lambda x: x == 24, 0)

bed_m = bed * 60
wake_m = wake * 60
wake_m_adj = np.where(wake_m <= bed_m, wake_m + 1440, wake_m)

tib = (wake_m_adj - bed_m) / 60
tib = pd.Series(tib, index=survey_matched.index).mask(lambda x: x <= 0, np.nan)

sleep_h = num(survey_matched[q119])
sleep_eff = 100 * sleep_h / tib
sleep_eff = pd.Series(sleep_eff, index=survey_matched.index).mask(~np.isfinite(sleep_eff), np.nan)

c_eff = pd.Series(np.select(
    [sleep_eff > 85,
     (sleep_eff <= 85) & (sleep_eff >= 75),
     (sleep_eff < 75) & (sleep_eff >= 65),
     sleep_eff < 65],
    [0, 1, 2, 3],
    default=np.nan
), index=survey_matched.index)

c_qual = clean(survey_matched[q121]).map({"很好": 0, "较好": 1, "较差": 2, "很差": 3})

lat_raw = clean(survey_matched[q118])
c_lat = lat_raw.map({
    "≤15分钟": 0,
    "16-30分钟": 1,
    "31-60分钟": 2,
    "60分钟": 2,
    " 60分钟": 2,
    ">60分钟": 3,
    "＞60分钟": 3
})

c_dur = pd.Series(np.select(
    [sleep_h > 7,
     (sleep_h <= 7) & (sleep_h >= 6),
     (sleep_h < 6) & (sleep_h >= 5),
     sleep_h < 5],
    [0, 1, 2, 3],
    default=np.nan
), index=survey_matched.index)

dist_raw = clean(survey_matched[q120])
c_dist = dist_raw.map({
    "无": 0,
    "<1次／周": 1,
    "1次／周": 2,
    "1-2次／周": 2,
    "≥3次／周": 3
})

components = pd.concat(
    [c_qual.rename("c_qual"),
     c_lat.rename("c_lat"),
     c_dur.rename("c_dur"),
     c_dist.rename("c_dist"),
     c_eff.rename("c_eff")],
    axis=1
)

survey_matched["sleep_quality"] = components.sum(axis=1, min_count=5)

survey_matched["sleep_quality"].value_counts(dropna= False)

survey_matched["sleep_quality"].count()

# Reverse the score
survey_matched["sleep_quality_worse"] = survey_matched["sleep_quality"]


survey_matched["sleep_quality"] = 15 - survey_matched["sleep_quality_worse"]

# quick check
print("OLD (higher=worse):")
print(survey_matched["sleep_quality_worse"].describe())

print("\nNEW sleep_quality (higher=better):")
print(survey_matched["sleep_quality"].describe())



### 9) PSS-4 total score calculation
score_map = {"从不": 0, "偶尔": 1, "有时": 2, "经常": 3, "总是": 4}

col1 = "84、请回想最近一个月来，您发生下列状况的频率:—觉得自己无法控制生活中的重要事情"
col2 = "84、对自己处理个人问题的能力没有自信"
col3 = "84、觉得事情进展不顺利"
col4 = "84、感到困难堆积如山，以致无法克服"

survey_matched["pss4_item1"] = survey_matched[col1].map(score_map)
survey_matched["pss4_item2"] = survey_matched[col2].map(score_map)
survey_matched["pss4_item3"] = survey_matched[col3].map(score_map)
survey_matched["pss4_item4"] = survey_matched[col4].map(score_map)

survey_matched["pss4_total"] = (
    survey_matched["pss4_item1"]
    + survey_matched["pss4_item2"]
    + survey_matched["pss4_item3"]
    + survey_matched["pss4_item4"]
)

print(list(survey_matched.columns))

print(survey_matched["city_zh"].value_counts(dropna=False))
print(survey_matched["sport_facility_count"].value_counts(dropna=False))



survey_matched.to_csv("survey_matched.csv", index=False, encoding="utf-8-sig")
