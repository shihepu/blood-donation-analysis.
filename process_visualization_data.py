#!/usr/bin/env python3
"""
数据预处理脚本：从 full_data.json 生成箱型图数据和河流图数据
用于 "热血心声" 系统的公众反馈侧可视化

使用方法:
    python process_visualization_data.py

前置条件:
    data/full_data.json 必须存在

输出文件:
    data/boxplot_data.json
    data/stream_data.json
"""

import json
import os
from collections import defaultdict
import sys

# ==================== 配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# 大主题定义（固定5个）
BIG_THEMES = [
    '献血动机与心理认知',
    '献血流程与现场服务',
    '献血后健康与副作用',
    '血站管理与用血政策',
    '其他'
]

# 大主题颜色映射（与网络图保持一致）
BIG_THEME_COLORS = {
    '献血动机与心理认知': '#e41a1c',
    '献血流程与现场服务': '#377eb8',
    '献血后健康与副作用': '#4daf4a',
    '血站管理与用血政策': '#984ea3',
    '其他': '#ff7f00'
}

# 小主题 → 大主题 映射表（22个小主题）
THEME_MAPPING = {
    # 献血动机与心理认知
    '社会责任': '献血动机与心理认知',
    '献血动机': '献血动机与心理认知',
    '献血光荣': '献血动机与心理认知',
    '献血上瘾': '献血动机与心理认知',
    '献血恐惧': '献血动机与心理认知',
    '献血奖励': '献血动机与心理认知',
    # 献血流程与现场服务
    '献血条件': '献血流程与现场服务',
    '献血体验': '献血流程与现场服务',
    '医护服务': '献血流程与现场服务',
    '信息咨询': '献血流程与现场服务',
    '献血记录': '献血流程与现场服务',
    '献血量与频率': '献血流程与现场服务',
    # 献血后健康与副作用
    '献血有益健康': '献血后健康与副作用',
    '献血副作用': '献血后健康与副作用',
    # 血站管理与用血政策
    '血站信任': '血站管理与用血政策',
    '报销问题': '血站管理与用血政策',
    '用血收费': '血站管理与用血政策',
    '血液管理': '血站管理与用血政策',
    '政策讨论': '血站管理与用血政策',
    '献血证作用': '血站管理与用血政策',
    '稀有血型讨论': '血站管理与用血政策',
    # 其他
    '其他': '其他'
}

# 所有小主题列表
ALL_SUB_THEMES = list(THEME_MAPPING.keys())

# 平台列表
PLATFORMS = ['B站', '微博', '抖音', '知乎']


# ==================== 辅助函数 ====================

def parse_sub_themes(sub_theme_detail_str):
    """
    解析小主题详情字符串，返回列表 [{'主题': 'xxx', '情感得分': 0.5}, ...]
    支持两种格式：
    1. JSON 格式: [{"主题": "社会责任", "情感得分": 0.52}, ...]
    2. Python 字典字符串格式: [{'主题': '社会责任', '情感得分': 0.52}, ...]
    """
    if not sub_theme_detail_str or sub_theme_detail_str == '[]':
        return []
    
    try:
        return json.loads(sub_theme_detail_str)
    except json.JSONDecodeError:
        try:
            fixed = sub_theme_detail_str.replace("'", '"')
            return json.loads(fixed)
        except json.JSONDecodeError:
            return []


def extract_year(month_str):
    """从月份字符串中提取年份"""
    if not month_str or month_str == '未知':
        return None
    try:
        if '-' in month_str:
            return month_str.split('-')[0]
        elif '年' in month_str:
            return month_str.split('年')[0]
        else:
            return month_str[:4] if len(month_str) >= 4 else None
    except:
        return None


# ==================== 主处理函数 ====================

def process_data():
    """主处理函数"""
    
    # 1. 检查数据目录是否存在
    if not os.path.exists(DATA_DIR):
        print(f"❌ 错误: 数据目录不存在 {DATA_DIR}")
        print("   请确保 data/ 目录存在")
        sys.exit(1)
    
    # 2. 加载数据
    input_file = os.path.join(DATA_DIR, 'full_data.json')
    if not os.path.exists(input_file):
        print(f"❌ 错误: 找不到文件 {input_file}")
        print("   请确保 data/full_data.json 存在")
        print("   该文件是从原始评论数据预处理后生成的总数据集")
        sys.exit(1)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        full_data = json.load(f)
    
    print(f"✅ 加载评论数据: {len(full_data)} 条")
    
    # 检查数据是否为空
    if len(full_data) == 0:
        print("⚠️ 警告: full_data.json 为空，没有数据可处理")
        sys.exit(0)
    
    # ============================================================
    # 2. 生成箱型图数据 (boxplot_data.json)
    # ============================================================
    # 数据结构:
    #   - 情感模式: 每条记录 = 一条评论对一个主题的情感得分
    #   - 频次模式: 每条记录 = 一个平台 × 一个主题的评论总数
    
    print("\n" + "="*50)
    print("📊 生成箱型图数据...")
    print("="*50)
    
    # 2.1 情感模式数据: 展开每条评论的每个主题
    sentiment_records = []
    
    for item in full_data:
        platform = item.get('平台', '未知')
        if platform not in PLATFORMS:
            continue
        
        sub_details = parse_sub_themes(item.get('小主题详情', ''))
        if not sub_details:
            continue
        
        for detail in sub_details:
            sub_theme = detail.get('主题', '')
            if not sub_theme or sub_theme not in THEME_MAPPING:
                continue
            
            sentiment = detail.get('情感得分', 0.5)
            big_theme = THEME_MAPPING[sub_theme]
            
            # 小主题级别记录
            sentiment_records.append({
                'platform': platform,
                'theme_level': '小',
                'theme_name': sub_theme,
                'big_theme': big_theme,
                'sentiment_score': sentiment
            })
            
            # 大主题级别记录
            sentiment_records.append({
                'platform': platform,
                'theme_level': '大',
                'theme_name': big_theme,
                'big_theme': big_theme,
                'sentiment_score': sentiment
            })
    
    # 添加 "总计" 列
    total_sentiment_records = []
    for record in sentiment_records:
        total_sentiment_records.append({
            'platform': '总计',
            'theme_level': record['theme_level'],
            'theme_name': record['theme_name'],
            'big_theme': record['big_theme'],
            'sentiment_score': record['sentiment_score']
        })
    sentiment_records.extend(total_sentiment_records)
    
    print(f"  ✅ 情感模式记录数: {len(sentiment_records)}")
    
    # 2.2 频次模式数据: 按 平台 + 主题层级 + 主题名称 聚合
    freq_agg = defaultdict(int)
    
    for item in full_data:
        platform = item.get('平台', '未知')
        if platform not in PLATFORMS:
            continue
        
        sub_details = parse_sub_themes(item.get('小主题详情', ''))
        if not sub_details:
            continue
        
        # 收集该评论涉及的所有主题（去重）
        sub_themes_in_comment = set()
        big_themes_in_comment = set()
        
        for detail in sub_details:
            sub_theme = detail.get('主题', '')
            if not sub_theme or sub_theme not in THEME_MAPPING:
                continue
            sub_themes_in_comment.add(sub_theme)
            big_themes_in_comment.add(THEME_MAPPING[sub_theme])
        
        # 为每个小主题计数
        for sub_theme in sub_themes_in_comment:
            key = (platform, '小', sub_theme)
            freq_agg[key] += 1
        
        # 为每个大主题计数
        for big_theme in big_themes_in_comment:
            key = (platform, '大', big_theme)
            freq_agg[key] += 1
    
    # 添加 "总计" 列
    total_freq_agg = defaultdict(int)
    for (platform, theme_level, theme_name), count in freq_agg.items():
        # 跳过原有的总计（如果有）
        if platform == '总计':
            continue
        total_key = ('总计', theme_level, theme_name)
        total_freq_agg[total_key] += count
    
    # 合并
    for key, count in total_freq_agg.items():
        freq_agg[key] += count
    
    # 构建频次模式记录
    freq_records = []
    for (platform, theme_level, theme_name), count in freq_agg.items():
        big_theme = theme_name if theme_level == '大' else THEME_MAPPING.get(theme_name, '其他')
        freq_records.append({
            'platform': platform,
            'theme_level': theme_level,
            'theme_name': theme_name,
            'big_theme': big_theme,
            'count': count
        })
    
    print(f"  ✅ 频次模式记录数: {len(freq_records)}")
    
    # 保存箱型图数据（合并情感和频次）
    boxplot_data = {
        'sentiment': sentiment_records,
        'freq': freq_records
    }
    
    boxplot_output = os.path.join(DATA_DIR, 'boxplot_data.json')
    with open(boxplot_output, 'w', encoding='utf-8') as f:
        json.dump(boxplot_data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 已保存: {boxplot_output}")
    
    # ============================================================
    # 3. 生成河流图数据 (stream_data.json)
    # ============================================================
    # 三层结构同时包含: 总数据 + 大主题 + 小主题
    # 每条记录: time, level (总数据/大/小), theme_name, big_theme, color, count, avg_sentiment
    
    print("\n" + "="*50)
    print("🌊 生成河流图数据...")
    print("="*50)
    
    # 3.1 收集所有时间点
    time_points = set()
    for item in full_data:
        year = extract_year(item.get('月份', ''))
        if year:
            time_points.add(year)
    time_points = sorted(list(time_points))
    
    if not time_points:
        print("⚠️ 警告: 没有有效的年份数据，使用默认时间点")
        time_points = ['2023', '2024', '2025', '2026']
    
    print(f"  📅 时间点: {time_points}")
    
    # 3.2 按时间 + 层级 + 主题聚合
    # 结构: agg[time][level][theme_name] = {count, sentiment_sum, sentiment_count, big_theme}
    agg = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
        'count': 0,
        'sentiment_sum': 0,
        'sentiment_count': 0,
        'big_theme': ''
    })))
    
    for item in full_data:
        year = extract_year(item.get('月份', ''))
        if not year or year not in time_points:
            continue
        
        sub_details = parse_sub_themes(item.get('小主题详情', ''))
        if not sub_details:
            continue
        
        # 收集该评论涉及的所有主题
        sub_themes_in_comment = set()
        big_themes_in_comment = set()
        sentiment_map = {}
        
        for detail in sub_details:
            sub_theme = detail.get('主题', '')
            if not sub_theme or sub_theme not in THEME_MAPPING:
                continue
            sentiment = detail.get('情感得分', 0.5)
            big_theme = THEME_MAPPING[sub_theme]
            
            sub_themes_in_comment.add(sub_theme)
            big_themes_in_comment.add(big_theme)
            sentiment_map[sub_theme] = sentiment
        
        # === 总数据 ===
        # 计算该评论所有主题的平均情感得分
        if sentiment_map:
            overall_avg_sent = sum(sentiment_map.values()) / len(sentiment_map)
        else:
            overall_avg_sent = 0.5
        
        agg[year]['总数据']['总数据']['count'] += 1
        agg[year]['总数据']['总数据']['sentiment_sum'] += overall_avg_sent
        agg[year]['总数据']['总数据']['sentiment_count'] += 1
        agg[year]['总数据']['总数据']['big_theme'] = '总数据'
        
        # === 大主题 ===
        for big_theme in big_themes_in_comment:
            # 计算该评论中属于该大主题的所有小主题的平均情感得分
            sub_sentiments = [
                sentiment_map[sub] for sub in sub_themes_in_comment
                if THEME_MAPPING[sub] == big_theme
            ]
            if sub_sentiments:
                avg_sent = sum(sub_sentiments) / len(sub_sentiments)
            else:
                avg_sent = 0.5
            
            agg[year]['大主题'][big_theme]['count'] += 1
            agg[year]['大主题'][big_theme]['sentiment_sum'] += avg_sent
            agg[year]['大主题'][big_theme]['sentiment_count'] += 1
            agg[year]['大主题'][big_theme]['big_theme'] = big_theme
        
        # === 小主题 ===
        for sub_theme in sub_themes_in_comment:
            sentiment = sentiment_map.get(sub_theme, 0.5)
            big_theme = THEME_MAPPING[sub_theme]
            
            agg[year]['小主题'][sub_theme]['count'] += 1
            agg[year]['小主题'][sub_theme]['sentiment_sum'] += sentiment
            agg[year]['小主题'][sub_theme]['sentiment_count'] += 1
            agg[year]['小主题'][sub_theme]['big_theme'] = big_theme
    
    # 3.3 构建河流图数据
    stream_records = []
    
    for time_point in time_points:
        if time_point not in agg:
            continue
        
        # 总数据
        if '总数据' in agg[time_point]:
            data = agg[time_point]['总数据']['总数据']
            stream_records.append({
                'time': time_point,
                'level': '总数据',
                'theme_name': '总数据',
                'big_theme': '总数据',
                'color': '#888888',
                'count': data['count'],
                'avg_sentiment': round(
                    data['sentiment_sum'] / data['sentiment_count'], 3
                ) if data['sentiment_count'] > 0 else 0.5
            })
        
        # 大主题
        if '大主题' in agg[time_point]:
            for big_theme in BIG_THEMES:
                if big_theme in agg[time_point]['大主题']:
                    data = agg[time_point]['大主题'][big_theme]
                    stream_records.append({
                        'time': time_point,
                        'level': '大主题',
                        'theme_name': big_theme,
                        'big_theme': big_theme,
                        'color': BIG_THEME_COLORS.get(big_theme, '#888888'),
                        'count': data['count'],
                        'avg_sentiment': round(
                            data['sentiment_sum'] / data['sentiment_count'], 3
                        ) if data['sentiment_count'] > 0 else 0.5
                    })
        
        # 小主题
        if '小主题' in agg[time_point]:
            for sub_theme in ALL_SUB_THEMES:
                if sub_theme in agg[time_point]['小主题']:
                    data = agg[time_point]['小主题'][sub_theme]
                    big_theme = data['big_theme'] or THEME_MAPPING.get(sub_theme, '其他')
                    stream_records.append({
                        'time': time_point,
                        'level': '小主题',
                        'theme_name': sub_theme,
                        'big_theme': big_theme,
                        'color': BIG_THEME_COLORS.get(big_theme, '#888888'),
                        'count': data['count'],
                        'avg_sentiment': round(
                            data['sentiment_sum'] / data['sentiment_count'], 3
                        ) if data['sentiment_count'] > 0 else 0.5
                    })
    
    print(f"  ✅ 河流图记录数: {len(stream_records)}")
    
    # 保存河流图数据
    stream_output = os.path.join(DATA_DIR, 'stream_data.json')
    with open(stream_output, 'w', encoding='utf-8') as f:
        json.dump(stream_records, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 已保存: {stream_output}")
    
    # ============================================================
    # 4. 统计信息
    # ============================================================
    print("\n" + "="*50)
    print("🎉 数据预处理完成！")
    print("="*50)
    
    # 统计河流图各层级的记录数
    level_counts = defaultdict(int)
    for r in stream_records:
        level_counts[r['level']] += 1
    
    print("\n📋 河流图数据统计（按层级）:")
    for level, count in level_counts.items():
        print(f"  {level}: {count} 条记录")
    
    # 统计时间跨度
    times = sorted(set(r['time'] for r in stream_records))
    print(f"\n📅 时间跨度: {times[0] if times else 'N/A'} ~ {times[-1] if times else 'N/A'}")
    
    print(f"\n📁 输出文件:")
    print(f"  - {boxplot_output}")
    print(f"  - {stream_output}")
    print("\n✅ 现在可以启动前端页面查看箱型图和河流图了！")
    
    return boxplot_data, stream_records


# ==================== 入口 ====================
if __name__ == '__main__':
    process_data()