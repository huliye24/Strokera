# Strokera 品牌视觉套件

原 `logo/logo.jpg` 保持原样。横版标志、头像和应用图标通过 SVG 容器引用并裁切原始位图；这些 SVG **不是纯路径矢量标志**。如需印刷级矢量版，需要人工描摹与校验。

| 资产 | 尺寸 | 用途 |
| --- | --- | --- |
| `assets/github-header.png` | 1600 × 500 | GitHub README 顶部横图 |
| `assets/lockup-light.png` | 1600 × 440 | 浅底横版品牌图 |
| `assets/lockup-dark.png` | 1600 × 440 | 深底横版品牌图 |
| `assets/social-card.png` | 1200 × 630 | 社交分享封面 |
| `assets/avatar.png` | 1024 × 1024 | 账号头像 |
| `assets/app-icon.png` | 512 × 512 | 应用图标 |

同名 SVG 是可缩放的合成源文件。`showcase.html` 展示了品牌图、色彩和可供未来绘画工作台参考的 UI 元素。基础色：纸白 `#F7F2E9`、深墨 `#202725`、古金 `#8A7046`、灰绿 `#676F69`。留白至少为标志高度的 10%，不可拉伸或重描原标志。横幅与图标分别适配，不建议把宽图直接裁成正方形。

运行 `node brand/build-assets.mjs` 重建 SVG。背景 `assets/paper-strokes.png` 由内置图像生成工具制作，最终提示词：

> Light warm ivory paper across the entire canvas, including top edge and corners; no black or dark filled areas. Subtle graphite contour curves, thin bronze plotted arcs, sparse dry-brush strokes mainly near the lower edge, layered translucent marks suggesting depth and a human painter's touch. Panoramic 3:1 composition, broad clean central space. No logo, no bird or feather, no text, no watermark, no UI.
