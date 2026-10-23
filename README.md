# web-visual-craft · 网页视觉打磨与 3D 展厅交付工艺

一个 [WorkBuddy](https://www.workbuddy.cn) 技能（Skill）。沉淀自一次完整的博物馆网站实战——三星堆青铜器线上展馆「青铜有声」（React 19 + TypeScript + three.js 0.186 + Vite 7）——把网站从「能用」打磨到「好看、能交付」的全套工艺，每条结论都经过无头浏览器截图验证。

## 这个技能解决什么

| 场景 | 典型问题 | 技能给出 |
|---|---|---|
| 网页美化 | 叠版布局、氛围背景、入场动效、文字被 canvas 盖住 | `references/web-polish.md` |
| three.js 展厅 | 金属发黑/像黄漆、圆厅几何、模型归一化、柔和光照 | `references/three-hall.md` |
| 单 HTML 交付 | file:// 被 CORS 拦、模型太大、打包后白屏 | `references/single-file-pipeline.md` + `scripts/optimize_glb.py` |
| 渲染验证 | 「看着暗」「比例不对」全靠猜 | `references/verification.md` 无头截图循环 |

## 安装

把本仓库内容放进 `~/.workbuddy/skills/web-visual-craft/`（用户级）或项目 `.workbuddy/skills/web-visual-craft/`（项目级），重启会话即可。也可以直接使用 Release 里的 zip。

## 里面最有价值的几条

- **`mask-image` 加在 canvas 上会清空整个 WebGL 内容**——用 `::after` 渐变替代。
- **金属材质发黑/像漆**：金属只反射环境光；带 `metalnessMap` 的模型绝不能重置 metalness，只调 `envMapIntensity`。金面具「像一层黄色漆」就是这么修好的。
- **`parseFloat(q) || default` 会吃掉合法的 0**：URL 镜头参数 `cx=0` 全部失效，曾导致误判模型比例错误。
- **入场闸门动画**：首页必须在闸门收场后再挂载，否则 reveal 动画在幕后播完。
- **GLB 简化参数是保真度总闸**：`--simplify-error 0.008` 省 6 倍体积但 60k 面砍到 10k，模型会糊；评审版用 0.001。
- **无头浏览器截图循环**：`--headless=new --enable-unsafe-swiftshader --virtual-time-budget` 一条命令验证任何视觉改动，抓 console、采亮度、查遮挡，不靠目测。

## 结构

```
web-visual-craft/
├── SKILL.md                          # 触发条件 + 工作流（先读）
├── references/
│   ├── web-polish.md                 # CSS/布局/动效/性能工艺清单
│   ├── three-hall.md                 # three.js 展厅：几何/材质/光照/交互
│   ├── single-file-pipeline.md       # GLB 压缩 → 单 HTML 打包两条管线
│   └── verification.md               # 无头浏览器验证配方 + 坑速查
└── scripts/
    └── optimize_glb.py               # GLB 内嵌贴图重编码（PIL）
```

## 背景

这套工艺来自「青铜有声」项目：一个面向学生与普通观众的三星堆青铜器交互展馆，含图文展馆、可转动的 3D 展品查看器、第一人称圆形展厅、单文件离线交付包。技能中的参数（色调、字号、体积预算、简化等级）都是实战回归测试过的默认值。

## License

MIT
