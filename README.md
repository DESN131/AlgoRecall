# AlgoRecall

一个面向 LeetCode 练习的本地错题管理与间隔复习应用。支持红/黄/绿评级、自动复习计划、逐题复习、完整历史、搜索筛选和学习统计。

## 环境

- Python 3.12+
- SQLite（数据默认保存在 `data/algorecall.db`）

## 安装与启动

Windows 可以直接双击 `start.bat`，或在 PowerShell 中运行：

```powershell
.\start.ps1
```

脚本会检查 Python 版本、按需安装依赖并启动开发服务器。可选参数：

```powershell
.\start.ps1 -BindHost 0.0.0.0 -Port 8080 -NoReload
```

也可以手动启动：

```powershell
python -m pip install -e ".[test]"
uvicorn app.main:app --reload
```

访问 <http://127.0.0.1:8000>。首次启动会自动运行 Alembic 迁移并创建数据库。API 文档位于 <http://127.0.0.1:8000/docs>。

如需修改配置，复制 `.env.example` 为 `.env` 后编辑。

## 测试

```powershell
python -m pytest
```

## 复习规则

- Red：1 天后复习。
- 首次 Yellow：3 天后；连续 Yellow：7 天后。
- 首次 Green：7 天后；再次 Green：14 天后；连续通过后进入 Mastered。
- 所有间隔以应用时区的自然日计算，逾期任务不会丢失。

## 常用入口

- `/`：Dashboard
- `/problems`：题库、搜索与筛选
- `/review`：今日复习队列
- `/history`：全局复习历史
- `/statistics`：学习统计
- `/api/v1`：REST API 前缀
