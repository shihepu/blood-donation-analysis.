#!/usr/bin/env python3
import pandas as pd
import json
import os
import random
def load_full_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BIG_THEMES = ['献血动机与心理认知', '献血流程与现场服务', '献血后健康与副作用', '血站管理与用血政策', '其他']

def get_top_comments_by_title(comments, video_title, top_n=5):
    """根据视频标题筛选评论，按点赞数排序取前N条"""
    matched = []
    for comment in comments:
        if comment.get('视频标题') == video_title:
            matched.append(comment)
    # 按点赞数降序
    matched.sort(key=lambda x: x.get('点赞数', 0), reverse=True)
    return matched[:top_n]

def process_video_data():
    input_file = os.path.join(BASE_DIR, 'video_analysis_results.xlsx')
    full_data_path = os.path.join(BASE_DIR,'data', 'full_data.json')
    output_dir = os.path.join(BASE_DIR, 'data')
    output_file = os.path.join(output_dir, 'video_data.json')
    
    os.makedirs(output_dir, exist_ok=True)
    
    full_comments = load_full_data(full_data_path)
    df = pd.read_excel(input_file)
    print(f"读取Excel文件成功，共 {len(df)} 行数据")
    
    videos = []
    theme_labels = BIG_THEMES
    
    for idx, row in df.iterrows():
        title = str(row.get('视频标题', f'视频{idx+1}'))
        oss_url = str(row.get('B站视频直链', ''))
        author = str(row.get('B站UP主', '未知'))
        publish_time = str(row.get('发布时间', '未知'))
        views = int(row.get('播放量', 0))
        likes = int(row.get('点赞数', 0))
        small_themes = str(row.get('视频小主题', '')).split(',') if pd.notna(row.get('视频小主题')) else []
        small_themes = [t.strip() for t in small_themes if t.strip()]
        big_theme = str(row.get('视频大主题', ''))
        core_view = str(row.get('视频核心观点', '暂无核心观点'))
        
        # 从OSS URL提取BV号，转换为B站嵌入式链接
        import re
        bv_match = re.search(r'(BV\w+)', oss_url)
        if bv_match:
            bvid = bv_match.group(1)
            embed_url = f'https://player.bilibili.com/player.html?bvid={bvid}&page=1&high_quality=1'
        else:
            embed_url = oss_url
        
        video_big_themes = [t.strip() for t in re.split(r'[,，、\s]+', big_theme) if t.strip()]
        video_radar = [1 if theme in video_big_themes else 0 for theme in BIG_THEMES]
        video_comments = [c for c in full_comments if c.get('视频标题') == title]
        
        # 初始化计数
        big_counts = {theme: 0 for theme in BIG_THEMES}
        for comment in video_comments:
            # 获取评论的大主题列表
            comment_big_list = comment.get('大主题列表', [])
            if isinstance(comment_big_list, str):
                try:
                    comment_big_list = eval(comment_big_list)
                except:
                    comment_big_list = []
            if isinstance(comment_big_list, list):
                for theme in comment_big_list:
                    if theme in big_counts:
                        big_counts[theme] += 1
        
        total_big = sum(big_counts.values())
        if total_big > 0:
            # 评论雷达（百分比）
            comment_radar = [round(big_counts[t] / total_big * 100, 1) for t in BIG_THEMES]
            # 评论计数分布（用于柱状图）
            comment_counts = [big_counts[t] for t in BIG_THEMES]
        else:
            comment_radar = [0] * 5
            comment_counts = [0] * 5
        video = {
            "id": idx,
            "title": title,
            "url": embed_url,
            "mp4_url": oss_url,
            "author": author if author else "未知",
            "views": views,
            "likes": likes,
            "publish_time": publish_time,
            "tags": small_themes if small_themes else ["无偿献血"],
            "theme_labels": theme_labels,
            "视频雷达": video_radar,               # 视频传播倾向（0/1）
            "评论雷达": comment_radar,             # 评论接收比例（百分比）
            "评论计数": comment_counts,            # 各主题评论数
            "core_view": core_view,
            "big_themes": video_big_themes
        }
        top_comments_raw = get_top_comments_by_title(full_comments, title, top_n=5)
        top_comments = []
        for c in top_comments_raw:
            top_comments.append({
                'content': c.get('评论内容', ''),
                'likes': c.get('点赞数', 0)
            })
        video["top_comments"] = top_comments  
        videos.append(video)
    
    output_data = {"videos": videos}
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"处理完成！共处理了 {len(videos)} 个视频")
    print(f"输出文件: {output_file}")
    
    return output_data

if __name__ == '__main__':
    process_video_data()