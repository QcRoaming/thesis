# 第五章图形 QA

- 生成时间：2026-08-13T06:30:17.215319+00:00
- 后端：Python/Matplotlib/Seaborn。
- 数据边界：只读取冻结结果文件，不重新编译、不运行 BaCO、不进行硬件测量。
- 每幅图均导出 SVG、PDF、600 dpi TIFF 和 PNG；SVG 文字保持可编辑。
- 颜色以形状、线型或填充纹理辅助区分，关键判断不只依赖颜色。
- 图5-3只显示不活跃参数规范化的配对规模变化，不解释为性能收益。
- 图5-4明确区分规范化前结果与冻结离线 replay。
- 图5-5的区间重采样 trajectory，不代表主机间不确定性。
- 图5-6的 packing 消融改变空间成员，只用于操作性边界解释。
- 图5-7将表示、生成器、合法执行和性能排序分层。
- 图5-8的 i7 曲线是 post-hoc descriptive upper bound，cycle 不是模型推理。

## 自动检查

- 图5-1: four formats present; SVG contains editable text.
- 图5-2: four formats present; SVG contains editable text.
- 图5-3: four formats present; SVG contains editable text.
- 图5-4: four formats present; SVG contains editable text.
- 图5-5: four formats present; SVG contains editable text.
- 图5-6: four formats present; SVG contains editable text.
- 图5-7: four formats present; SVG contains editable text.
- 图5-8: four formats present; SVG contains editable text.
