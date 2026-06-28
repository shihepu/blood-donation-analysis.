import json

with open('data/network_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

nodes = data.get('nodes', [])
edges = data.get('edges', [])

if not nodes or not edges:
    print("暂无网络数据。")
else:
    total_topics = len(nodes)
    total_edges = len(edges)

    # 高频主题 Top 5
    sorted_nodes = sorted(nodes, key=lambda x: x.get('freq', 0), reverse=True)
    top5 = '、'.join([f'“{n["id"]}”({n["freq"]}次)' for n in sorted_nodes[:5]])

    # 尝试获取权重字段（自动适配）
    def get_weight(e):
        for k in ['value', 'weight', 'count', 'strength']:
            if k in e:
                return e[k]
        return 1

    weighted_edges = [(e, get_weight(e)) for e in edges]
    sorted_edges = sorted(weighted_edges, key=lambda x: x[1], reverse=True)
    top3 = '、'.join([f'“{e[0]["source"]}—{e[0]["target"]}”({e[1]}次)' for e in sorted_edges[:3]])

    # 风险群组识别
    risk_keywords = ['血站', '用血', '报销', '信任', '政策', '管理']
    risk_nodes = [n for n in nodes if any(kw in n['id'] for kw in risk_keywords)]
    risk_ids = {n['id'] for n in risk_nodes}
    connected_risks = [e for e in edges if e['source'] in risk_ids and e['target'] in risk_ids]
    risk_text = ''
    if len(risk_nodes) >= 3 and connected_risks:
        names = '、'.join([f'“{n["id"]}”' for n in risk_nodes[:4]])
        risk_text = f'其中，{names} 等 {len(risk_nodes)} 个主题相互关联紧密，构成舆情风险核心群组。'

    insight = f"""网络共包含 {total_topics} 个主题节点与 {total_edges} 条共现关系（关联边）。
核心高频主题集中于 {top5}。
最强关联边为 {top3}，表明这几组话题在讨论中常被同时提及。
{risk_text} 点击节点可跳转到传播内容侧查看相关视频；悬停查看详情。"""

    print(insight)