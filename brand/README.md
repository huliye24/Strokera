# Strokera 品牌视觉套件

品牌主标志现为用户提供的黑色笔触版本，原始白底文件保存在 `logo/logo-black-source.png`，透明母版保存在 `logo/logo-black-transparent.png`。旧的金色 `logo/logo.jpg` 保留作历史源文件，不再用于当前品牌合成。横版标志、头像和应用图标通过 SVG 容器引用透明位图；这些 SVG **不是纯路径矢量标志**。如需印刷级矢量版，需要人工描摹与校验。

| 资产 | 尺寸 | 用途 |
| --- | --- | --- |
| `assets/github-header.png` | 1600 × 500 | GitHub README 顶部横图 |
| `assets/lockup-light.png` | 1600 × 440 | 浅底横版品牌图 |
| `assets/lockup-dark.png` | 1600 × 440 | 深底横版品牌图 |
| `assets/social-card.png` | 1200 × 630 | 社交分享封面 |
| `assets/avatar.png` | 1024 × 1024 | 账号头像 |
| `assets/app-icon.png` | 512 × 512 | 应用图标 |
| `../logo/logo-black-transparent.png` | 1254 × 1254 | 透明底黑色主标志，可直接叠放在浅色背景 |

同名 SVG 是可缩放的合成源文件。深底横版将同一透明标志反色呈白色。`showcase.html` 展示了品牌图、色彩和可供未来绘画工作台参考的 UI 元素。基础色：纸白 `#F7F2E9`、深墨 `#202725`、古金 `#8A7046`、灰绿 `#676F69`。留白至少为标志高度的 10%，不可拉伸或重描原标志。横幅与图标分别适配，不建议把宽图直接裁成正方形。

运行 `node brand/build-assets.mjs` 重建 SVG。背景 `assets/paper-strokes.png` 由内置图像生成工具制作，最终提示词：

透明母版使用内置图像编辑工具从用户提供的黑色白底标志去背。提示词要点：只移除白底，生成真实 alpha；保留原几何、线重、眼部细节与内部镂空；不重绘、不改色、不裁切。

> Light warm ivory paper across the entire canvas, including top edge and corners; no black or dark filled areas. Subtle graphite contour curves, thin bronze plotted arcs, sparse dry-brush strokes mainly near the lower edge, layered translucent marks suggesting depth and a human painter's touch. Panoramic 3:1 composition, broad clean central space. No logo, no bird or feather, no text, no watermark, no UI.
