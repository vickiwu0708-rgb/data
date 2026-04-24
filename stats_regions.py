import csv
from collections import Counter, defaultdict

CN_FILE = "大夫山观赏乔木 - 国内分布.csv"
WW_FILE = "大夫山观赏乔木 - 国外分布.csv"

def split_tokens(s):
    s = (s or "").strip()
    if not s:
        return []
    # 统一全角/半角顿号与中点
    s = s.replace("，", "、").replace(",", "、")
    return [t.strip() for t in s.split("、") if t.strip()]

# ------- 国内：token -> 区域 -------
cn_region_map = {
    "华南": ["广东", "广西", "海南"],
    "西南": ["云南", "贵州", "四川", "重庆", "西藏"],
    "华东": ["上海", "江苏", "浙江", "安徽", "福建", "江西", "山东"],
    "华中": ["河南", "湖北", "湖南"],
    "华北": ["北京", "天津", "河北", "山西", "内蒙古"],
    "东北": ["辽宁", "吉林", "黑龙江"],
    "西北": ["陕西", "甘肃", "青海", "宁夏", "新疆"],
}

def cn_token_to_region(tok):
    # 台湾单列；“台湾有栽培”等按台湾处理
    if "台湾" in tok:
        return "台湾地区"
    # 全国/泛分布
    if ("全国" in tok) or ("各地" in tok) or ("长江流域" in tok) or ("广泛" in tok):
        return "全国/泛分布"
    # 按关键词命中省份
    for region, keys in cn_region_map.items():
        for k in keys:
            if k in tok:
                return region
    return "其他/未映射"

# ------- 国外：token -> 世界大区 -------
sea = {"越南","泰国","缅甸","老挝","柬埔寨","马来西亚","印度尼西亚","菲律宾","新加坡","文莱","东帝汶"}
sa  = {"印度","斯里兰卡","尼泊尔","孟加拉国","巴基斯坦"}
ea  = {"日本","朝鲜","韩国"}
oce = {"澳大利亚","新西兰"}
ame = {"墨西哥","古巴","美国","巴西","阿根廷","智利","秘鲁","加拿大"}  # 按需扩展
def ww_token_to_region(tok):
    if tok in {"无", "/"}:
        return "缺失/未记录"
    if tok in sea:
        return "东南亚"
    if tok in sa:
        return "南亚"
    if tok in ea:
        return "东亚"
    if tok in oce:
        return "大洋洲"
    if tok in ame:
        return "美洲"
    # 兜底：未在映射表内的国家/地区，先归为“其他国家/地区”
    return "其他国家/地区"

# ------- 读取并统计 -------
def read_col4(file):
    rows = []
    with open(file, "r", encoding="utf-8", errors="ignore", newline="") as f:
        r = csv.reader(f)
        for i, row in enumerate(r):
            if i == 0:
                continue
            if len(row) < 4:
                continue
            rows.append(row[3].strip())
    return rows

cn_col = read_col4(CN_FILE)
ww_col = read_col4(WW_FILE)
assert len(cn_col) == len(ww_col), (len(cn_col), len(ww_col))
n = len(cn_col)

# 1) 国内区域频次
cn_region_freq = Counter()
for s in cn_col:
    for tok in split_tokens(s):
        cn_region_freq[cn_token_to_region(tok)] += 1

# 2) 国外世界大区频次
ww_region_freq = Counter()
ww_tokens_by_row = []
for s in ww_col:
    toks = split_tokens(s)
    ww_tokens_by_row.append(toks)
    for tok in toks:
        ww_region_freq[ww_token_to_region(tok)] += 1

# 3) 五类分布型（每行唯一）
def five_type(i):
    toks = ww_tokens_by_row[i]
    if len(toks) == 1 and toks[0] in {"无", "/"}:
        return "中国特有分布"

    regions = set(ww_token_to_region(t) for t in toks if t not in {"无","/"})
    # 若只有“缺失/未记录”，也按中国特有（与你规则一致）
    if not regions:
        return "中国特有分布"

    # 东亚分布：只出现东亚国家
    if regions.issubset({"东亚"}):
        return "东亚分布"

    # 世界分布：跨两个及以上世界大区（排除“其他国家/地区”可按需处理；此处计入跨区）
    core = {r for r in regions if r != "缺失/未记录"}
    if len(core) >= 2:
        return "世界分布"

    # 热带/温带判定：澳大利亚视作热带（你指定）
    # 简化规则：东南亚/南亚/大洋洲(含澳大利亚) -> 热带；仅东亚 -> 温带
    if core.issubset({"东南亚","南亚","大洋洲"}):
        return "热带分布"
    if core.issubset({"东亚"}):
        return "温带分布"

    # 兜底
    return "世界分布"

five = Counter(five_type(i) for i in range(n))

def print_table(title, counter):
    print("\n" + title)
    for k,v in counter.most_common():
        print(f"{k}\t{v}\t{v/n:.4f}")

print_table("国内分布（区域频次）", cn_region_freq)
print_table("国外分布（世界大区频次）", ww_region_freq)
print_table("五类分布型（每物种唯一归类）", five)
print(f"\n物种数 n={n}")