import pandas as pd
import os

def main():
    # Create output directory if it doesn't exist
    os.makedirs('stats_output', exist_ok=True)

    # Read the CSV files
    domestic_df = pd.read_csv('大夫山观赏乔木 - 国内分布.csv', encoding='utf-8', errors='ignore')
    foreign_df = pd.read_csv('大夫山观赏乔木 - 国外分布.csv', encoding='utf-8', errors='ignore')

    # Process domestic data
    domestic_freq = {}  # Mapping for statistical frequency
    for index, row in domestic_df.iterrows():
        tokens = str(row[3]).split('、')  # Column index 4 is 3
        # Handle various delimiters
        tokens = [token.strip() for token in tokens for token in token.split(',')]
        for token in tokens:
            # Determine which region it falls into
            if '台湾' in token:
                key = '台湾地区'
            elif any(x in token for x in ['全国', '各地', '长江流域', '广泛']):
                key = '全国/泛分布'
            else:
                if any(province in token for province in ['广东', '广西', '海南']):
                    key = '华南'
                elif any(province in token for province in ['云南', '贵州', '四川', '重庆', '西藏']):
                    key = '西南'
                elif any(province in token for province in ['上海', '江苏', '浙江', '安徽', '福建', '江西', '山东']):
                    key = '华东'
                elif any(province in token for province in ['河南', '湖北', '湖南']):
                    key = '华中'
                elif any(province in token for province in ['北京', '天津', '河北', '山西', '内蒙古']):
                    key = '华北'
                elif any(province in token for province in ['辽宁', '吉林', '黑龙江']):
                    key = '东北'
                elif any(province in token for province in ['陕西', '甘肃', '青海', '宁夏', '新疆']):
                    key = '西北'
                else:
                    key = '其他/未映射'

            domestic_freq[key] = domestic_freq.get(key, 0) + 1

    total_domestic = sum(domestic_freq.values())
    domestic_stats = pd.DataFrame({'区域': domestic_freq.keys(), '频次': domestic_freq.values()})
    domestic_stats['占比(以物种数n为分母)'] = domestic_stats['频次'] / total_domestic
    domestic_stats.to_csv('stats_output/国内分布_区域统计.csv', index=False)

    # Process foreign data
    foreign_freq = {}  # Mapping for foreign statistics
    for index, row in foreign_df.iterrows():
        token = str(row[3]).strip()
        if token == '无' or token == '/':
            key = '缺失/未记录'
        elif any(country in token for country in ['越南', '泰国', '缅甸', '老挝', '柬埔寨', '马来西亚', '印度尼西亚', '菲律宾', '新加坡', '文莱', '东帝汶']):
            key = '东南亚'
        elif any(country in token for country in ['印度', '斯里兰卡', '尼泊尔', '孟加拉国', '巴基斯坦']):
            key = '南亚'
        elif any(country in token for country in ['日本', '朝鲜', '韩国']):
            key = '东亚'
        elif any(country in token for country in ['澳大利亚', '新西兰']):
            key = '大洋洲'
        elif any(country in token for country in ['墨西哥', '古巴', '美国', '巴西', '阿根廷', '智利', '秘鲁', '加拿大']):
            key = '美洲'
        else:
            key = '其他国家/地区'

        foreign_freq[key] = foreign_freq.get(key, 0) + 1

    total_foreign = sum(foreign_freq.values())
    foreign_stats = pd.DataFrame({'区域': foreign_freq.keys(), '频次': foreign_freq.values()})
    foreign_stats['占比(分母n)'] = foreign_stats['频次'] / total_foreign
    foreign_stats.to_csv('stats_output/国外分布_世界区域统计.csv', index=False)

    # Process distribution types
    distribution_type_freq = {}  # Tracking the distribution types
    for index, row in domestic_df.iterrows():
        foreign_token = str(row[4]).strip()  # Assuming column index for foreign is 4
        if foreign_token == '无' or foreign_token == '/':
            distribution_type = '中国特有分布'
        else:
            world_regions = set()
            if '东亚' in foreign_token:
                world_regions.add('东亚')
            if '东南亚' in foreign_token or '南亚' in foreign_token or '大洋洲' in foreign_token:
                world_regions.add('热带分布')
            if len(world_regions) >= 2:
                distribution_type = '世界分布'
            elif '东亚' in world_regions:
                distribution_type = '温带分布'
            else:
                distribution_type = '世界分布'

        distribution_type_freq[distribution_type] = distribution_type_freq.get(distribution_type, 0) + 1

    total_distribution_types = sum(distribution_type_freq.values())
    distribution_types_stats = pd.DataFrame({'分布型': distribution_type_freq.keys(), '物种数': distribution_type_freq.values()})
    distribution_types_stats['占比(分母n)'] = distribution_types_stats['物种数'] / total_distribution_types
    distribution_types_stats.to_csv('stats_output/五类分布型_统计.csv', index=False)

    # Create README for output directory
    with open('stats_output/README.md', 'w', encoding='utf-8') as readme:
        readme.write("# 统计结果输出\n")
        readme.write("\n## 方法及映射规则\n")
        readme.write("1. 国内分布统计基于区域字典\n")
        readme.write("2. 国外分布根据世界各区域分划\n")
        readme.write("3. 分布型依据定义的规则确定\n")

if __name__ == '__main__':
    main()