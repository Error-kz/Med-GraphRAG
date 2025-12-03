#!/bin/bash

# 简单一键启动脚本：启动 Agent 服务 和 Graph 服务

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Python 命令，优先用 python3.11，可按需要修改
PYTHON_CMD="${PYTHON_CMD:-python3.11}"

echo "使用 Python: $PYTHON_CMD"
echo "项目目录: $PROJECT_ROOT"

# 后台启动 Agent 服务
echo "启动 Agent 服务..."
$PYTHON_CMD scripts/start_agent.py > storage/logs/agent_service_simple.log 2>&1 &
AGENT_PID=$!
echo "Agent 服务 PID: $AGENT_PID"

# 后台启动 Graph 服务
echo "启动 Graph 服务..."
$PYTHON_CMD scripts/start_graph_service.py > storage/logs/graph_service_simple.log 2>&1 &
GRAPH_PID=$!
echo "Graph 服务 PID: $GRAPH_PID"

echo
echo "=============================="
echo "  所有服务已启动（简单版）"
echo "=============================="
echo "Agent 服务： http://localhost:8103/"
echo "Graph 服务： http://localhost:8101/"
echo
echo "日志文件："
echo "  storage/logs/agent_service_simple.log"
echo "  storage/logs/graph_service_simple.log"
echo

# 等待服务启动
echo "等待服务就绪..."
sleep 5

# 自动打开浏览器（macOS）
echo "正在打开浏览器..."
open http://localhost:8103/

# 防止脚本立即退出（可选）
wait