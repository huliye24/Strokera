# SPP 0.1 — Strokera Painting Protocol（草案）

SPP 是绘画**过程**的交换格式，不是最终图像格式。本文定义当前 CLI 已实现的最小交集；更丰富的笔刷物理和编辑事件留待后续版本。

## 文档结构

顶层 JSON 必须有 `protocol: "spp/0.1"`、`canvas`、`layers`、`strokes`。可选 `title`。画布含 `width`、`height`（1–10000）和可选 `background`（`#RRGGBB`）。`layers` 为从后到前的非空数组，每层有唯一 `id`，可加 `name`。`strokes` 是有序数组，每笔有唯一 `id`、有效 `layer_id`、`width`（0.01–1000）、`color`（`#RRGGBB`）、可选 `opacity`（0–1），并在以下几何形式中选择一种：

- `path`: 至少 2、最多 10000 个 `[x,y]` 点。单位为画布坐标。
- `parametric`: `x`、`y` 数学表达式，`from`、`to` 范围，`steps` 采样数（2–2000）。变量仅 `t`；常量 `pi`、`tau`、`e`；函数 `sin`、`cos`、`tan`、`sqrt`、`log`、`exp`；运算符 `+ - * / **`。不允许属性访问、导入或执行代码。

层顺序决定遮挡；层内笔触按 `strokes` 中的出现顺序绘制。0.1 只支持圆头、圆角的均匀宽度路径。`render` 为确定性 SVG；`preview` 为回放观察界面。参数表达式是创作输入，不会在产物中执行。

## Agent CLI 契约

```bash
strokera validate painting.json
strokera render painting.json -o painting.svg
strokera preview painting.json -o painting.html
```

成功：退出码 0，stdout 单行 JSON `{"ok":true,...}`。验证或 IO 失败：退出码 2，stderr 单行 JSON `{"ok":false,"error":"..."}`。CLI 不隐式联网、不调用生成模型、不修改输入文件。

## 下一版候选

笔压/宽度曲线、刷毛纹理、颜色混合、局部版本事件、分组与对象语义、坐标变换、Agent 提案与作者确认记录。扩展字段须明确版本，不得让 0.1 客户端静默误读。
