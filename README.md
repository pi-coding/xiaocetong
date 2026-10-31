# 校厕通 · 校园厕所智能管家

参赛作品：面向校园场景的厕所报修、保洁调度与运营管理平台。学生一键报单，后勤智能派单与超时预警，管理员通过数据驾驶舱掌握全局。三角色闭环、离线可演示。

## 功能一览

### 学生端（移动优先）
- 绑定宿舍厕所，自动匹配或创建宿舍厕所档案
- 查询公共厕所：按楼栋、类型、状态、评分筛选，查看清洁状态与最近清洁记录
- 一键提交工单：通厕所 / 清洁 / 报修，支持现场照片、优先级与响应时限
- 工单跟踪：进度时间线、催单（10 分钟限频）、取消、完工后评价
- 积分体系：下单 +5、完工 +10、评价 +5，含排行榜与流水
- AI 助手：查进度、报修引导、附近厕所、积分与清洁规则；下单页「AI 帮我写」自动生成规范描述

### 管理端（桌面）
- 数据驾驶舱：实时指标、7 天工单趋势、类型分布、厕所评分榜、员工绩效榜
- 公共厕所台账：增删改查、二维码（前端本地渲染）、责任保洁与清洁周期
- 超时未打扫预警：三级分级、一键生成清洁工单、超时工单列表
- 工单看板：待派/已派/处理中/已完成四列，手动派单与改派
- AI 派单：空闲度 35% + 历史时效 25% + 服务评分 20% + 区域匹配 20%，可解释得分与理由，支持批量派单
- 统计报表：7/14/30 天趋势、类型与状态分布、楼栋热力、星级分布、排行、导出 CSV
- 员工管理：档案、上下岗、可选自动创建员工登录账号
- 评价管理：差评筛选、回复、申诉标记
- AI 助手：运营问答 + 智能洞察（超时、积压、满意度、楼栋集中、绩效标杆）

### 员工端（移动优先）
- 待办工单：已派单与处理中分组、超时标红
- 工单处理：接单、上传完工照片、提交完工
- 清洁打卡：责任厕所、清洁项、前后照片、耗时与结果，自动刷新清洁时间
- 我的：绩效档案（完成量、平均时效、评分、负责厕所数）

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | Python 3.11+、FastAPI、SQLAlchemy 2.0、Pydantic 2、JWT、bcrypt |
| 数据库 | SQLite（默认，可切 MySQL）、8 张业务表 |
| 前端 | Vue 3、Vite 5、Element Plus、Pinia、Vue Router、ECharts、qrcode |
| 交付形态 | 前后端分离，REST API，统一响应 `{code,msg,data}` |

## 快速开始

### 方式一：Windows 一键启动

双击项目根目录的 `start.bat`。脚本会自动完成：虚拟环境与依赖、建库与演示数据、前端依赖，并分别打开后端与前端窗口。

### 方式二：手动启动

```bash
# 后端
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_db.py --reset
python scripts/seed_demo.py --force
python run.py

# 前端（另开终端）
cd frontend
npm install
npm run dev
```

- 前端：http://localhost:5173
- 后端：http://localhost:8000
- 接口文档：http://localhost:8000/docs

### 演示账号

| 角色 | 账号 | 密码 |
|---|---|---|
| 管理员 | `admin` | `123456` |
| 学生 | `2023101` ~ `2023110` | `123456` |
| 员工 | `staff001` ~ `staff008` | `123456` |

## 5 分钟演示脚本

1. 学生 `2023101` 登录 → 「工单」→ 提交新工单（选择 `D-301`、通厕所、上传照片）→ 详情显示待派单。
2. 管理员 `admin` → 「AI 派单」→ 查看候选得分与理由 → 点「派给 TA」；或「一键 AI 派单」批量处理。
3. 员工 `staff001` → 「待办工单」→ 接单 → 上传完工照片 → 提交完工。
4. 学生回到工单详情 → 评价（星级 + 标签）→ 积分到账 → 「我的积分」查看排行榜与明细。
5. 管理员「数据驾驶舱」「统计报表」查看实时变化；「AI 助手」提问「有哪些超时预警」，查看右侧智能洞察。
6. 可选：「超时未打扫预警」生成清洁单 → 「清洁打卡」由员工补录前后照片。

## 核心业务规则

- **工单状态机**：`待派单 → 已派单 → 处理中 → 已完成`；待派/已派可取消，管理端可关闭；每次流转同步员工负载与绩效。
- **响应时限（SLA）**：紧急 2 小时、高 4 小时、普通 8 小时、低 24 小时；超时工单在看板与预警中标记。
- **超时未打扫**：按「距上次清洁时长 − 清洁周期」计算，超 1 倍为预警、2 倍为严重、3 倍为紧急，无记录直接紧急。
- **AI 派单**：候选先按「在岗 + 工种匹配 + 当日未超上限」过滤，再按四项加权打分，输出因子分与推荐理由。
- **积分**：提交工单 +5、完工 +10、评价 +5、每日签到 +2；所有变动写入流水并记录变动后余额。
- **权限**：学生仅能操作本人绑定与工单；员工仅能处理指派给自己的工单、给自己责任区厕所打卡；管理端接口统一 `role=admin` 校验。

## 接口概览

统一前缀 `/api/v1`，统一返回 `{code,msg,data}`；业务异常返回 HTTP 200 + 业务码（0 成功、1000 参数、1001 未登录、1002 无权限、2001 不存在、2002 状态不允许、2003 重复）。

| 分组 | 代表接口 |
|---|---|
| 认证 | `POST /auth/register`、`POST /auth/login`、`GET /auth/me`、`PUT /auth/password` |
| 厕所 | `GET /toilets`、`GET /toilets/nearby`、`GET /toilets/{id}`、`GET /toilets/{id}/qr`、`POST/PUT/DELETE /toilets` |
| 宿舍绑定 | `GET /dorm-bindings/my`、`GET /dorm-bindings/match`、`POST/PUT/DELETE /dorm-bindings` |
| 工单 | `POST /orders`、`GET /orders/my`、`GET /orders/staff/my`、`POST /orders/{id}/assign`、`accept`、`finish`、`PUT /orders/{id}/cancel`、`urge` |
| AI 派单 | `GET /orders/ai-dispatch/suggest`、`POST /orders/ai-dispatch` |
| 清洁 | `POST /cleaning-logs`、`GET /cleaning-logs/my`、`GET /toilets/{id}/cleaning-logs` |
| 预警 | `GET /alerts/overdue-toilets`、`GET /alerts/overdue-orders`、`GET /alerts/summary`、`POST /alerts/{id}/create-order` |
| 员工 | `GET /staffs`、`GET /staffs/me`、`GET /staffs/my-toilets`、`POST/PUT/DELETE /staffs`、`PUT /staffs/{id}/status` |
| 评价 | `POST /orders/{id}/evaluation`、`GET /evaluations`、`PUT /evaluations/{id}/reply`、`appeal` |
| 积分 | `GET /points/my`、`GET /points/ranking`、`GET /points/rules`、`POST /points/adjust` |
| 统计 | `GET /stats/overview`、`orders-trend`、`type-distribution`、`toilet-ranking`、`staff-ranking`、`building-heat`、`export` |
| AI | `POST /ai/chat`、`POST /ai/describe-problem`、`GET /ai/insight` |
| 其他 | `POST /files/upload`、`GET /health` |

完整定义见 Swagger：`http://localhost:8000/docs`。

## 数据模型

```
user 1─N dorm_binding N─1 toilet
user 1─N service_order N─1 toilet
service_order N─1 staff        service_order 1─1 evaluation
staff 1─N toilet(责任区)        staff 1─N cleaning_log
toilet 1─N cleaning_log         user 1─N points
```

八张表：`user`、`dorm_binding`、`toilet`、`service_order`、`cleaning_log`、`staff`、`evaluation`、`points`。

## 目录结构

```
校厕通/
├─ start.bat / start.sh          # 一键启动
├─ backend/
│  ├─ app/
│  │  ├─ main.py                 # 应用装配、CORS、静态目录
│  │  ├─ core/                   # 配置、统一响应、异常、JWT、依赖
│  │  ├─ db/                     # 引擎与会话
│  │  ├─ models/                 # 8 张表模型
│  │  ├─ schemas/                # 入参/出参
│  │  ├─ api/v1/                 # 13 组路由
│  │  ├─ services/               # 业务逻辑（工单、派单、预警、评价、积分、统计、AI）
│  │  └─ utils/                  # 工单号等
│  ├─ scripts/                   # 建库、演示数据、离线自测
│  ├─ uploads/                   # 图片上传目录
│  └─ requirements.txt
└─ frontend/
   ├─ src/
   │  ├─ api/                    # axios 封装与接口模块
   │  ├─ components/             # ChatPanel、EChart、ImageUpload
   │  ├─ layouts/                # 学生、管理、员工三端布局
   │  ├─ router/                 # 路由与菜单配置
   │  ├─ stores/                 # Pinia 用户状态
   │  ├─ utils/                  # 字典、格式化、二维码
   │  └─ views/                  # 学生、管理、员工页面
   └─ vite.config.js             # /api 与 /uploads 代理
```

## 自测与验证

```bash
# 后端业务自测（离线，不依赖网络与事件循环）
cd backend
.venv\Scripts\python.exe scripts\smoke_test.py

# 前端组件编译校验
cd frontend
node scripts/check-sfc.mjs
```

当前基线：后端 **128/128 通过**，前端 **34/34 组件通过**。

## 常见问题

**端口被占用**：后端改 `python run.py` 中的端口或使用 `uvicorn app.main:app --port 8001`；前端 `npm run dev -- --port 5174`。

**重置演示数据**：

```bash
cd backend
.venv\Scripts\python.exe scripts/init_db.py --reset
.venv\Scripts\python.exe scripts/seed_demo.py --force
```

**切换 MySQL**：安装 `pymysql`，在 `backend/.env` 设置 `DATABASE_URL=mysql+pymysql://user:pass@host:3306/cct?charset=utf8mb4`，再执行建库与种子脚本。SQLite 现有数据不会自动迁移。

**启用大模型**：在 `backend/.env` 配置 `AI_API_KEY`、`AI_BASE_URL`、`AI_MODEL`，重启后端即可；调用失败或超时会自动回退到内置规则引擎，不影响演示。

**二维码**：后端只返回标识内容，前端用 qrcode 库本地渲染，可下载 PNG，离线可用。

**生产部署**：前端 `npm run build` 后由 Nginx 托管 `dist`，并将 `/api`、`/uploads` 反向代理到后端；后端使用 `uvicorn app.main:app --host 0.0.0.0 --port 8000`。

## 开发约定

- 接口统一返回 `{code,msg,data}`，业务异常经全局处理器包装。
- 数据库操作全部走 SQLAlchemy 参数化，禁止字符串拼接 SQL。
- 权限通过依赖注入统一校验，避免在业务代码中散落判断。
- 每个模块交付附带启动命令与页面验证步骤。