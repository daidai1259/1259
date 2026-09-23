# 1259 AI施工图审核平台

AI 辅助施工图审核平台，目标是把图纸上传、解析、识别、规则检查、问题定位和报告生成串成完整工作流。

## 当前能力

- 项目管理
- PDF / JPG / PNG 图纸上传与安全校验
- PDF 页面渲染、缩略图生成
- PDF 文字层提取与坐标保存
- 图号、图名、专业、比例的基础元数据识别
- OCR Provider 接口层（默认 noop，可配置 Tesseract；扫描 PDF 无文字层时可进入 OCR）
- 审核问题采用明确的 normalized 0..1 坐标系，前端可稳定定位红框
- 审核任务状态与失败重试基础设施
- 结构化审核问题模型
- 第一批确定性元数据检查规则
- Next.js 审图工作台界面
- GitHub Actions 前后端构建/测试

## 技术路线

- Frontend: Next.js + React + TypeScript
- Backend: FastAPI + SQLAlchemy
- Database: SQLite（开发）/ PostgreSQL（生产规划）
- Migration: Alembic
- Drawing rendering: PyMuPDF
- Image processing: Pillow
- OCR: Provider abstraction，可接入本地 OCR 或云 OCR
- AI review: 预留视觉模型与规则引擎组合架构

## 本地启动

后端：进入 backend，创建虚拟环境，安装 requirements.txt，复制 .env.example 为 .env，然后执行 alembic upgrade head，再运行 uvicorn app.main:app --reload --port 8000。

前端：进入 frontend，执行 npm install，然后 npm run dev。浏览器打开 http://localhost:3000。

## 数据库

应用启动不会自动创建生产数据库表，必须使用 alembic upgrade head 创建或升级数据库。

## 产品边界

本系统是 AI 辅助审图工具。AI、OCR 和规则检查结果均需要专业人员复核；系统不替代注册工程师、施工图审查机构或法定审批程序。

## OCR 配置

默认 `OCR_PROVIDER=noop`，不会要求本机安装 OCR 引擎。需要本地 Tesseract 时安装 Tesseract 与 Python 依赖，并设置 `OCR_PROVIDER=tesseract`；中文图纸可进一步设置 `OCR_LANG=chi_sim+eng`。系统在 PDF 无文字层时对渲染页执行 OCR，并把识别结果写入页面文字数据。
