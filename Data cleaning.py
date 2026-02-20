### Created by Yuxuan Gou (Rebecca). Team members: Yuxuan Gou and Shoshana Abikzer.
# It is mainly aout data cleaning and EDA and visualization. 
# I used AI tools solely for debugging and resolving coding errors. All data processing, analysis, interpretation, and writing were completed independently.




### data wrangling
import pandas as pd

### INPUT

SUMMARY_PATH = "sports.xlsx"  


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

### 8) PSQI partial score (0-15, higher = worse)
def to_numeric_safe(s):
    return pd.to_numeric(s, errors="coerce")

# 116/117 hours: treat 24 as 0
bed_h = to_numeric_safe(survey_matched["116、近1个月，您晚上上床睡觉通常是几点钟？"])
wake_h = to_numeric_safe(survey_matched["117、近1个月，您早上起床通常是几点钟？"])

bed_h = bed_h.mask(bed_h == 24, 0)
wake_h = wake_h.mask(wake_h == 24, 0)

bed_min = bed_h * 60
wake_min = wake_h * 60

wake_min_adj = np.where(wake_min <= bed_min, wake_min + 24 * 60, wake_min)
time_in_bed_h = (wake_min_adj - bed_min) / 60

sleep_h = to_numeric_safe(survey_matched["119、近1个月，您每夜通常实际睡眠多少小时（不等于卧床时间）？"])
sleep_eff = 100 * sleep_h / time_in_bed_h

# c_eff
c_eff = pd.Series(np.nan, index=survey_matched.index, dtype="float")
c_eff = c_eff.mask(sleep_eff > 85, 0)
c_eff = c_eff.mask((sleep_eff <= 85) & (sleep_eff >= 75), 1)
c_eff = c_eff.mask((sleep_eff < 75) & (sleep_eff >= 65), 2)
c_eff = c_eff.mask(sleep_eff < 65, 3)

# c_qual
qual = survey_matched["121、您如何评价您的整体睡眠质量?"].astype(str)
c_qual = pd.Series(np.nan, index=survey_matched.index, dtype="float")
c_qual = c_qual.mask(qual == "很好", 0)
c_qual = c_qual.mask(qual == "较好", 1)
c_qual = c_qual.mask(qual == "较差", 2)
c_qual = c_qual.mask(qual == "很差", 3)

# c_lat
lat = survey_matched["118、近1个月，您从上床到入睡通常需要多少分钟?"].astype(str)
c_lat = pd.Series(np.nan, index=survey_matched.index, dtype="float")
c_lat = c_lat.mask(lat == "≤15分钟", 0)
c_lat = c_lat.mask(lat == "16-30分钟", 1)
c_lat = c_lat.mask(lat == "31-60分钟", 2)
c_lat = c_lat.mask(lat.isin([">60分钟", "60分钟"]), 3)

# c_dur
c_dur = pd.Series(np.nan, index=survey_matched.index, dtype="float")
c_dur = c_dur.mask(sleep_h >= 7, 0)
c_dur = c_dur.mask((sleep_h < 7) & (sleep_h >= 6), 1)
c_dur = c_dur.mask((sleep_h < 6) & (sleep_h >= 5), 2)
c_dur = c_dur.mask(sleep_h < 5, 3)

# c_disturb
dist = survey_matched["120、您是否因为半夜或清晨醒来而难以入睡?"].astype(str)
c_disturb = pd.Series(np.nan, index=survey_matched.index, dtype="float")
c_disturb = c_disturb.mask(dist == "无", 0)
c_disturb = c_disturb.mask(dist.isin(["<1次／周", "1次／周"]), 1)
c_disturb = c_disturb.mask(dist == "1-2次／周", 2)
c_disturb = c_disturb.mask(dist == "≥3次／周", 3)

survey_matched["bed_h"] = bed_h
survey_matched["wake_h"] = wake_h
survey_matched["time_in_bed_h"] = time_in_bed_h
survey_matched["sleep_h"] = sleep_h
survey_matched["sleep_eff"] = sleep_eff
survey_matched["c_eff"] = c_eff
survey_matched["c_qual"] = c_qual
survey_matched["c_lat"] = c_lat
survey_matched["c_dur"] = c_dur
survey_matched["c_disturb"] = c_disturb

survey_matched["sleep_quality"] = (
    survey_matched["c_qual"]
    + survey_matched["c_lat"]
    + survey_matched["c_dur"]
    + survey_matched["c_disturb"]
    + survey_matched["c_eff"]
)


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



####10 merge environment file

data_envi = pd.read_csv("ndvi.csv")

survey_matched["district_cn"] = survey_matched["district_cn"].astype(str).str.strip()
data_envi["unit_zh"] = data_envi["unit_zh"].astype(str).str.strip()

survey_matched = survey_matched.merge(
    data_envi,
    how="left",
    left_on="district_cn",
    right_on="unit_zh"
)


#### recode two variables
import pandas as pd
import numpy as np

income_levels = [
    "≤1000",
    "1001-2000",
    "2001-3000",
    "3001-4000",
    "4001-5000",
    "5001-6000",
    "6001-9000",
    "9001-12000",
    "12001-15000",
    "≥15001",
]

survey_matched["income_ord"] = (
    pd.Categorical(
        survey_matched["52、目前您家庭的人均月收入是:（元）"],
        categories=income_levels,
        ordered=True,
    )
    .codes
)

survey_matched.loc[survey_matched["income_ord"] == -1, "income_ord"] = np.nan
survey_matched["income_ord"] = survey_matched["income_ord"] + 1


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


########### regression model
import pandas as pd

import statsmodels.formula.api as smf

survey_matched = survey_matched.rename(columns={
    "年龄": "age",
    "3、您的性别:": "gender",
    "35、您的户口性质:": "hukou",
    "36、您的婚姻情况:": "marital",
    "39、近三个月内，您是否独居": "living_alone_3m",
})

m1_interaction = smf.ols(
    "sleep_quality ~ pss4_total + facility_per_100k_pop "
    "+ age + C(gender) + C(hukou) + C(marital) + C(living_alone_3m) "
    "+ income_ord + edu_ord + viirs_mean + ndvi_mean",
    data=survey_matched
).fit()

print(m1_interaction.summary())


print(list(survey_matched.columns))





###### recode
survey_matched["gender"] = survey_matched["gender"].replace({
    "男": "Male",
    "女": "Female"
})

survey_matched["hukou"] = survey_matched["hukou"].replace({
    "农业": "Rural",
    "非农业": "Urban"
})

survey_matched["marital"] = survey_matched["marital"].replace({
    "已婚（包括初婚有配偶、再婚有配偶、复婚有配偶）": "Married",
    "未婚（单身）": "Never married (single)",
    "未婚（非单身）": "Never married (non-single)",
    "离异": "Divorced",
    "丧偶": "Widowed"
})

survey_matched["living_alone_3m"] = survey_matched["living_alone_3m"].replace({
    "是": "Yes",
    "否": "No"
})



#### descriptive analysis
import numpy as np
import pandas as pd

df = survey_matched.copy()

y = "sleep_quality"
x_num = ["pss4_total", "facility_per_100k_pop", "age", "income_ord", "edu_ord", "viirs_mean", "ndvi_mean"]
x_cat = ["gender", "hukou", "marital", "living_alone_3m"]

cols = [y] + x_num + x_cat
d = df[cols].copy()

for c in [y] + x_num:
    d[c] = pd.to_numeric(d[c], errors="coerce")

numeric_table = []
for c in [y] + x_num:
    s = d[c]
    numeric_table.append({
        "variable": c,
        "N": int(s.notna().sum()),
        "missing": int(s.isna().sum()),
        "missing_pct": float(s.isna().mean() * 100),
        "mean": float(s.mean(skipna=True)),
        "std": float(s.std(skipna=True, ddof=1)),
        "min": float(s.min(skipna=True)),
        "p25": float(s.quantile(0.25)),
        "median": float(s.quantile(0.50)),
        "p75": float(s.quantile(0.75)),
        "max": float(s.max(skipna=True)),
    })

numeric_table = pd.DataFrame(numeric_table)
numeric_table.to_csv("descriptives_numeric.csv", index=False)

cat_rows = []
for c in x_cat:
    vc = d[c].astype("object").where(d[c].notna(), "NA").value_counts(dropna=False)
    total = vc.sum()
    for level, n in vc.items():
        cat_rows.append({
            "variable": c,
            "level": str(level),
            "count": int(n),
            "percent": float(n / total * 100),
        })

categorical_table = pd.DataFrame(cat_rows)
categorical_table.to_csv("descriptives_categorical.csv", index=False)

print(numeric_table)
print(categorical_table.head(30))





################## visualization
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs("figs", exist_ok=True)

df = survey_matched.copy()
df["sleep_quality"] = pd.to_numeric(df["sleep_quality"], errors="coerce")
df["pss4_total"] = pd.to_numeric(df["pss4_total"], errors="coerce")
df["facility_per_100k_pop"] = pd.to_numeric(df["facility_per_100k_pop"], errors="coerce")

# 1) Distribution: sleep_quality
fig = plt.figure(figsize=(8, 6))
ax = plt.gca()
bins = np.arange(-0.5, 15.5 + 1, 1)
ax.hist(df["sleep_quality"].dropna(), bins=bins)
ax.set_title("Distribution: sleep_quality")
ax.set_xlabel("sleep_quality")
ax.set_ylabel("count")
plt.tight_layout()
plt.savefig("figs/1_sleep_quality_distribution.png", dpi=200, bbox_inches="tight")
plt.show()

# 2

os.makedirs("figs", exist_ok=True)

d = survey_matched[["pss4_total", "sleep_quality"]].copy()
d["pss4_total"] = pd.to_numeric(d["pss4_total"], errors="coerce")
d["sleep_quality"] = pd.to_numeric(d["sleep_quality"], errors="coerce")
d = d.dropna()

g = d.groupby("pss4_total")["sleep_quality"].agg(["mean", "count", "std"]).reset_index()
g["se"] = g["std"] / np.sqrt(g["count"])
g["ci95"] = 1.96 * g["se"]

fig = plt.figure(figsize=(8, 6))
ax = plt.gca()
ax.errorbar(g["pss4_total"], g["mean"], yerr=g["ci95"], fmt="o", capsize=4)
ax.plot(g["pss4_total"], g["mean"])
ax.set_title("Mean sleep_quality by pss4_total (95% CI)")
ax.set_xlabel("pss4_total")
ax.set_ylabel("sleep_quality (mean)")

plt.tight_layout()
plt.savefig("figs/stress_sleep_mean_ci.png", dpi=200, bbox_inches="tight")
plt.show()

# 3) Boxplot: sleep by facility quartiles
d3 = df[["facility_per_100k_pop", "sleep_quality"]].dropna().copy()
d3["facility_q"] = pd.qcut(d3["facility_per_100k_pop"], 4, labels=["Q1 (low)", "Q2", "Q3", "Q4 (high)"])
labels = ["Q1 (low)", "Q2", "Q3", "Q4 (high)"]
groups = [d3.loc[d3["facility_q"] == lab, "sleep_quality"].to_numpy() for lab in labels]

fig = plt.figure(figsize=(8, 6))
ax = plt.gca()
ax.boxplot(groups, labels=labels, showfliers=False)
ax.set_title("sleep_quality by facility density quartiles")
ax.set_xlabel("facility_per_100k_pop quartile")
ax.set_ylabel("sleep_quality")
plt.tight_layout()
plt.savefig("figs/3_box_sleep_by_facility_quartile.png", dpi=200, bbox_inches="tight")
plt.show()

print(os.path.abspath("figs"))
