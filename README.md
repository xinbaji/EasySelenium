# EasySelenium

EasySelenium 是一个基于 Selenium 的 Python 封装库，提供了简洁的 API 来简化 Web 自动化测试的常见操作。以下是库中所有函数的详细说明和使用方法。

## 类与函数说明

### 1. `Log` 类

**功能**：用于记录日志信息，支持调试模式和信息模式。

**参数**：
- `log_name` (str): 日志名称。
- `mode` (str, 可选): 日志模式，`"d"` 为调试模式，`"i"` 为信息模式（默认）。

**方法**：
- `__init__`: 初始化日志记录器。

---

### 2. `only_chained_calls` 装饰器

**功能**：确保链式调用的方法只能在元素存在时执行。

**参数**：
- `func`: 被装饰的函数。

---

### 3. `Driver` 类

**功能**：封装了 Selenium WebDriver 的核心功能，支持 Chrome 和 Edge 浏览器。

**参数**：
- 无显式参数，但初始化时会检查可用的浏览器驱动。

**方法**：

#### `__init__`

**功能**：初始化 WebDriver，配置浏览器选项。

**参数**：
- 无显式参数。

---

#### `_driver_isavailable`

**功能**：检查指定的浏览器驱动是否可用。

。

**返回值**：
- `str`: 返回一个可用驱动字符串。

---

#### `get`

**功能**：打开指定的 URL。

**参数**：
- `url` (str): 目标 URL。

---

#### `wait`

**功能**：等待页面元素满足指定条件。

**参数**：
- `case` (str): 等待条件，可选值：
  - `"visible"`: 元素可见。
  - `"clickable"`: 元素可点击。
  - `"iframe_available"`: iframe 可用并切换。
  - `"string_visible"`: 元素中包含指定文本。
- `path` (str): 元素的 CSS 选择器或 XPath 路径。
- `target_string` (str, 可选): 当 `case` 为 `"string_visible"` 时，指定目标文本。
- `timeout` (int, 可选): 超时时间（秒），默认为 `-1`（使用类中定义的默认超时时间）。

**返回值**：
- `self`: 支持链式调用。

---

#### `remove`

**功能**：移除当前临时元素。

**参数**：
- 无显式参数。

---

#### `click`

**功能**：点击当前临时元素。

**参数**：
- 无显式参数。

---

#### `send_keys`

**功能**：向当前临时元素发送键盘输入。

**参数**：
- `keys` (str): 输入的文本。

---

#### `get_attribute`

**功能**：获取当前临时元素的指定属性值。

**参数**：
- `attr` (str): 属性名称。

**返回值**：
- `str`: 属性值。

---

#### `get_text`

**功能**：获取当前临时元素的文本内容。

**参数**：
- 无显式参数。

**返回值**：
- `str`: 元素的文本内容。

---

#### `force_click`

**功能**：强制点击当前临时元素（通过 JavaScript）。

**参数**：
- 无显式参数。

---

#### `switch_to_last_window`

**功能**：切换到最后一个打开的窗口。

**参数**：
- 无显式参数。

---

#### `close`

**功能**：关闭当前窗口。

**参数**：
- 无显式参数。

---

#### `refresh`

**功能**：刷新当前页面。

**参数**：
- 无显式参数。

---

#### `get_page_source`

**功能**：获取当前页面的 HTML 源码。

**参数**：
- 无显式参数。

**返回值**：
- `str`: 页面源码。

---

#### `switch_to_default_frame`

**功能**：切换回默认的 iframe。

**参数**：
- 无显式参数。

---

## 异常类

### 1. `NoSuchDriverException`

**功能**：当没有可用的浏览器驱动时抛出。

---

### 2. `PathInvalid`

**功能**：当路径格式非法时抛出。

---

### 3. `NoSuchCaseException`

**功能**：当指定的 `case` 不存在时抛出。

---

### 4. `NoSuchElement`

**功能**：当元素不存在时抛出。

---

## 使用示例

```python
from EasySelenium import Driver

driver = Driver()
driver.get("https://example.com")
driver.wait("visible", "#some-element").click()
driver.wait("visible", "#some-element").send_keys("Hello, World!")
driver.close()
```

## 注意事项

1. 确保已安装 Chrome 或 Edge 浏览器驱动。
2. 使用 `wait` 方法时，确保 `case` 和 `path` 参数正确。
3. 链式调用方法（如 `click`、`send_keys`）必须在 `wait` 方法之后调用。

---

**作者**: [Your Name]
**版本**: 1.0.0
**最后更新**: 2025-08-31
