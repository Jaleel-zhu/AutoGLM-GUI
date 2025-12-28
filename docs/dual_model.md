# 双模型协作功能 (Dual Model Collaboration)

## 概述

AutoGLM-GUI 支持大模型+小模型的协作模式，实现更智能的手机自动化操作：

- **大模型 (GLM-4.7)**: 负责任务分析、决策制定、内容生成（如帖子、回复等）
- **小模型 (autoglm-phone)**: 负责屏幕识别、动作执行

这种架构充分利用了两种模型的优势：
- 大模型拥有更强的推理能力，可以进行复杂的任务规划和内容创作
- 小模型拥有视觉能力，可以直接理解屏幕内容并执行精确操作

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    用户输入任务                          │
│           "帮我在小红书发一条关于天气的帖子"              │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 大模型 (GLM-4.7)                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │ 1. 分析任务，制定执行计划                          │  │
│  │ 2. 根据屏幕描述做出决策                           │  │
│  │ 3. 生成需要输入的内容                             │  │
│  └───────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│               小模型 (autoglm-phone)                     │
│  ┌───────────────────────────────────────────────────┐  │
│  │ 1. 截取屏幕，识别内容                             │  │
│  │ 2. 将屏幕描述发送给大模型                         │  │
│  │ 3. 执行大模型的决策                               │  │
│  └───────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                   Android 设备                          │
└─────────────────────────────────────────────────────────┘
```

## 协作流程

### Step 1: 任务初始化
```
用户: "帮我在小红书发一条帖子，内容关于今天的天气"

大模型分析任务：
→ 任务类型：社交媒体发帖
→ 执行计划：
   1. 打开小红书APP
   2. 点击发布按钮
   3. 输入内容
   4. 发布
```

### Step 2: 识图+决策循环
```
循环开始:

小模型截图并识别:
→ 当前屏幕: "手机桌面，可见图标：微信、支付宝、小红书..."

大模型决策:
→ 判断当前位置：手机桌面
→ 目标：打开小红书
→ 决策: "点击小红书图标"

小模型执行:
→ 定位小红书图标位置
→ 执行点击操作
```

### Step 3: 内容生成
```
当需要输入内容时:

大模型生成内容:
→ 标题: "今日天气☀️"
→ 正文: "今天阳光明媚，心情也特别好..."

小模型执行:
→ 点击标题栏
→ 输入标题
→ 点击正文栏
→ 输入正文
```

## API 端点

### 初始化双模型

```http
POST /api/dual/init
```

请求体:
```json
{
  "device_id": "设备ID",
  "decision_base_url": "https://api-inference.modelscope.cn/v1",
  "decision_api_key": "your-api-key",
  "decision_model_name": "ZhipuAI/GLM-4.7",
  "vision_base_url": "可选，默认使用全局配置",
  "vision_api_key": "可选",
  "vision_model_name": "可选",
  "max_steps": 50
}
```

### 流式聊天

```http
POST /api/dual/chat/stream
Content-Type: application/json

{
  "device_id": "设备ID",
  "message": "帮我在小红书发一条帖子"
}
```

响应 (Server-Sent Events):
```
event: decision_start
data: {"type":"decision_start","model":"decision","stage":"analyzing"}

event: decision_thinking
data: {"type":"decision_thinking","chunk":"正在分析任务..."}

event: task_plan
data: {"type":"task_plan","plan":{"summary":"发帖任务","steps":[...]}}

event: vision_start
data: {"type":"vision_start","model":"vision","stage":"recognizing"}

event: vision_recognition
data: {"type":"vision_recognition","description":"手机桌面..."}

event: decision_result
data: {"type":"decision_result","decision":{"action":"tap","target":"小红书图标"}}

event: action_result
data: {"type":"action_result","success":true,"action_type":"tap"}

event: step_complete
data: {"type":"step_complete","step":1,"success":true}

event: task_complete
data: {"type":"task_complete","success":true,"message":"任务完成","steps":5}
```

### 中止任务

```http
POST /api/dual/chat/abort
Content-Type: application/json

{
  "device_id": "设备ID"
}
```

### 获取状态

```http
GET /api/dual/status?device_id=设备ID
```

### 重置

```http
POST /api/dual/reset
Content-Type: application/json

{
  "device_id": "设备ID"
}
```

## 配置

在 `~/.config/autoglm/config.json` 中添加双模型配置：

```json
{
  "base_url": "http://localhost:8080/v1",
  "model_name": "autoglm-phone-9b",
  "api_key": "your-vision-api-key",
  "dual_model_enabled": true,
  "decision_base_url": "https://api-inference.modelscope.cn/v1",
  "decision_model_name": "ZhipuAI/GLM-4.7",
  "decision_api_key": "your-decision-api-key"
}
```

## 前端集成

### 使用 DualModelPanel 组件

```tsx
import { DualModelPanel, useDualModelState } from '@/components/DualModelPanel';
import { sendDualModelStream } from '@/api';

function MyComponent() {
  const { state, handleEvent, reset } = useDualModelState();
  const [isStreaming, setIsStreaming] = React.useState(false);

  const handleSend = (message: string) => {
    reset();
    setIsStreaming(true);

    const stream = sendDualModelStream(
      message,
      deviceId,
      (event) => {
        handleEvent(event);
        if (event.type === 'task_complete' || event.type === 'error') {
          setIsStreaming(false);
        }
      },
      (error) => {
        console.error(error);
        setIsStreaming(false);
      }
    );
  };

  return (
    <div>
      <DualModelPanel state={state} isStreaming={isStreaming} />
      {/* 其他UI */}
    </div>
  );
}
```

## 文件结构

```
AutoGLM_GUI/
├── dual_model/                     # 双模型协作模块
│   ├── __init__.py                 # 模块导出
│   ├── decision_model.py           # 决策大模型 (GLM-4.7)
│   ├── vision_model.py             # 视觉小模型适配器
│   ├── dual_agent.py               # 双模型协调器
│   └── protocols.py                # 通信协议定义
│
├── api/
│   └── dual_model.py               # 双模型API端点
│
frontend/src/
├── components/
│   └── DualModelPanel.tsx          # 双模型状态显示组件
│
└── api.ts                          # 双模型API调用
```

## 注意事项

1. **模型选择**: 大模型需要较强的推理能力，推荐使用 GLM-4.7 或同等级模型
2. **API Key**: 需要分别配置大模型和小模型的 API Key
3. **延迟**: 双模型模式会增加一些延迟，因为需要两个模型协作
4. **Token 消耗**: 大模型处理任务规划和决策会消耗较多 token
5. **兼容性**: 小模型需要支持视觉输入（图片理解能力）
