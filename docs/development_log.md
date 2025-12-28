# 开发日志

## [2025-12-28] 双模型协作功能 - Bug修复

### 修复内容

修复了 `'Screenshot' object has no attribute 'data'` 错误：
- 问题表现：双模型模式下循环在 vision_start 事件，无法进入决策阶段
- 根因：vision_model.py 使用了错误的 Screenshot 属性名
- 修复：将 `screenshot.data`/`screenshot.base64` 改为 `screenshot.base64_data`

### 文件变更

**修改文件:**
- `AutoGLM_GUI/dual_model/vision_model.py`: 修正 capture_screenshot() 返回值
- `AutoGLM_GUI/dual_model/dual_agent.py`: 适配新的返回值签名

### 测试状态

- [x] 服务器启动正常
- [ ] 双模型功能测试

---

## [2025-12-28] 双模型协作功能 - 前端集成

### 实现内容

完成了双模型功能的前端集成：
- 在 DevicePanel 组件中添加了双模型切换按钮（紫色 Brain 图标）
- 集成了 DualModelPanel 组件用于显示双模型状态
- 实现了双模型流式消息发送功能
- 更新了 Reset 和 Abort 功能以支持双模型模式

### 技术要点

1. **前端组件更新**
   - 导入 `DualModelPanel` 和 `useDualModelState`
   - 导入双模型 API 函数：`initDualModel`, `sendDualModelStream`, `abortDualModelChat`, `resetDualModel`
   - 添加双模型状态变量：`dualModelEnabled`, `dualModelInitialized`
   - 添加双模型流引用：`dualModelStreamRef`

2. **新增功能函数**
   - `handleInitDualModel()`: 初始化双模型 Agent
   - `handleToggleDualModel()`: 切换双模型模式
   - `handleSendDualModel()`: 使用双模型发送消息
   - `handleSendMessage()`: 统一发送函数，根据模式选择单/双模型

3. **UI 更新**
   - 头部添加紫色双模型切换按钮
   - 启用双模型时显示 DualModelPanel 状态面板
   - DualModelPanel 显示：任务计划、大模型状态、小模型状态、进度

### 文件变更

**修改文件:**
- `frontend/src/components/DevicePanel.tsx`: 集成双模型功能

## [2025-12-28] 双模型协作功能

### 实现内容

实现了大模型+小模型的协作机制：
- 大模型(GLM-4.7)：负责任务分析、决策制定、内容生成
- 小模型(autoglm-phone)：负责屏幕识别、动作执行

### 技术要点

1. **后端架构**
   - `DecisionModel`: 决策大模型客户端，支持流式输出和 reasoning_content 解析
   - `VisionModel`: 视觉小模型适配器，复用现有的 ModelClient 和 ActionHandler
   - `DualModelAgent`: 双模型协调器，管理协作流程和状态

2. **API设计**
   - `POST /api/dual/init`: 初始化双模型Agent
   - `POST /api/dual/chat/stream`: 流式聊天(SSE)
   - `POST /api/dual/chat/abort`: 中止任务
   - `GET /api/dual/status`: 获取状态
   - `POST /api/dual/reset`: 重置Agent

3. **前端组件**
   - `DualModelPanel`: 双模型状态显示组件
   - `useDualModelState`: 状态管理Hook
   - 扩展了 api.ts 支持双模型API调用

4. **SSE事件类型**
   - `decision_start/thinking/result`: 大模型相关事件
   - `vision_start/recognition`: 小模型识图事件
   - `action_start/result`: 动作执行事件
   - `task_plan`: 任务计划事件
   - `step_complete/task_complete`: 进度事件

### 文件变更

**新增文件:**
- `AutoGLM_GUI/dual_model/__init__.py`
- `AutoGLM_GUI/dual_model/protocols.py`
- `AutoGLM_GUI/dual_model/decision_model.py`
- `AutoGLM_GUI/dual_model/vision_model.py`
- `AutoGLM_GUI/dual_model/dual_agent.py`
- `AutoGLM_GUI/api/dual_model.py`
- `frontend/src/components/DualModelPanel.tsx`
- `docs/dual_model.md`
- `docs/development_log.md`

**修改文件:**
- `AutoGLM_GUI/api/__init__.py`: 注册双模型路由
- `AutoGLM_GUI/config_manager.py`: 添加双模型配置字段
- `frontend/src/api.ts`: 添加双模型API类型和函数

### 测试状态

- [ ] 后端API测试
- [ ] 前端组件测试
- [ ] 集成测试

### 备注

- 大模型使用 ModelScope 的 GLM-4.7，支持 reasoning_content 字段
- 小模型复用现有的 autoglm-phone 模型
- 双模型模式需要分别配置两个模型的 API Key
