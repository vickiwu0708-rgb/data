import csv
import os
from collections import Counter

CN_FILE = "大夫山观赏乔木 - 国内分布.csv"
WW_FILE = "大夫山观赏乔木 - 国外分布.csv"
OUT_DIR = "stats_output"

N_SPECIES_EXPECT = 150  # 文件里应为150条记录（不含表头）

def split_tokens(s: str):
    s = (s or "").strip()
    if not s:
        return []
    # 兼容中英文逗号
    s = s.replace("，", "、").replace(",", "、")
    return [t.strip() for t in s.split("、") if t.strip()]

# ---------- 国内：token -> 区域 ----------
CN_REGION_MAP = {
    "华南": ["广东", "广西", "海南"],
    "西南": ["云南", "贵州", "四川", "重庆", "西藏"],
    "华东": ["上海", "江苏", "浙江", "安徽", "福建", "江西", "山东"],
    "华中": ["河南", "湖北", "湖南"],
    "华北": ["北京", "天津", "河北", "山西", "内蒙古"],
    "东北": ["辽宁", "吉林", "黑龙江"],
    "西北": ["陕西", "甘肃", "青海", "宁夏", "新疆"],
}

def cn_token_to_region(tok: str) -> str:
    # 台湾单列（含“台湾有栽培”等）
    if "台湾" in tok:
        return "台湾地区"
    # 全国/泛分布（你指定2A）
    if ("全国" in tok) or ("各地" in tok) or ("长江流域" in tok) or ("广泛" in tok):
        return "全国/泛分布"
    # 命中省份关键词则归入区域
    for region, keys in CN_REGION_MAP.items():
        for k in keys:
            if k in tok:
                return region
    return "其他/未映射"

# ---------- 国外：token -> 世界大区 ----------
SEA = {"越南","泰国","缅甸","老挝","柬埔寨","马来西亚","印度尼西亚","菲律宾","新加坡","文莱","东帝汶"}
SA  = {"印度","斯里兰卡","尼泊尔","孟加拉国","巴基斯坦"}
EA  = {"日本","朝鲜","韩国"}
OCE = {"澳大利亚","新西兰"}
AME = {"墨西哥","古巴","美国","巴西","阿根廷","智利","秘鲁","加拿大"}

def ww_token_to_region(tok: str) -> str:
    if tok in {"无", "/"}:
        return "缺失/未记录"
    if tok in SEA:
        return "东南亚"
    if tok in SA:
        return "南亚"
    if tok in EA:
        return "东亚"
    if tok in OCE:
        return "大洋洲"
    if tok in AME:
        return "美洲"
    return "其他国家/地区"

# ---------- 五类分布型（每物种唯一归类） ----------
# 你指定：澳大利亚按热带分布（口径B）
TROPICAL_REGIONS = {"东南亚", "南亚", "大洋洲"}  # 大洋洲在此口径下并入热带判定

def five_type(ww_tokens):
    # 中国特有：国外分布为“无”或“/”（你指定）
    if len(ww_tokens) == 1 and ww_tokens[0] in {"无", "/"}:
        return "中国特有分布"

    regions = {ww_token_to_region(t) for t in ww_tokens if t not in {"无", "/"}}
    # 若完全没有效国家（空白等），也按中国特有（与“缺失/未记录”一致处理）
    if not regions:
        return "中国特有分布"

    # 东亚分布：仅出现东亚国家
    if regions.issubset({"东亚"}):
        return "东亚分布"

    # 世界分布：跨两个及以上世界大区（含“其他国家/地区”也算一个大区）
    if len(regions) >= 2:
        return "世界分布"

    # 此时 regions 只有一个值
    only = next(iter(regions))
    if only in TROPICAL_REGIONS:
        return "热带分布"
    if only == "东亚":
        return "温带分布"

    # 兜底：其他国家/地区
    return "世界分布"

def read_col4_tokens(file_path):
    values = []
    with open(file_path, "r", encoding="utf-8", errors="replace", newline="") as f:
        r = csv.reader(f)
        header = next(r, None)
        for row in r:
            if not row:
                continue
            # 第4列索引=3
            s = row[3].strip() if len(row) > 3 else ""
            values.append(split_tokens(s))
    return values

def write_counter_csv(path, counter: Counter, n_species: int, *, include_token_share=True):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    total_tokens = sum(counter.values()) if counter else 0
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        cols = ["类别", "频次", "占比(以物种数n为分母)"]
        if include_token_share:
            cols.append("占比(以token总数为分母)")
        w.writerow(cols)
        for k, v in counter.most_common():
            row = [k, v, f"{v/n_species:.4f}"]
            if include_token_share:
                row.append(f"{(v/total_tokens if total_tokens else 0):.4f}")
            w.writerow(row)

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    cn_tokens_by_row = read_col4_tokens(CN_FILE)
    ww_tokens_by_row = read_col4_tokens(WW_FILE)

    n = len(cn_tokens_by_row)
    if len(ww_tokens_by_row) != n:
        raise RuntimeError(f"国内/国外记录行数不一致：{n} vs {len(ww_tokens_by_row)}")

    # 国内区域频次（token计数）
    cn_region_freq = Counter()
    for toks in cn_tokens_by_row:
        for tok in toks:
            cn_region_freq[cn_token_to_region(tok)] += 1

    # 国外世界区域频次（token计数）
    ww_region_freq = Counter()
    for toks in ww_tokens_by_row:
        for tok in toks:
            ww_region_freq[ww_token_to_region(tok)] += 1

    # 五类分布型（每物种唯一归类）
    five_freq = Counter(five_type(toks) for toks in ww_tokens_by_row)

    write_counter_csv(os.path.join(OUT_DIR, "国内分布_区域统计.csv"), cn_region_freq, n)
    write_counter_csv(os.path.join(OUT_DIR, "国外分布_世界区域统计.csv"), ww_region_freq, n)
    write_counter_csv(os.path.join(OUT_DIR, "五类分布型_统计.csv"), five_freq, n, include_token_share=False)

    # 同时输出一个简单说明
    with open(os.path.join(OUT_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write("# 大夫山观赏乔木 分布统计输出\n\n")
        f.write(f"- 物种记录行数 n={n}\n")
        f.write("- 国内分布：按“、”拆分后，省份关键词映射到中国地理分区；台湾单列；泛描述单列。\n")
        f.write("- 国外分布：按“、”拆分后，国家映射到世界区域；“无”和“/”合并为“缺失/未记录”。\n")
        f.write("- 五类分布型：世界/热带/温带/东亚/中国特有；其中澳大利亚按热带口径处理。\n")

    print(f"OK: 输出已生成在 {OUT_DIR}/ ，物种行数 n={n}")

if __name__ == "__main__":
    main()

