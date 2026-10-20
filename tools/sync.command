#!/bin/zsh
cd "${0:A:h:h}" || exit 1
python3 tools/sync_from_surge.py || { read '?❌ 检查失败，按回车退出'; exit 1; }
read 'choice?🔄 1：生成 Loon；🚀 2：生成并发布 GitHub；其他退出：'
case "$choice" in
  1) python3 tools/sync_from_surge.py --apply ;;
  2) python3 tools/sync_from_surge.py --apply --publish ;;
esac
read '?✅ 按回车关闭'
