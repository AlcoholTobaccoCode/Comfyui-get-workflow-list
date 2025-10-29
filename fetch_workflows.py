#!/usr/bin/env python3
"""
RunningHub 工作流数据采集器
使用模拟真人请求模式获取所有工作流数据
"""

import requests
import json
import time
import random
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv


class WorkflowFetcher:
    """工作流数据采集器"""
    
    def __init__(self, base_dir: str = None):
        """初始化采集器"""
        self.base_url = "https://www.runninghub.cn/api/search/workflow"
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # 加载环境变量
        env_path = self.base_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        # 从环境变量读取 authorization token
        auth_token = os.getenv("RUNNINGHUB_AUTH_TOKEN")
        if not auth_token:
            print("警告: 未找到 RUNNINGHUB_AUTH_TOKEN 环境变量")
            print("请在 .env 文件中设置 RUNNINGHUB_AUTH_TOKEN")
            print("参考 .env.example 文件")
        
        # 从浏览器请求中提取的请求头
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua": '"Chromium";v="139", "Not;A=Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-language": "en_US",
            "referer": "https://www.runninghub.cn/search?q=%E6%8D%A2%E8%A3%85"
        }
        
        # 如果有 token，添加到 headers
        if auth_token:
            self.headers["authorization"] = auth_token
    
    def human_delay(self, base_delay: float = 1.0, jitter: float = 0.5):
        """
        模拟真人延迟（带抖动算法）
        
        参数:
            base_delay: 基础延迟时间（秒）
            jitter: 最大随机抖动范围（秒）
        """
        # 使用高斯分布添加随机抖动
        delay = base_delay + random.gauss(0, jitter / 2)
        # 确保延迟在合理范围内
        delay = max(0.5, min(delay, base_delay + jitter))
        time.sleep(delay)
    
    def fetch_page(self, page: int, size: int = 30, search: str = "换装") -> Dict[str, Any]:
        """
        获取单页工作流数据
        
        参数:
            page: 页码（从1开始）
            size: 每页数量
            search: 搜索关键词
            
        返回:
            响应数据字典
        """
        payload = {
            "size": size,
            "current": page,
            "search": search,
            "tags": []
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取第 {page} 页时出错: {e}")
            return None
    
    def fetch_all_workflows(self, search: str = "换装", size: int = 30, max_pages=None, callback=None) -> List[Dict[str, Any]]:
        """
        获取所有工作流数据（动态获取所有分页）
        
        参数:
            search: 搜索关键词
            size: 每页数量
            max_pages: 最大抓取页数（None表示抓取所有）
            callback: 进度回调函数
            
        返回:
            所有工作流记录列表
        """
        all_records = []
        page = 1
        
        print(f"开始获取工作流数据，搜索关键词: '{search}'")
        if callback:
            callback(0, 0, f"开始获取数据...")
        
        # 获取第一页以确定总页数（动态获取，不使用固定值）
        first_response = self.fetch_page(page, size, search)
        if not first_response or first_response.get("code") != 0:
            print("获取第一页失败")
            if callback:
                callback(0, 0, "获取第一页失败")
            return []
        
        data = first_response.get("data", {})
        # 动态获取总页数和总记录数
        total_pages = int(data.get("pages", 0))
        total_records = int(data.get("total", 0))
        
        # 如果设置了最大页数限制，使用较小值
        if max_pages:
            total_pages = min(total_pages, max_pages)
            print(f"总页数: {data.get('pages', 0)}（限制为 {max_pages} 页）, 总记录数: {total_records}")
        else:
            print(f"总页数: {total_pages}, 总记录数: {total_records}")
        
        if callback:
            callback(1, total_pages, f"共 {total_pages} 页，{total_records} 条记录")
        
        # 添加第一页记录
        first_page_records = data.get("records", [])
        all_records.extend(first_page_records)
        print(f"已获取 1/{total_pages} 页 - {len(first_page_records)} 条记录")
        
        # 获取剩余页面
        for page in range(2, total_pages + 1):
            # 模拟真人浏览延迟（带抖动）
            base_delay = random.uniform(1.5, 3.0)
            jitter = random.uniform(0.3, 1.0)
            self.human_delay(base_delay, jitter)
            
            response = self.fetch_page(page, size, search)
            if response and response.get("code") == 0:
                records = response.get("data", {}).get("records", [])
                all_records.extend(records)
                print(f"已获取 {page}/{total_pages} 页 - {len(records)} 条记录")
                if callback:
                    callback(page, total_pages, f"已获取 {page}/{total_pages} 页")
            else:
                print(f"获取第 {page} 页失败")
                if callback:
                    callback(page, total_pages, f"第 {page} 页失败")
                # 失败时额外延迟
                time.sleep(random.uniform(3, 5))
        
        print(f"\n总共获取: {len(all_records)} 条记录")
        if callback:
            callback(total_pages, total_pages, f"完成！共 {len(all_records)} 条记录")
        return all_records
    
    def sort_workflows(self, workflows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        对工作流进行排序：按收藏数降序，收藏数相同则按点赞数降序，再按使用次数降序
        
        参数:
            workflows: 工作流记录列表
            
        返回:
            排序后的工作流记录列表
        """
        def sort_key(workflow):
            stats = workflow.get("statisticsInfo", {})
            collect_count = int(stats.get("collectCount", 0))
            like_count = int(stats.get("likeCount", 0))
            use_count = int(stats.get("useCount", 0))
            return (-collect_count, -like_count, -use_count)  # 负数实现降序
        
        return sorted(workflows, key=sort_key)
    
    def save_data(self, workflows: List[Dict[str, Any]], search: str = "") -> str:
        """
        保存工作流数据到 JSON 文件（带时间戳，按搜索关键词分组）
        
        参数:
            workflows: 工作流记录列表
            search: 搜索关键词（空表示所有）
            
        返回:
            保存的文件路径
        """
        # 创建搜索关键词对应的子目录，空搜索使用 "all"
        search_key = search if search else "all"
        search_dir = self.data_dir / search_key
        search_dir.mkdir(exist_ok=True)
        
        # 生成带时间戳的文件名（年月日时分）
        timestamp = datetime.now().strftime("%Y%m%d%H%M")
        filename = f"workflows_{timestamp}.json"
        filepath = search_dir / filename
        
        # 准备数据结构
        data = {
            "fetch_time": datetime.now().isoformat(),
            "total_count": len(workflows),
            "search": search,
            "workflows": workflows
        }
        
        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n数据已保存到: {filepath}")
        return str(filepath)
    
    def run(self, search: str = "换装", max_pages=None, callback=None):
        """
        主执行方法
        
        参数:
            search: 搜索关键词
            max_pages: 最大抓取页数（None表示抓取所有）
            callback: 进度回调函数
            
        返回:
            保存的文件路径
        """
        print("=" * 60)
        print("RunningHub 工作流数据采集器")
        print("=" * 60)
        
        # 获取所有工作流
        workflows = self.fetch_all_workflows(search, max_pages=max_pages, callback=callback)
        
        if not workflows:
            print("未获取到任何工作流数据")
            return None
        
        # 排序工作流
        print("\n正在排序工作流（按点赞数和使用次数）...")
        sorted_workflows = self.sort_workflows(workflows)
        
        # 显示前10名
        print("\n点赞数 Top 10:")
        print("-" * 60)
        for i, workflow in enumerate(sorted_workflows[:10], 1):
            stats = workflow.get("statisticsInfo", {})
            print(f"{i}. {workflow.get('name', '未命名')}")
            print(f"   点赞: {stats.get('likeCount', 0)}, 使用: {stats.get('useCount', 0)}")
        
        # 保存数据
        filepath = self.save_data(sorted_workflows, search)
        
        print("\n" + "=" * 60)
        print("数据采集完成！")
        print("=" * 60)
        
        return filepath


if __name__ == "__main__":
    fetcher = WorkflowFetcher()
    fetcher.run()
