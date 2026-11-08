; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

define { ptr, ptr, i64, [2 x i64], [2 x i64] } @integrated_anchor_192x256x256_f32_m24_n32_k128_pnone_v0(ptr %0, ptr %1, i64 %2, i64 %3, i64 %4, i64 %5, i64 %6, ptr %7, ptr %8, i64 %9, i64 %10, i64 %11, i64 %12, i64 %13, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20) {
  %22 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %7, 0
  %23 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %22, ptr %8, 1
  %24 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %23, i64 %9, 2
  %25 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %24, i64 %10, 3, 0
  %26 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %25, i64 %12, 4, 0
  %27 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %26, i64 %11, 3, 1
  %28 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %27, i64 %13, 4, 1
  %29 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %0, 0
  %30 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %29, ptr %1, 1
  %31 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %30, i64 %2, 2
  %32 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %31, i64 %3, 3, 0
  %33 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %32, i64 %5, 4, 0
  %34 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %33, i64 %4, 3, 1
  %35 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %34, i64 %6, 4, 1
  %36 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %14, 0
  %37 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %36, ptr %15, 1
  %38 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %37, i64 %16, 2
  %39 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %38, i64 %17, 3, 0
  %40 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %39, i64 %19, 4, 0
  %41 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %40, i64 %18, 3, 1
  %42 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %41, i64 %20, 4, 1
  %43 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 0
  %44 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 1
  %45 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 1
  br label %46

46:                                               ; preds = %177, %21
  %47 = phi i64 [ %178, %177 ], [ 0, %21 ]
  %48 = icmp slt i64 %47, %43
  br i1 %48, label %49, label %179

49:                                               ; preds = %175, %46
  %50 = phi i64 [ %176, %175 ], [ 0, %46 ]
  %51 = icmp slt i64 %50, %45
  br i1 %51, label %52, label %177

52:                                               ; preds = %173, %49
  %53 = phi i64 [ %174, %173 ], [ 0, %49 ]
  %54 = icmp slt i64 %53, %44
  br i1 %54, label %55, label %175

55:                                               ; preds = %52
  %56 = sub i64 %43, %47
  %57 = call i64 @llvm.smin.i64(i64 %56, i64 24)
  %58 = sub i64 %45, %50
  %59 = call i64 @llvm.smin.i64(i64 %58, i64 32)
  %60 = sub i64 %44, %53
  %61 = call i64 @llvm.smin.i64(i64 %60, i64 128)
  %62 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 0
  %63 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 1
  %64 = insertvalue { ptr, ptr, i64 } undef, ptr %62, 0
  %65 = insertvalue { ptr, ptr, i64 } %64, ptr %63, 1
  %66 = insertvalue { ptr, ptr, i64 } %65, i64 0, 2
  %67 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 2
  %68 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 0
  %69 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 1
  %70 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 0
  %71 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 1
  %72 = mul nsw i64 %47, %70
  %73 = add i64 %72, %53
  %74 = extractvalue { ptr, ptr, i64 } %66, 0
  %75 = extractvalue { ptr, ptr, i64 } %66, 1
  %76 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %74, 0
  %77 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %76, ptr %75, 1
  %78 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %77, i64 %73, 2
  %79 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %78, i64 %57, 3, 0
  %80 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %79, i64 %70, 4, 0
  %81 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %80, i64 %61, 3, 1
  %82 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %81, i64 1, 4, 1
  %83 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 0
  %84 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 1
  %85 = insertvalue { ptr, ptr, i64 } undef, ptr %83, 0
  %86 = insertvalue { ptr, ptr, i64 } %85, ptr %84, 1
  %87 = insertvalue { ptr, ptr, i64 } %86, i64 0, 2
  %88 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 2
  %89 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 0
  %90 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 1
  %91 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 4, 0
  %92 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 4, 1
  %93 = mul nsw i64 %53, %91
  %94 = add i64 %93, %50
  %95 = extractvalue { ptr, ptr, i64 } %87, 0
  %96 = extractvalue { ptr, ptr, i64 } %87, 1
  %97 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %95, 0
  %98 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %97, ptr %96, 1
  %99 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %98, i64 %94, 2
  %100 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %99, i64 %61, 3, 0
  %101 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %100, i64 %91, 4, 0
  %102 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %101, i64 %59, 3, 1
  %103 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %102, i64 1, 4, 1
  %104 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 0
  %105 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %106 = insertvalue { ptr, ptr, i64 } undef, ptr %104, 0
  %107 = insertvalue { ptr, ptr, i64 } %106, ptr %105, 1
  %108 = insertvalue { ptr, ptr, i64 } %107, i64 0, 2
  %109 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 2
  %110 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 0
  %111 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 1
  %112 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 0
  %113 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 1
  %114 = mul nsw i64 %47, %112
  %115 = add i64 %114, %50
  %116 = extractvalue { ptr, ptr, i64 } %108, 0
  %117 = extractvalue { ptr, ptr, i64 } %108, 1
  %118 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %116, 0
  %119 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %118, ptr %117, 1
  %120 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %119, i64 %115, 2
  %121 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %120, i64 %57, 3, 0
  %122 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %121, i64 %112, 4, 0
  %123 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %122, i64 %59, 3, 1
  %124 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %123, i64 1, 4, 1
  br label %125

125:                                              ; preds = %171, %55
  %126 = phi i64 [ %172, %171 ], [ 0, %55 ]
  %127 = icmp slt i64 %126, %57
  br i1 %127, label %128, label %173

128:                                              ; preds = %169, %125
  %129 = phi i64 [ %170, %169 ], [ 0, %125 ]
  %130 = icmp slt i64 %129, %59
  br i1 %130, label %131, label %171

131:                                              ; preds = %134, %128
  %132 = phi i64 [ %168, %134 ], [ 0, %128 ]
  %133 = icmp slt i64 %132, %61
  br i1 %133, label %134, label %169

134:                                              ; preds = %131
  %135 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %82, 1
  %136 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %82, 2
  %137 = getelementptr float, ptr %135, i64 %136
  %138 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %82, 4, 0
  %139 = mul i64 %126, %138
  %140 = add i64 %139, %132
  %141 = getelementptr float, ptr %137, i64 %140
  %142 = load float, ptr %141, align 4
  %143 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %103, 1
  %144 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %103, 2
  %145 = getelementptr float, ptr %143, i64 %144
  %146 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %103, 4, 0
  %147 = mul i64 %132, %146
  %148 = add i64 %147, %129
  %149 = getelementptr float, ptr %145, i64 %148
  %150 = load float, ptr %149, align 4
  %151 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %124, 1
  %152 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %124, 2
  %153 = getelementptr float, ptr %151, i64 %152
  %154 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %124, 4, 0
  %155 = mul i64 %126, %154
  %156 = add i64 %155, %129
  %157 = getelementptr float, ptr %153, i64 %156
  %158 = load float, ptr %157, align 4
  %159 = fmul float %142, %150
  %160 = fadd float %158, %159
  %161 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %124, 1
  %162 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %124, 2
  %163 = getelementptr float, ptr %161, i64 %162
  %164 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %124, 4, 0
  %165 = mul i64 %126, %164
  %166 = add i64 %165, %129
  %167 = getelementptr float, ptr %163, i64 %166
  store float %160, ptr %167, align 4
  %168 = add i64 %132, 1
  br label %131

169:                                              ; preds = %131
  %170 = add i64 %129, 1
  br label %128

171:                                              ; preds = %128
  %172 = add i64 %126, 1
  br label %125

173:                                              ; preds = %125
  %174 = add i64 %53, 128
  br label %52

175:                                              ; preds = %52
  %176 = add i64 %50, 32
  br label %49

177:                                              ; preds = %49
  %178 = add i64 %47, 24
  br label %46

179:                                              ; preds = %46
  ret { ptr, ptr, i64, [2 x i64], [2 x i64] } %42
}

define void @_mlir_ciface_integrated_anchor_192x256x256_f32_m24_n32_k128_pnone_v0(ptr %0, ptr %1, ptr %2, ptr %3) {
  %5 = load { ptr, ptr, i64, [2 x i64], [2 x i64] }, ptr %1, align 8
  %6 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %5, 0
  %7 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %5, 1
  %8 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %5, 2
  %9 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %5, 3, 0
  %10 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %5, 3, 1
  %11 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %5, 4, 0
  %12 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %5, 4, 1
  %13 = load { ptr, ptr, i64, [2 x i64], [2 x i64] }, ptr %2, align 8
  %14 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %13, 0
  %15 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %13, 1
  %16 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %13, 2
  %17 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %13, 3, 0
  %18 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %13, 3, 1
  %19 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %13, 4, 0
  %20 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %13, 4, 1
  %21 = load { ptr, ptr, i64, [2 x i64], [2 x i64] }, ptr %3, align 8
  %22 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %21, 0
  %23 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %21, 1
  %24 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %21, 2
  %25 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %21, 3, 0
  %26 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %21, 3, 1
  %27 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %21, 4, 0
  %28 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %21, 4, 1
  %29 = call { ptr, ptr, i64, [2 x i64], [2 x i64] } @integrated_anchor_192x256x256_f32_m24_n32_k128_pnone_v0(ptr %6, ptr %7, i64 %8, i64 %9, i64 %10, i64 %11, i64 %12, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20, ptr %22, ptr %23, i64 %24, i64 %25, i64 %26, i64 %27, i64 %28)
  store { ptr, ptr, i64, [2 x i64], [2 x i64] } %29, ptr %0, align 8
  ret void
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.smin.i64(i64, i64) #0

attributes #0 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
