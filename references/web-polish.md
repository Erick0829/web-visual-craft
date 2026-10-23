# 网页美化工艺清单（CSS / 布局 / 动效 / 性能）

全部来自实战踩坑，每条都被截图验证过。

## 布局

- **叠版效果**：CSS Grid 两列宽度总和 >100%（如 44% + 56% + 4% gap）让图与文自然叠压，比绝对定位稳。
- **inline style 会杀 CSS 负 margin**：元素上写 `style={{margin:0}}` 后，样式表里的负 margin 失效，叠压变 0。排查方法：读 computed margin 实际值。
- **页面根容器**：路由页返回 fragment（没有 `.page` 容器）时，内容会贴到视口边缘（textX=0）。每个页面统一包一层容器。
- **flex 项不会被 max-width 撑宽**：内容定宽的 flex 子项想要响应式变宽，必须写 `width: clamp(min, vw, max)`，只给 max-width 没用。
- **背景图露边**：`background-size: auto 100%` 在超宽屏（1920+）会露出图片右边缘。用 `cover` + `background-position` 微调。

## Canvas / WebGL 与图层的相互作用

- **`mask-image` 加在 canvas 上会清空全部 WebGL 内容**（画面整体消失）。要给 canvas 加渐变遮罩效果，改用兄弟元素 `::after` 叠加渐变。
- **`mix-blend-mode: screen` + z-index 会压住上层文字**：症状是「文字颜色明明是纯白却看着半暗」。排查：`elementFromPoint(x, y)` 看命中的是不是 canvas；用截图采样实测文字最大亮度（如 124/255 ≈ 50%）定位问题。修法：把提示文字移出 canvas 容器。
- **透明 poster 图吞掉指针事件**：canvas 上叠了透明 PNG 时拖拽失效。修法：poster `pointer-events: none` + canvas 提 z-index。

## 动效与入场

- **入场闸门（gate）时序**：如果首页在闸门显示期间就已挂载，reveal 动画会在幕后播完，闸门一收用户看到的是静态页。正确做法：闸门 `onDone` 回调里再 `setPageMounted(true)`，且 reveal 的 effect 依赖里加入挂载状态（如 `${routeKey}:${mounted}` 字符串做 dep）。
- **逐字模糊显影**：`filter: blur()` + `opacity` + 逐字 animation-delay 是低成本高级感方案。
- **可展开指示**：`summary::marker { content: '' }` 清掉浏览器默认箭头后，记得删掉历史遗留的 `::before` 图标，否则两套指示叠画。倒三角用 border 或 clip-path 自绘，亮度拉满（纯色 #c6ad7c，无透明度）。

## 氛围背景（神秘叙事感）

- 深色底 + 多层 radial-gradient（`body::before`，2~3 个暖色微光斑）+ feTurbulence 噪点层（`body::after`，opacity 3~4%），比纯色底有质感且不抢内容。
- 展品区背景要「黑但史诗」：底色 #101411 级别，光源感用渐变伪造，对比度留给展品本身。

## 文案与内容纪律

- 「待核验」之类的状态字样要从**组件级**清除：状态标签、空态文案、小节标题、组件名都可能藏着，逐个组件查；改完用渲染后的 DOM 文本（不是源码 grep）确认，因为有缓存。
- 用户的文案、标题、状态字段一律不动；有异议就报告。

## 性能

- **三维查看器懒加载**：`const Viewer = lazy(() => import('./Viewer').then(m => ({default: m.Viewer})))` + `<Suspense fallback={<静态图/>}>`。效果：three.js 从 entry（884KB）拆到独立 chunk，主包 262KB。
- **按需渲染**：IntersectionObserver（滚出视口暂停）+ visibilitychange（切后台暂停）+ `requestRender()` 手动触发，避免持续 rAF 空转。
- 构建警告 >500KB chunk 时优先查静态 import 的重组件。

## 手动轨道查看器（OrbitControls 失效时的替代）

被 overlay/透明层吃掉事件时，手写球坐标拖拽更稳：维护 `{yaw, pitch, dist}`，`dist` 由 bbox 自适应计算：

```
fitDistance = max( halfH/tan(fov/2), halfW/(tan(fov/2)*aspect) ) * 1.18
```

材质分类处理：有 `metalnessMap` 的保持不动只调 `envMapIntensity`（3.0）；没有的 `envMapIntensity 0.75`。
