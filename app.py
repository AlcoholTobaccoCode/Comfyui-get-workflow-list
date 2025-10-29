#!/usr/bin/env python3
"""
RunningHub 工作流浏览器
集成数据采集和 Web 展示功能
"""

from flask import Flask, render_template, jsonify, send_from_directory
from pathlib import Path
import json
import os
from datetime import datetime
import threading
import time
from dotenv import load_dotenv
from fetch_workflows import WorkflowFetcher

app = Flask(__name__)

# 基础目录设置
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# 加载环境变量
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

# 创建必要的目录
DATA_DIR.mkdir(exist_ok=True)
TEMPLATE_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# 全局变量：刷新状态
refresh_status = {
    'is_running': False,
    'current': 0,
    'total': 0,
    'message': '',
    'error': None
}


def get_data_files(search=None):
    """获取所有 JSON 数据文件，按时间戳排序（最新的在前）
    
    参数:
        search: 搜索关键词，如果指定则只返回该关键词的文件
    """
    if not DATA_DIR.exists():
        return []
    
    files = []
    
    if search:
        # 获取指定搜索关键词的文件
        search_dir = DATA_DIR / search
        if search_dir.exists():
            files = list(search_dir.glob("workflows_*.json"))
    else:
        # 兼容旧格式：获取根目录下的文件
        files = list(DATA_DIR.glob("workflows_*.json"))
        
        # 同时获取所有子目录中的文件
        for subdir in DATA_DIR.iterdir():
            if subdir.is_dir():
                files.extend(subdir.glob("workflows_*.json"))
    
    # 按文件修改时间降序排序
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return files


def parse_filename_timestamp(filename):
    """从文件名解析时间戳"""
    try:
        # 从类似 "workflows_202501291430.json" 的文件名提取时间戳
        timestamp_str = filename.stem.split('_')[1]
        dt = datetime.strptime(timestamp_str, "%Y%m%d%H%M")
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return filename.stem


def refresh_data_background(search="换装", max_pages=None):
    """后台刷新数据的函数"""
    global refresh_status
    
    def progress_callback(current, total, message):
        """进度回调函数"""
        refresh_status['current'] = current
        refresh_status['total'] = total
        refresh_status['message'] = message
    
    try:
        refresh_status['is_running'] = True
        refresh_status['current'] = 0
        refresh_status['total'] = 0
        refresh_status['message'] = '开始刷新数据...'
        refresh_status['error'] = None
        
        # 创建采集器并运行（传递页数限制）
        fetcher = WorkflowFetcher(str(BASE_DIR))
        filepath = fetcher.run(search=search, max_pages=max_pages, callback=progress_callback)
        
        if filepath:
            refresh_status['message'] = '数据刷新完成！'
        else:
            refresh_status['error'] = '数据刷新失败'
            
    except Exception as e:
        refresh_status['error'] = f'刷新出错: {str(e)}'
        print(f"后台刷新出错: {e}")
    finally:
        refresh_status['is_running'] = False


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/api/files')
def list_files():
    """API: 获取所有可用的数据文件列表"""
    files = get_data_files()
    file_list = []
    
    for f in files:
        file_list.append({
            'filename': f.name,
            'timestamp': parse_filename_timestamp(f),
            'size': f.stat().st_size
        })
    
    return jsonify(file_list)


@app.route('/api/data/<filename>')
def get_data(filename):
    """API: 获取指定文件的数据"""
    filepath = DATA_DIR / filename
    
    if not filepath.exists() or not filepath.is_file():
        return jsonify({'error': '文件不存在'}), 404
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/latest')
def get_latest():
    """API: 获取最新数据"""
    files = get_data_files()
    
    if not files:
        return jsonify({'error': '没有可用的数据文件'}), 404
    
    latest_file = files[0]
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/search/<path:search>')
def get_search_data(search=''):
    """API: 获取指定搜索关键词的最新数据"""
    # "all" 路径映射回空字符串（获取所有工作流）
    if search == 'all':
        search = ''
    
    # 空搜索使用特殊文件夹名 "all"
    search_key = search if search else 'all'
    files = get_data_files(search_key)
    
    if not files:
        # 没有数据，触发后台抓取
        display_search = search if search else '所有'
        return jsonify({
            'status': 'fetching',
            'message': f'正在获取 "{display_search}" 的数据，请稍候...'
        }), 202
    
    latest_file = files[0]
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/fetch/<path:search>', methods=['POST'])
def trigger_fetch(search=''):
    """API: 触发指定搜索关键词的数据抓取"""
    from flask import request
    global refresh_status
    
    if refresh_status['is_running']:
        return jsonify({
            'success': False,
            'message': '数据抓取正在进行中，请稍候...'
        })
    
    # "all" 路径映射回空字符串（获取所有工作流）
    if search == 'all':
        search = ''
    
    # 获取页数限制参数
    max_pages = None
    if request.is_json:
        data = request.get_json()
        max_pages = data.get('max_pages')
    
    search_param = search
    display_search = search if search else '所有'
    
    # 在后台线程中启动抓取（传递页数限制）
    thread = threading.Thread(
        target=refresh_data_background, 
        args=(search_param, max_pages), 
        daemon=True
    )
    thread.start()
    
    message = f'开始抓取 "{display_search}" 的数据...'
    if max_pages:
        message += f'（最多 {max_pages} 页）'
    
    return jsonify({
        'success': True,
        'message': message
    })


@app.route('/api/total-pages')
def get_total_pages():
    """API: 查询工作流总页数（不抓取数据，只查询第一页获取总数）"""
    import requests
    
    # 从环境变量读取 token
    auth_token = os.getenv("RUNNINGHUB_AUTH_TOKEN")
    
    url = "https://www.runninghub.cn/api/search/workflow"
    
    # 参考 fetch_workflows.py 的完整请求头
    headers = {
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
        headers["authorization"] = auth_token
    
    # 只查询第一页获取总数（参考 fetch_workflows.py 的格式）
    payload = {
        "size": 30,
        "current": 1,
        "search": "",
        "tags": []
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('code') == 0:
            result_data = data.get('data', {})
            # 转换为整数（API 可能返回字符串）
            total = int(result_data.get('total', 0))
            size = int(result_data.get('size', 30))
            total_pages = (total + size - 1) // size  # 向上取整
            
            return jsonify({
                'total_count': total,
                'total_pages': total_pages,
                'page_size': size
            })
        else:
            error_msg = data.get('msg', '查询失败')
            print(f"API 返回错误: code={data.get('code')}, msg={error_msg}")
            return jsonify({'error': error_msg, 'code': data.get('code')}), 400
    except Exception as e:
        print(f"查询总页数异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/searches')
def list_searches():
    """API: 获取所有可用的搜索关键词"""
    if not DATA_DIR.exists():
        return jsonify([])
    
    searches = []
    
    # 获取所有子目录（搜索关键词）
    for subdir in DATA_DIR.iterdir():
        if subdir.is_dir():
            files = list(subdir.glob("workflows_*.json"))
            if files:
                # 获取最新文件的信息
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    searches.append({
                        'keyword': subdir.name,
                        'count': data.get('total_count', 0),
                        'last_update': data.get('fetch_time', '')
                    })
                except:
                    pass
    
    return jsonify(searches)


@app.route('/api/workflow/<workflow_id>')
def get_workflow_detail(workflow_id):
    """API: 获取工作流详细信息（包含 workflowContent）"""
    import requests
    
    # 从环境变量读取 token
    auth_token = os.getenv("RUNNINGHUB_AUTH_TOKEN")
    if not auth_token:
        return jsonify({'error': '未配置 RUNNINGHUB_AUTH_TOKEN 环境变量'}), 500
    
    url = "https://www.runninghub.cn/api/workflow/copy"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": auth_token,
        "content-type": "application/json",
    }
    payload = {
        "workflowId": workflow_id,
        "copyMode": 1
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get('code') == 0:
            return jsonify(result.get('data', {}))
        else:
            return jsonify({'error': result.get('msg', '获取失败')}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """API: 触发后台数据刷新"""
    global refresh_status
    
    if refresh_status['is_running']:
        return jsonify({
            'success': False,
            'message': '数据刷新正在进行中...'
        })
    
    # 在后台线程中启动刷新
    thread = threading.Thread(target=refresh_data_background, daemon=True)
    thread.start()
    
    return jsonify({
        'success': True,
        'message': '已开始刷新数据'
    })


@app.route('/api/refresh/status')
def get_refresh_status():
    """API: 获取刷新状态"""
    return jsonify(refresh_status)


@app.route('/static/<path:path>')
def send_static(path):
    """提供静态文件"""
    return send_from_directory(STATIC_DIR, path)


def init_data():
    """初始化：如果没有数据文件，先获取一次"""
    files = get_data_files()
    if not files:
        print("\n" + "=" * 60)
        print("首次运行，正在获取初始数据...")
        print("=" * 60 + "\n")
        
        fetcher = WorkflowFetcher(str(BASE_DIR))
        fetcher.run()
        
        print("\n初始数据获取完成！")


def run_server(host='127.0.0.1', port=5000, debug=False):
    """运行 Flask 服务器"""
    print(f"\n{'='*60}")
    print(f"RunningHub 工作流浏览器")
    print(f"{'='*60}")
    print(f"服务器地址: http://{host}:{port}")
    print(f"数据目录: {DATA_DIR}")
    print(f"按 Ctrl+C 停止服务器")
    print(f"{'='*60}\n")
    
    # 初始化数据
    init_data()
    
    # 启动服务器
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    # 从环境变量读取端口，默认 5000
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')  # PM2 使用 0.0.0.0
    debug = os.getenv('FLASK_ENV') != 'production'
    
    run_server(host=host, port=port, debug=debug)
