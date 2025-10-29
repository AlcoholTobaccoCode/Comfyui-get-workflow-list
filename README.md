# RunningHub 工作流浏览器

一个用于采集和浏览 RunningHub 平台工作流数据的工具。

## ✨ 功能特性

1. **智能数据采集**
   - 模拟真人请求模式（带抖动算法）
   - 动态获取所有分页数据（自动适应数据量变化）
   - 按点赞数和使用次数排序

2. **Web 可视化界面**
   - 美观的现代化设计
   - 卡片式布局展示工作流
   - 支持后台刷新数据（不影响当前浏览）
   - 历史数据切换
   - 响应式设计

3. **数据管理**
   - 自动保存为 JSON 文件
   - 文件名包含时间戳（年月日时分）
   - 保留历史数据

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd runninghub-workflow

# 如果使用 conda 环境
conda activate runninghub

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置你的 Authorization token
# RUNNINGHUB_AUTH_TOKEN=Bearer your_token_here
```

**如何获取 Authorization Token：**

1. 打开浏览器访问 https://www.runninghub.cn
2. 打开开发者工具 (F12)
3. 切换到 Network 标签
4. 在网站上搜索任意关键词
5. 找到 `workflow` 请求
6. 查看 Request Headers 中的 `authorization` 字段
7. 复制完整的值（包括 "Bearer " 前缀）到 `.env` 文件

### 3. 启动服务

```bash
python app.py
```

首次运行会自动获取初始数据，然后启动 Web 服务器。

### 4. 访问界面

在浏览器中打开：`http://127.0.0.1:5000`

## 🚀 生产环境部署（PM2）

### 使用 PM2 启动

```bash
# 启动服务（端口 17910）
./start.sh

# 或手动启动
pm2 start ecosystem.config.js

# 查看日志
pm2 logs runninghub-workflow

# 停止服务
./stop.sh
# 或
pm2 stop runninghub-workflow

# 重启服务
pm2 restart runninghub-workflow

# 删除服务
pm2 delete runninghub-workflow
```

### 访问地址

生产环境：`http://localhost:17910`

### PM2 配置

- **端口**: 17910
- **实例数**: 1
- **自动重启**: 是
- **内存限制**: 1GB
- **日志目录**: `./logs/`

## 📁 项目结构

```
runninghub-workflow/
├── app.py                 # 主程序（集成数据采集和 Web 服务）
├── fetch_workflows.py     # 数据采集模块
├── requirements.txt       # Python 依赖
├── README.md             # 说明文档
├── data/                 # 数据存储目录
│   └── workflows_*.json  # 采集的数据文件
└── templates/            # HTML 模板
    └── index.html       # Web 界面
```

## 🎯 使用说明

### Web 界面功能

1. **查看工作流**
   - 自动加载最新数据
   - 显示工作流预览图、名称、统计数据
   - 点击卡片可跳转到详情页

2. **刷新数据**
   - 点击「刷新数据」按钮
   - 后台自动获取最新数据
   - 显示实时进度
   - 完成后自动更新文件列表
   - **不影响当前浏览**

3. **切换历史数据**
   - 使用下拉菜单选择不同时间的数据
   - 查看历史趋势

### 数据文件格式

```json
{
  "fetch_time": "2025-01-29T14:30:00",
  "total_count": 513,
  "workflows": [
    {
      "id": "工作流ID",
      "name": "工作流名称",
      "statisticsInfo": {
        "likeCount": "点赞数",
        "useCount": "使用次数",
        "collectCount": "收藏数"
      }
    }
  ]
}
```

## ⚠️ 注意事项

1. **Token 过期**：如果请求失败，需要更新 `fetch_workflows.py` 中的 `authorization` 字段
2. **请求频率**：已内置智能延迟机制（1.5-3秒 + 随机抖动）
3. **数据量变化**：系统会动态获取总页数，自动适应数据量变化
4. **历史数据**：每次刷新都会生成新文件，不会覆盖历史数据

## 🛠️ 技术栈

- **后端**：Python 3, Flask, Requests
- **前端**：HTML5, CSS3, JavaScript
- **数据**：JSON 文件存储

## License
