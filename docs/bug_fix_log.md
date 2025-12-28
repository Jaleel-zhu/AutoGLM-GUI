# 问题修复日志

## [2025-12-28] Screenshot属性访问错误修复

### 问题描述
双模型功能测试时，系统一直循环在 vision_start 事件，无法进入 decision_start 阶段，最终报错"达到最大步数限制(50)"。

### 定位分析
通过日志分析，发现错误信息：
```
步骤执行失败: 'Screenshot' object has no attribute 'data'
```

根因分析：
- `vision_model.py` 中的 `capture_screenshot()` 方法使用了错误的属性名
- 代码使用了 `screenshot.data` 和 `screenshot.base64`
- 实际 `Screenshot` 类的属性名是 `screenshot.base64_data`

### 修复方案

1. **vision_model.py** - 修正 `capture_screenshot()` 方法：
   ```python
   # 修复前
   return (
       screenshot.data,  # 错误
       screenshot.base64,  # 错误
       screenshot.width,
       screenshot.height,
   )

   # 修复后
   return (
       screenshot.base64_data,  # 正确
       screenshot.width,
       screenshot.height,
   )
   ```

2. **dual_agent.py** - 更新调用处适配新的返回值签名：
   ```python
   # 修复前
   _, screenshot_base64, width, height = self.vision_model.capture_screenshot()

   # 修复后
   screenshot_base64, width, height = self.vision_model.capture_screenshot()
   ```

### 涉及文件
- `AutoGLM_GUI/dual_model/vision_model.py`
- `AutoGLM_GUI/dual_model/dual_agent.py`

### 验证结果
- 服务器已重启，运行在 http://127.0.0.1:8000
- 等待用户测试验证

### 预防措施
- 使用第三方库的数据类时，应先检查实际属性名
- 添加类型注解可以帮助 IDE 提前发现此类错误
