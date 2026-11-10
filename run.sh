#!/usr/bin/env bash
# 打开题库网页。
#
# 用法：
#   ./run.sh          重新生成题目与答案网页，启动本地服务并在浏览器中打开两个页面
#   ./run.sh qa       只打开晋升考核题库（题目与答案）
#   ./run.sh shuzhi   只打开述职题库
#   PORT=9000 ./run.sh   指定端口（默认 8765）
#
# 按 Ctrl+C 停止本地服务。
set -euo pipefail

cd "$(dirname "$0")"
PORT="${PORT:-8765}"
TARGET="${1:-all}"

python3 shuzhishengji/build_qa_html.py

if lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "端口 $PORT 已被占用，请用 PORT=其他端口 ./run.sh 重试" >&2
  exit 1
fi

python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null; echo; echo "本地服务已停止"' EXIT INT TERM
sleep 1

QA_URL="http://127.0.0.1:$PORT/shuzhishengji/%E9%A2%98%E7%9B%AE%E4%B8%8E%E7%AD%94%E6%A1%88.html"
SHUZHI_URL="http://127.0.0.1:$PORT/shuzhi_web.html"

echo "晋升考核题库：$QA_URL"
echo "述职题库：    $SHUZHI_URL"
echo "按 Ctrl+C 停止"

# 浏览器没有自动打开时，手动复制上面的地址访问
case "$TARGET" in
  qa)     open "$QA_URL" || true ;;
  shuzhi) open "$SHUZHI_URL" || true ;;
  *)      open "$QA_URL" || true; open "$SHUZHI_URL" || true ;;
esac

wait "$SERVER_PID"
