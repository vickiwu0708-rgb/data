import csv
import os
from collections import Counter

CN_FILE = "大夫山观赏乔木 - 国内分布.csv"
WW_FILE = "大夫山观赏乔木 - 国外分布.csv"
OUT_DIR = "stats_output"

# ---------- 工具：编码探测读取 ----------
CANDIDATE_ENCODINGS = ["utf-8-sig", "gb18030", "gbk", "utf-8"]

def open_text_auto(path):
    last_err = None
    for enc in CANDIDATE_ENCODINGS:
        try:
            f = open(path, "r", encoding=enc, errors="strict", newline="")
            # 试读一点点触发解码
            f.read(1024)
            f.seek(0)
            return f, enc
        except Exception as e:
            last_err = e
    # 兜底：用 replace，保证不崩，但可能仍乱码
    f = open(path, "r", encoding="utf-8", errors="replace", newline="")
    return f, "utf-8(replace)"

ZERO_WIDTH = {
    "\ufeff",  # BOM
    "\u200b",  # zero width space
    "\u200c",
    "\u200d",
    "\u2060",
}

def clean_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    for ch in ZERO_WIDTH:
        s = s.replace(ch, "")
    return s.strip()

def split_tokens(s: str):
    s = clean_text(s)
    if not s:
        return []
    # 统一分隔符：中文逗号/英文逗号 -> 顿号
    s = s.replace("，", "、").replace(",", "、")
    return [clean_text(t) for t in s.split("、") if clean_text(t)]

def read_col4_tokens(file_path):
    """
    读取CSV第4列（索引3），按“、/逗号”拆分成 tokens（每行一个 token list）。
    """
    rows = []
    f, enc = open_text_auto(file_path)
    with f:
        r = csv.reader(f)
        header = next(r, None)  # skip header
        for row in r:
            if not row:
                continue
            val = row[3] if len(row) > 3 else ""
            rows.append(split_tokens(val))
    return rows, enc

# ---------- 国内：token -> 区域（七大区 + 台湾单列 + 全国/泛分布单列） ----------
CN_REGION_MAP = {
    "华南": ["广东", "广西", "海南"],
    "西南": ["云南", "贵州", "四川", "重庆", "西藏"],
    "华东": ["上海", "江苏", "浙江", "安徽", "福建", "江西", "山东"],
    "华中": ["河南", "湖北", "湖南"],
    "华北": ["北京", "天津", "河北", "山西", "内蒙古"],
    "东北": ["辽宁", "吉林", "黑龙江"],
    "西北": ["陕西", "甘肃", "青海", "宁夏", "新疆"],
}

MERGE_TO_NATIONAL = {"华东", "华中"}
NATIONAL_KEYWORDS = ["秦岭"]

def cn_token_to_region(tok: str) -> str:
    tok = clean_text(tok)

    if "台湾" in tok:
        return "台湾地区"

    if ("全国" in tok) or ("各地" in tok) or ("长江流域" in tok) or ("广泛" in tok):
        return "全国/泛分布"

    for kw in NATIONAL_KEYWORDS:
        if kw in tok:
            return "全国/泛分布"

    for region, keys in CN_REGION_MAP.items():
        for k in keys:
            if k in tok:
                if region in MERGE_TO_NATIONAL:
                    return "全国/泛分布"
                return region

    return "其他/未映射"

# ---------- 国外：token -> 世界区域 ----------
SEA = {"越南","泰国","缅甸","老挝","柬埔寨","马来西亚","印度尼西亚","菲律宾","新加坡","文莱","东帝汶"}
SA  = {"印度","斯里兰卡","尼泊尔","孟加拉国","巴基斯坦"}
EA  = {"日本","朝鲜","韩国"}
OCE = {"澳大利亚","新西兰"}
AME = {"墨西哥","古巴","美国","巴西","阿根廷","智利","秘鲁","加拿大"}

def ww_token_to_region(tok: str) -> str:
    tok = clean_text(tok)
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
    if "非洲" in tok:
        return "非洲"
    if "地中海" in tok:
        return "地中海"
    return "其他国家/地区"

# ---------- 5类分布型（每物种唯一归类） ----------
# 你确认：澳大利亚按“热带分布”口径
TROPICAL_REGIONS = {"东南亚", "南亚", "大洋洲", "非洲"}
TEMPERATE_REGIONS = {"地中海"}

def _five_type_token(tok: str) -> str:
    if "非洲" in tok or "中南半岛" in tok:
        return "热带"
    if "地中海" in tok:
        return "温带"
    region = ww_token_to_region(tok)
    if region in TROPICAL_REGIONS:
        return "热带"
    if region in TEMPERATE_REGIONS or region == "东亚":
        return "温带"
    if region in {"缺失/未记录"}:
        return "缺失"
    return region

def five_type(ww_tokens):
    ww_tokens = [clean_text(t) for t in ww_tokens if clean_text(t)]

    if len(ww_tokens) == 1 and ww_tokens[0] in {"无", "/"}:
        return "中国特有分布"

    valid = [t for t in ww_tokens if t not in {"无", "/"} and t]
    if not valid:
        return "中国特有分布"

    types = {_five_type_token(t) for t in valid}
    types.discard("缺失")

    if not types:
        return "中国特有分布"

    regions = {ww_token_to_region(t) for t in valid if t not in {"无", "/"}}
    regions.discard("缺失/未记录")

    if regions.issubset({"东亚"}) and not any("非洲" in t or "中南半岛" in t or "地中海" in t for t in valid):
        return "东亚分布"

    if len(types) >= 2:
        return "世界分布"

    only = next(iter(types))
    if only == "热带":
        return "热带分布"
    if only == "温带":
        return "温带分布"

    return "世界分布"

# ---------- 输出 ----------
def write_counter_csv(path, counter: Counter, n_species: int, include_token_share=True):
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

    cn_tokens_by_row, cn_enc = read_col4_tokens(CN_FILE)
    ww_tokens_by_row, ww_enc = read_col4_tokens(WW_FILE)

    n = len(cn_tokens_by_row)
    if len(ww_tokens_by_row) != n:
        raise RuntimeError(f"国内/国外记录行数不一致：{n} vs {len(ww_tokens_by_row)}")

    cn_region_freq = Counter()
    for toks in cn_tokens_by_row:
        seen = set()
        for tok in toks:
            region = cn_token_to_region(tok)
            if region not in seen:
                seen.add(region)
                cn_region_freq[region] += 1

    ww_region_freq = Counter()
    for toks in ww_tokens_by_row:
        seen = set()
        for tok in toks:
            region = ww_token_to_region(tok)
            if region not in seen:
                seen.add(region)
                ww_region_freq[region] += 1

    # 五类分布型（每物种唯一）
    five_freq = Counter(five_type(toks) for toks in ww_tokens_by_row)

    write_counter_csv(os.path.join(OUT_DIR, "国内分布_区域统计.csv"), cn_region_freq, n)
    write_counter_csv(os.path.join(OUT_DIR, "国外分布_世界区域统计.csv"), ww_region_freq, n)
    write_counter_csv(os.path.join(OUT_DIR, "五类分布型_统计.csv"), five_freq, n, include_token_share=False)

    with open(os.path.join(OUT_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write("# 分布统计输出（自动编码识别版）\n\n")
        f.write(f"- 国内文件编码尝试顺序：{', '.join(CANDIDATE_ENCODINGS)}；实际使用：{cn_enc}\n")
        f.write(f"- 国外文件编码尝试顺序：{', '.join(CANDIDATE_ENCODINGS)}；实际使用：{ww_enc}\n")
        f.write(f"- 物种行数 n={n}\n")
        f.write("- 台湾单列；国内泛描述单列。\n")
        f.write("- 国外“无”和“/”合并为“缺失/未记录”。\n")
        f.write("- 5类分布型：世界/热带/温带/东亚/中国特有；澳大利亚按热带口径处理。\n")

    print(f"OK: 输出已生成在 {OUT_DIR}/ ，物种行数 n={n}；国内编码={cn_enc}；国外编码={ww_enc}")

if __name__ == "__main__":
    main()

