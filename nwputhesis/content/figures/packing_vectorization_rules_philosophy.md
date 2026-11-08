# Packing and Vectorization Rules Visual Philosophy

This visual language treats a matrix multiply kernel as a disciplined act of rearrangement. The surface should feel quiet, engineered, and inevitable: broad regions of white space, a few deliberate strokes, and a restrained palette that lets structure carry the narrative. The composition is not decorative in the ordinary sense; it is meticulously crafted to reveal how an irregular memory object becomes a contract-compatible stream of panels and lanes.

The work should suggest precision without clutter. Rectangles, stripes, lane marks, and small alignment ticks become the vocabulary of the piece. Every mark must look like the product of deep expertise and painstaking attention: panel boundaries align on a hidden grid, arrows move only when they clarify a dependency, and labels remain sparse enough that the geometry, not the text, explains the transformation.

The core visual metaphor is a loom. Source matrices enter as broad woven fields, packing combs them into narrow panels, and vectorization threads those panels through fixed-width lanes. This metaphor should stay subtle. Someone familiar with GEMM should recognize packed A/B panels, tail handling, and SIMD lanes; someone less familiar should still see an elegant progression from irregular layout to disciplined execution.

The aesthetic should feel like a master-level systems diagram rather than a slide illustration. Edges are fine, color is muted, and contrast is reserved for the few places where decisions occur: alignment, lane width, tail masks, and fallback/adapt choices. The piece should look meticulously crafted even at small thesis-print scale, with no visual collision, no noisy ornament, and no ambiguous direction of flow.

The final artifact should leave the impression that expert rules are not isolated heuristics, but a carefully machined interface between memory layout and hardware execution. Its craft lies in making that interface look calm: panels nest into cache blocks, lanes consume packed data, and the whole path resolves into a small rule capsule. It should feel like the work of someone who has spent time with kernels, registers, and page margins alike.

## Subtle reference thread

The hidden reference is the path from BLIS-style packed panels to SIMD-lane consumption: row/column strides are compressed into aligned panel strips, vector lanes reveal fixed-width ISA structure, and the shaded tail cell marks the non-divisible remainder path. The figure avoids naming specific ISAs so it remains portable, while still encoding the concrete concerns that make Packing and Vectorization rules inseparable.
