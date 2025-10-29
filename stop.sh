#!/bin/bash

# RunningHub 工作流浏览器 PM2 停止脚本

echo "正在停止 RunningHub 工作流浏览器..."
pm2 stop runninghub-workflow

echo ""
echo "服务已停止"
echo ""
