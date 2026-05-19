#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D2 调研Agent V2 - 真实WebSearch版本
使用SOLO的WebSearch工具进行真实搜索
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse

# 添加工具路径
sys.path.insert(0, '/workspace/KZCQL/03_执行代码/工具库')

class D2ResearchAgentV2:
    """D2调研Agent V2 - 真实WebSearch版本"""
    
    def __init__(self, topic: str, domain_preference: List[str] = None, 
                 excluded_domains: List[str] = None, time_range: str = None):
        self.topic = topic
        self.domain_preference = domain_preference or []
        self.excluded_domains = excluded_domains or []
        self.time_range = time_range or "7天"
        self.research_data = {
            "主题": topic,
            "调研时间": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "版本": "V2-真实WebSearch",
            "调研维度": {
                "必选维度": ["热点信息", "跨领域关联", "竞品内容分析", "历史案例"],
                "可选维度": []
            },
            "热点信息": [],
            "跨领域关联": [],
            "竞品内容分析": [],
            "历史案例": [],
            "数据支撑": [],
            "人物/金句": [],
            "信息来源清单": [],
            "矛盾信息标注": []
        }
        self.search_count = 0
        self.max_search = 19
        
    def log(self, message: str):
        """打印日志"""
        print(f"[D2-V2] {message}")
        
    def can_search(self) -> bool:
        """检查是否还有搜索预算"""
        return self.search_count < self.max_search
    
    def call_websearch(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        【真实WebSearch】调用SOLO的WebSearch工具
        
        此函数需要在SOLO环境中通过WebSearch工具调用
        返回真实的搜索结果
        """
        if not self.can_search():
            self.log(f"搜索预算已用完，跳过: {query}")
            return []
            
        self.search_count += 1
        self.log(f"搜索 [{self.search_count}/{self.max_search}]: {query}")
        
        # 在SOLO环境中，这里会被WebSearch工具调用替换
        # 返回真实的搜索结果
        
        # 标记：此处需要在SOLO环境中通过WebSearch工具调用
        # 示例调用方式：
        # results = WebSearch(query=query, num=num_results)
        # return self._parse_results(results)
        
        # 当前返回占位符，实际使用时需要替换
        self.log("  ⚠️  请在SOLO环境中使用WebSearch工具调用此函数")
        return []
    
    def _parse_results(self, raw_results) -> List[Dict]:
        """解析WebSearch结果"""
        parsed = []
        for result in raw_results:
            parsed.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
                "source": result.get("source", "WebSearch"),
                "is_real": True
            })
        return parsed
        
    def research_hot_topics(self) -> List[Dict]:
        """调研热点信息"""
        self.log("开始调研热点信息...")
        
        queries = [
            f"{self.topic} 最新",
            f"{self.topic} 2026",
            f"{self.topic} 发布"
        ]
        
        results = []
        for query in queries:
            if not self.can_search():
                break
            search_results = self.call_websearch(query)
            for r in search_results:
                results.append({
                    "标题": r["title"],
                    "来源": r["source"],
                    "时间": datetime.now().strftime("%Y-%m-%d"),
                    "摘要": r["snippet"],
                    "来源URL": r["url"],
                    "is_real": r.get("is_real", True)
                })
                
        seen = set()
        unique_results = []
        for r in results:
            if r["标题"] not in seen and len(unique_results) < 5:
                seen.add(r["标题"])
                unique_results.append(r)
                
        self.log(f"热点信息调研完成: {len(unique_results)}条")
        return unique_results[:3]
        
    def research_cross_domain(self) -> List[Dict]:
        """调研跨领域关联"""
        self.log("开始调研跨领域关联...")
        
        candidate_domains = [
            "电影", "历史", "商业", "设计", "喜剧", 
            "文学", "哲学", "体育", "游戏", "自然科学"
        ]
        
        if self.domain_preference:
            candidate_domains = self.domain_preference + [d for d in candidate_domains if d not in self.domain_preference]
        if self.excluded_domains:
            candidate_domains = [d for d in candidate_domains if d not in self.excluded_domains]
            
        results = []
        for domain in candidate_domains[:5]:
            if not self.can_search():
                break
                
            query = f"{self.topic} {domain}"
            search_results = self.call_websearch(query, num_results=3)
            
            if search_results:
                results.append({
                    "领域": domain,
                    "关联点": f"{self.topic}与{domain}的内在联系",
                    "灵感方向": f"从{domain}视角切入{self.topic}",
                    "参考来源": search_results[0]["url"] if search_results else ""
                })
                
        self.log(f"跨领域关联调研完成: {len(results)}个领域")
        return results[:3]
        
    def research_competitors(self) -> List[Dict]:
        """调研竞品内容"""
        self.log("开始调研竞品内容...")
        
        queries = [
            f"{self.topic} 公众号",
            f"{self.topic} 深度",
            f"{self.topic} 分析"
        ]
        
        results = []
        for query in queries:
            if not self.can_search():
                break
            search_results = self.call_websearch(query)
            for r in search_results:
                results.append({
                    "文章标题": r["title"],
                    "作者/平台": r.get("source", "未知平台"),
                    "角度": "待分析",
                    "数据表现": "待获取",
                    "可借鉴点": "待总结",
                    "来源URL": r["url"]
                })
                
        seen = set()
        unique_results = []
        for r in results:
            if r["文章标题"] not in seen and len(unique_results) < 5:
                seen.add(r["文章标题"])
                unique_results.append(r)
                
        self.log(f"竞品内容调研完成: {len(unique_results)}篇")
        return unique_results[:3]
        
    def research_history(self) -> List[Dict]:
        """调研历史案例"""
        self.log("开始调研历史案例...")
        
        queries = [
            f"{self.topic} 历史",
            f"{self.topic} 之前",
            f"{self.topic} 起源"
        ]
        
        results = []
        for query in queries:
            if not self.can_search():
                break
            search_results = self.call_websearch(query)
            for r in search_results:
                results.append({
                    "案例": r["title"],
                    "角度": "历史回顾角度",
                    "与当前主题的关联": f"与{self.topic}的发展轨迹相似",
                    "参考来源": r["url"]
                })
                
        seen = set()
        unique_results = []
        for r in results:
            if r["案例"] not in seen and len(unique_results) < 4:
                seen.add(r["案例"])
                unique_results.append(r)
                
        self.log(f"历史案例调研完成: {len(unique_results)}个")
        return unique_results[:2]
        
    def execute_research(self) -> Dict:
        """执行完整调研流程"""
        self.log(f"开始调研主题: {self.topic}")
        self.log(f"搜索预算: {self.max_search}次")
        
        self.research_data["热点信息"] = self.research_hot_topics()
        self.research_data["跨领域关联"] = self.research_cross_domain()
        self.research_data["竞品内容分析"] = self.research_competitors()
        self.research_data["历史案例"] = self.research_history()
        
        sources = set()
        for item in self.research_data["热点信息"]:
            sources.add(item.get("来源", "未知"))
        for item in self.research_data["竞品内容分析"]:
            sources.add(item.get("作者/平台", "未知"))
        self.research_data["信息来源清单"] = list(sources)
        
        self.log(f"调研完成! 总搜索次数: {self.search_count}/{self.max_search}")
        return self.research_data
        
    def quality_check(self) -> Dict:
        """执行质量检查"""
        checks = {
            "热点信息数量": len(self.research_data["热点信息"]) >= 3,
            "跨领域关联数量": len(self.research_data["跨领域关联"]) >= 3,
            "竞品内容数量": len(self.research_data["竞品内容分析"]) >= 3,
            "历史案例数量": len(self.research_data["历史案例"]) >= 2,
            "信息来源标注": len(self.research_data["信息来源清单"]) > 0
        }
        
        passed = sum(checks.values())
        total = len(checks)
        
        return {
            "检查项": checks,
            "通过数": passed,
            "总数": total,
            "质量状态": "通过" if passed == total else "部分通过"
        }
        
    def generate_markdown_report(self) -> str:
        """生成Markdown格式的调研报告"""
        md = f"""---
title: {self.topic}_信息地图
agent: D2-V2
created_at: {self.research_data['调研时间']}
dimensions_completed: {', '.join(self.research_data['调研维度']['必选维度'])}
quality_check: {self.quality_check()['质量状态']}
---

# {self.topic} - 信息地图 (V2真实WebSearch版本)

## 调研概览

- **主题**: {self.topic}
- **调研时间**: {self.research_data['调研时间']}
- **版本**: V2-真实WebSearch
- **搜索次数**: {self.search_count}/{self.max_search}
- **质量状态**: {self.quality_check()['质量状态']}

## 热点信息

"""
        
        for i, item in enumerate(self.research_data["热点信息"], 1):
            md += f"""### {i}. {item['标题']}
- **来源**: {item['来源']}
- **时间**: {item['时间']}
- **摘要**: {item['摘要']}
- **链接**: {item['来源URL']}

"""
            
        md += "## 跨领域关联\n\n"
        for i, item in enumerate(self.research_data["跨领域关联"], 1):
            md += f"""### {i}. {item['领域']}领域
- **关联点**: {item['关联点']}
- **灵感方向**: {item['灵感方向']}
- **参考来源**: {item['参考来源']}

"""
            
        md += "## 竞品内容分析\n\n"
        for i, item in enumerate(self.research_data["竞品内容分析"], 1):
            md += f"""### {i}. {item['文章标题']}
- **作者/平台**: {item['作者/平台']}
- **切入角度**: {item['角度']}
- **数据表现**: {item['数据表现']}
- **可借鉴点**: {item['可借鉴点']}
- **链接**: {item['来源URL']}

"""
            
        md += "## 历史案例\n\n"
        for i, item in enumerate(self.research_data["历史案例"], 1):
            md += f"""### {i}. {item['案例']}
- **切入角度**: {item['角度']}
- **与当前主题的关联**: {item['与当前主题的关联']}
- **参考来源**: {item['参考来源']}

"""
            
        md += f"""## 信息来源清单

{chr(10).join(['- ' + s for s in self.research_data['信息来源清单']])}

## 质量检查

"""
        qc = self.quality_check()
        for check, passed in qc["检查项"].items():
            status = "✅" if passed else "❌"
            md += f"- {status} {check}\n"
            
        md += f"\n**总体**: {qc['通过数']}/{qc['总数']} 项通过\n"
        
        return md
        
    def save_report(self, output_dir: str = None) -> str:
        """保存调研报告"""
        if output_dir is None:
            date_str = datetime.now().strftime("%Y%m%d")
            topic_key = self.topic[:20]
            output_dir = f"/workspace/KZCQL/04_工作区/产出归档/{date_str}_{topic_key}/调研"
            
        os.makedirs(output_dir, exist_ok=True)
        
        md_path = os.path.join(output_dir, f"{topic_key}_信息地图_V2.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self.generate_markdown_report())
            
        json_path = os.path.join(output_dir, f"{topic_key}_信息地图_V2.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.research_data, f, ensure_ascii=False, indent=2)
            
        self.log(f"报告已保存:")
        self.log(f"  - Markdown: {md_path}")
        self.log(f"  - JSON: {json_path}")
        
        return output_dir


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='D2 调研Agent V2 - 真实WebSearch版本')
    parser.add_argument('topic', help='调研主题')
    parser.add_argument('--domain-preference', nargs='+', help='领域偏好')
    parser.add_argument('--exclude-domain', nargs='+', help='排除领域')
    parser.add_argument('--time-range', default='7天', help='时间范围')
    parser.add_argument('--output-dir', help='输出目录')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("D2 调研Agent V2 - 真实WebSearch版本")
    print("=" * 60)
    print(f"主题: {args.topic}")
    print()
    print("⚠️  注意：此版本需要在SOLO环境中通过WebSearch工具调用")
    print("   请确保在SOLO环境中运行，并使用WebSearch工具进行搜索")
    print("=" * 60)
    print()
    
    agent = D2ResearchAgentV2(
        topic=args.topic,
        domain_preference=args.domain_preference,
        excluded_domains=args.exclude_domain,
        time_range=args.time_range
    )
    
    result = agent.execute_research()
    qc = agent.quality_check()
    output_dir = agent.save_report(args.output_dir)
    
    print("\n" + "=" * 60)
    print("调研完成!")
    print("=" * 60)
    print(f"主题: {args.topic}")
    print(f"搜索次数: {agent.search_count}/{agent.max_search}")
    print(f"质量检查: {qc['质量状态']} ({qc['通过数']}/{qc['总数']})")
    print(f"输出目录: {output_dir}")
    print("=" * 60)


if __name__ == '__main__':
    main()
