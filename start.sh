#!/bin/bash

# RunningHub 工作流浏览器 PM2 启动脚本

# 创建日志目录
mkdir -p logs

# 启动 PM2
pm2 start ecosystem.config.js

# 显示状态
pm2 status

echo ""
echo "=========================================="
echo "RunningHub 工作流浏览器已启动"
echo "访问地址: http://localhost:17910"
echo "=========================================="
echo ""
echo "常用命令:"
echo "  查看日志: pm2 logs runninghub-workflow"
echo "  停止服务: pm2 stop runninghub-workflow"
echo "  重启服务: pm2 restart runninghub-workflow"
echo "  删除服务: pm2 delete runninghub-workflow"
echo ""
