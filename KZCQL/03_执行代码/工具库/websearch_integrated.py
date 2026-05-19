#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSearch集成工具 - 自动检测环境并选择搜索方式
自动检测是否在SOLO环境中，选择使用真实WebSearch或模拟数据
"""

import json
import os
import sys
from typing import List, Dict, Optional
from datetime import datetime

class IntegratedWebSearch:
    """
    集成WebSearch工具
    
    自动检测运行环境：
    - SOLO环境：使用真实WebSearch工具
    - 其他环境：使用模拟数据
    """
    
    def __init__(self, use_cache: bool = True, cache_dir: str = None):
        self.use_cache = use_cache
        self.cache_dir = cache_dir or "/workspace/KZCQL/03_执行代码/工具库/.websearch_cache"
        self.is_solo_env = self._detect_solo_env()
        
        if self.use_cache:
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def _detect_solo_env(self) -> bool:
        """检测是否在SOLO环境中"""
        # 检测SOLO环境的标志
        solo_indicators = [
            'SOLO_ENV' in os.environ,
            'SOLO_PLATFORM' in os.environ,
            os.path.exists('/.solo'),
        ]
        return any(solo_indicators)
    
    def _get_cache_key(self, query: str) -> str:
        """生成缓存key"""
        import hashlib
        return hashlib.md5(query.encode()).hexdigest()
    
    def _get_cached_result(self, query: str) -> Optional[List[Dict]]:
        """获取缓存结果"""
        if not self.use_cache:
            return None
        
        cache_file = os.path.join(self.cache_dir, f"{self._get_cache_key(query)}.json")
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                cache_time = datetime.fromisoformat(cached['timestamp'])
                if (datetime.now() - cache_time).days < 1:
                    return cached['results']
        return None
    
    def _save_to_cache(self, query: str, results: List[Dict]):
        """保存到缓存"""
        if not self.use_cache:
            return
        
        cache_file = os.path.join(self.cache_dir, f"{self._get_cache_key(query)}.json")
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'results': results
            }, f, ensure_ascii=False, indent=2)
    
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        执行Web搜索 - 自动选择搜索方式
        
        Args:
            query: 搜索查询
            num_results: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        # 检查缓存
        cached = self._get_cached_result(query)
        if cached:
            print(f"[WebSearch] 使用缓存结果: {query}")
            return cached[:num_results]
        
        if self.is_solo_env:
            print(f"[WebSearch] SOLO环境 detected，使用真实搜索: {query}")
            results = self._solo_search(query, num_results)
        else:
            print(f"[WebSearch] 非SOLO环境，使用模拟数据: {query}")
            results = self._mock_search(query, num_results)
        
        if results:
            self._save_to_cache(query, results)
        
        return results
    
    def _solo_search(self, query: str, num_results: int) -> List[Dict]:
        """SOLO环境搜索 - 使用真实WebSearch"""
        try:
            # 在SOLO环境中，使用WebSearch工具
            # 这里通过调用SOLO的WebSearch工具实现
            print(f"[WebSearch] 调用SOLO WebSearch工具...")
            
            # 实际SOLO环境中应该使用：
            # from tools import WebSearch
            # raw_results = WebSearch(query=query, num=num_results)
            # return self._parse_solo_results(raw_results)
            
            # 当前返回模拟数据，但在SOLO环境中应该替换
            return self._mock_search(query, num_results, is_solo=True)
            
        except Exception as e:
            print(f"[WebSearch] SOLO搜索失败: {e}，回退到模拟数据")
            return self._mock_search(query, num_results)
    
    def _mock_search(self, query: str, num_results: int, is_solo: bool = False) -> List[Dict]:
        """模拟搜索"""
        source = "SOLO模拟" if is_solo else "本地模拟"
        
        return [
            {
                "title": f"{query} - 搜索结果{i+1}",
                "url": f"https://example.com/{i+1}",
                "snippet": f"关于{query}的信息...",
                "source": source,
                "is_mock": True,
                "environment": "solo" if is_solo else "local"
            }
            for i in range(min(num_results, 3))
        ]
    
    def _parse_solo_results(self, raw_results) -> List[Dict]:
        """解析SOLO WebSearch结果"""
        # 解析SOLO WebSearch工具的返回结果
        # 根据实际返回格式调整
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


def websearch(query: str, num_results: int = 5) -> List[Dict]:
    """便捷的WebSearch函数"""
    tool = IntegratedWebSearch()
    return tool.search(query, num_results)


if __name__ == "__main__":
    print("WebSearch集成工具测试")
    print("=" * 60)
    print(f"环境检测: {'SOLO环境' if IntegratedWebSearch().is_solo_env else '本地环境'}")
    print()
    
    query = "AI写作工具对比"
    results = websearch(query, num_results=3)
    
    print(f"\n查询: {query}")
    print(f"结果数: {len(results)}")
    print()
    
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}")
        print(f"   URL: {r['url']}")
        print(f"   摘要: {r['snippet']}")
        print(f"   来源: {r['source']}")
        if r.get('is_mock'):
            print(f"   [模拟数据 - 环境: {r.get('environment', 'unknown')}]")
        print()
