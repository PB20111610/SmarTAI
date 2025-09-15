# SmarTAI智能评估平台 🎓

基于人工智能的理工科教育评估系统，提供智能评分、深度分析和可视化报告。

## ✨ 项目特性

### 🎯 核心功能
- **智能评分报告** - 学生作业详细评分结果，支持人工修改和批量操作
- **可视化分析仪表盘** - 深度分析学生表现和题目质量，生成交互式图表
- **置信度分析** - 提供置信度指标和复核建议
- **多维度统计** - 成绩分布、知识点掌握度、错误分析等

### 🚀 技术栈
- **前端框架**: Streamlit
- **数据可视化**: Plotly, Altair
- **组件库**: Streamlit-aggrid, st-pages
- **样式**: 自定义CSS + Streamlit主题
- **数据处理**: Pandas, NumPy
- **模拟数据**: Faker

## 📁 项目结构

```
streamlit_demo/
├── main.py                 # 主应用入口
├── pages/                  # 页面目录
│   ├── score_report.py     # 评分报告界面
│   └── visualization.py    # 可视化分析界面
├── utils/                  # 工具模块
│   ├── __init__.py
│   ├── data_loader.py      # 数据模型和加载器
│   └── chart_components.py # 图表组件
├── assets/                 # 资源文件
│   └── styles.css          # 自定义样式
├── requirements.txt        # 依赖包列表
└── README.md              # 项目说明
```

## 🛠️ 安装与运行

### 环境要求
- Python 3.8+
- pip 包管理器

### 安装步骤

1. **克隆或下载项目**
   ```bash
   # 如果有git仓库
   git clone <repository_url>
   cd streamlit_demo
   ```

2. **创建虚拟环境（推荐）**
   ```bash
   # 使用conda
   conda create -n smartai python=3.12
   conda activate smartai
   
   # 或使用venv
   python -m venv smartai_env
   # Windows
   smartai_env\Scripts\activate
   # macOS/Linux
   source smartai_env/bin/activate
   ```

3. **安装依赖包**
   ```bash
   pip install -r requirements.txt
   ```

4. **运行应用**
   ```bash
   streamlit run main.py
   ```

5. **访问应用**
   - 本地访问: http://localhost:8501
   - 网络访问: http://[你的IP]:8501

## 📋 功能详解

### 🏠 主界面 (main.py)
- **系统概览**: 显示关键统计数据
- **快速预览**: 成绩分布和等级分布图表
- **快速操作**: 一键跳转到各功能模块
- **最近活动**: 显示系统操作历史

### 📊 评分报告界面 (pages/score_report.py)

#### 功能特性
1. **学生作业列表展示**
   - 支持按学号/姓名搜索
   - 显示学生基本信息（学号、姓名、提交时间）
   - 显示每题得分和总分
   - 标记需要复核的题目

2. **详细评分查看**
   - 点击学生行展开详细评分
   - 显示每题得分、评语、扣分点
   - 支持人工修改分数和评语
   - 显示置信度指标（低置信度红色高亮）

3. **批量操作**
   - 批量下载评分报告（PDF/Excel）
   - 批量标记复核状态
   - 全选/反选功能

4. **筛选和排序**
   - 按成绩等级筛选
   - 按复核状态筛选
   - 按置信度筛选
   - 多种排序方式

### 📈 可视化分析界面 (pages/visualization.py)

#### 功能模块
1. **成绩统计概览**
   - 班级平均分、最高分、最低分
   - 成绩分布直方图
   - 及格率统计
   - 分数段分布饼图

2. **题目分析**
   - 每题正确率柱状图
   - 题目难度系数计算
   - 知识点掌握度热力图
   - 易错题排行榜（Top10）

3. **学生表现**
   - 成绩排名表（可排序）
   - 进步/退步趋势（对比历史）
   - 个人雷达图（多维度能力）
   - 需要关注的学生列表（低分预警）

4. **交互功能**
   - 筛选器：按班级、时间段、题型
   - 图表联动：点击图表元素更新其他图表
   - 数据导出：PDF格式（包含当前筛选条件）
   - 一键生成分析报告

## 🎨 界面设计特色

### 设计规范
- **配色方案**: 深蓝色(#1E3A8A) + 橙色(#F59E0B) + 海蓝绿(#2E8B57)
- **字体**: Google Fonts Noto Sans SC
- **卡片设计**: 圆角、阴影效果、悬停动画
- **响应式布局**: 支持3列→2列→1列自适应

### 交互体验
- **加载动画**: 使用Streamlit原生spinner
- **状态反馈**: Toast通知、成功/错误提示
- **键盘导航**: 支持Tab键导航
- **工具提示**: 重要按钮添加tooltips

## 📊 数据模型

### 核心数据类

1. **StudentScore** - 学生成绩数据
   ```python
   - student_id: 学号
   - student_name: 姓名
   - total_score: 总分
   - questions: 题目列表
   - need_review: 是否需要复核
   - confidence_score: 置信度
   ```

2. **QuestionAnalysis** - 题目分析数据
   ```python
   - question_id: 题目ID
   - question_type: 题目类型
   - difficulty: 难度系数
   - correct_rate: 正确率
   - common_errors: 常见错误
   ```

3. **AssignmentStats** - 作业统计数据
   ```python
   - assignment_name: 作业名称
   - total_students: 学生总数
   - avg_score: 平均分
   - pass_rate: 及格率
   ```

## 🔧 自定义配置

### 修改样式
编辑 `assets/styles.css` 文件来自定义界面样式：
- 修改颜色主题
- 调整卡片样式
- 更改字体设置

### 修改数据
编辑 `utils/data_loader.py` 文件：
- 调整模拟数据生成逻辑
- 连接真实数据源
- 修改数据结构

### 添加图表
编辑 `utils/chart_components.py` 文件：
- 添加新的图表类型
- 修改图表样式
- 扩展交互功能

## 🚀 部署指南

### 本地部署
直接运行 `streamlit run main.py`

### 云端部署

1. **Streamlit Cloud**
   - 上传代码到GitHub
   - 连接Streamlit Cloud账户
   - 选择仓库部署

2. **Docker部署**
   ```dockerfile
   FROM python:3.12-slim
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   EXPOSE 8501
   CMD ["streamlit", "run", "main.py"]
   ```

3. **服务器部署**
   ```bash
   # 使用PM2管理进程
   npm install -g pm2
   pm2 start "streamlit run main.py" --name smartai
   ```

## 🛡️ 性能优化

### 缓存策略
- 使用 `@st.cache_data` 缓存数据加载
- 使用 `@st.cache_resource` 缓存图表组件
- 分页加载大数据集

### 加载优化
- 懒加载图表组件
- 使用 `st.skeleton` 占位符
- 图片和资源压缩

## 🔍 故障排除

### 常见问题

1. **导入错误**
   ```bash
   # 检查Python路径
   import sys
   print(sys.path)
   ```

2. **依赖包冲突**
   ```bash
   # 重新安装依赖
   pip uninstall streamlit
   pip install streamlit
   ```

3. **端口占用**
   ```bash
   # 指定其他端口
   streamlit run main.py --server.port 8502
   ```

4. **内存不足**
   - 减少同时显示的数据量
   - 使用数据分页
   - 优化图表渲染

### 调试模式
```bash
# 启用调试模式
streamlit run main.py --logger.level debug
```

## 📄 许可证

本项目仅供学习和演示使用。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

### 开发流程
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 发起Pull Request

## 📞 技术支持

- **文档**: 查看代码注释和README
- **Issues**: 在GitHub提交问题
- **讨论**: 参与项目讨论区

## 🎯 未来规划

- [ ] 添加用户认证系统
- [ ] 集成真实AI评分模型
- [ ] 支持多种文件格式
- [ ] 添加移动端适配
- [ ] 实现实时协作功能
- [ ] 增加多语言支持

---

**开发时间**: 2024年9月
**版本**: v1.0.0
**技术栈**: Streamlit + Plotly + Python
