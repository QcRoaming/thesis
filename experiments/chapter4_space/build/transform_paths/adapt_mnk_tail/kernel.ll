; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

define { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_adapt_mnk_tail(ptr %0, ptr %1, i64 %2, i64 %3, i64 %4, i64 %5, i64 %6, ptr %7, ptr %8, i64 %9, i64 %10, i64 %11, i64 %12, i64 %13, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20) {
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
  br label %43

43:                                               ; preds = %170, %21
  %44 = phi i64 [ %171, %170 ], [ 0, %21 ]
  %45 = icmp slt i64 %44, 190
  br i1 %45, label %46, label %172

46:                                               ; preds = %168, %43
  %47 = phi i64 [ %169, %168 ], [ 0, %43 ]
  %48 = icmp slt i64 %47, 250
  br i1 %48, label %49, label %170

49:                                               ; preds = %166, %46
  %50 = phi i64 [ %167, %166 ], [ 0, %46 ]
  %51 = icmp slt i64 %50, 250
  br i1 %51, label %52, label %168

52:                                               ; preds = %49
  %53 = sub i64 190, %44
  %54 = call i64 @llvm.smin.i64(i64 %53, i64 24)
  %55 = sub i64 250, %47
  %56 = call i64 @llvm.smin.i64(i64 %55, i64 32)
  %57 = sub i64 250, %50
  %58 = call i64 @llvm.smin.i64(i64 %57, i64 64)
  %59 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 0
  %60 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 1
  %61 = insertvalue { ptr, ptr, i64 } undef, ptr %59, 0
  %62 = insertvalue { ptr, ptr, i64 } %61, ptr %60, 1
  %63 = insertvalue { ptr, ptr, i64 } %62, i64 0, 2
  %64 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 2
  %65 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 0
  %66 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 1
  %67 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 0
  %68 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 1
  %69 = mul nsw i64 %44, 250
  %70 = add i64 %69, %50
  %71 = extractvalue { ptr, ptr, i64 } %63, 0
  %72 = extractvalue { ptr, ptr, i64 } %63, 1
  %73 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %71, 0
  %74 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %73, ptr %72, 1
  %75 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %74, i64 %70, 2
  %76 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %75, i64 %54, 3, 0
  %77 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %76, i64 250, 4, 0
  %78 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %77, i64 %58, 3, 1
  %79 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %78, i64 1, 4, 1
  %80 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 0
  %81 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 1
  %82 = insertvalue { ptr, ptr, i64 } undef, ptr %80, 0
  %83 = insertvalue { ptr, ptr, i64 } %82, ptr %81, 1
  %84 = insertvalue { ptr, ptr, i64 } %83, i64 0, 2
  %85 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 2
  %86 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 0
  %87 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 1
  %88 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 4, 0
  %89 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 4, 1
  %90 = mul nsw i64 %50, 250
  %91 = add i64 %90, %47
  %92 = extractvalue { ptr, ptr, i64 } %84, 0
  %93 = extractvalue { ptr, ptr, i64 } %84, 1
  %94 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %92, 0
  %95 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %94, ptr %93, 1
  %96 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %95, i64 %91, 2
  %97 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %96, i64 %58, 3, 0
  %98 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %97, i64 250, 4, 0
  %99 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %98, i64 %56, 3, 1
  %100 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %99, i64 1, 4, 1
  %101 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 0
  %102 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %103 = insertvalue { ptr, ptr, i64 } undef, ptr %101, 0
  %104 = insertvalue { ptr, ptr, i64 } %103, ptr %102, 1
  %105 = insertvalue { ptr, ptr, i64 } %104, i64 0, 2
  %106 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 2
  %107 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 0
  %108 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 1
  %109 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 0
  %110 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 1
  %111 = mul nsw i64 %44, 250
  %112 = add i64 %111, %47
  %113 = extractvalue { ptr, ptr, i64 } %105, 0
  %114 = extractvalue { ptr, ptr, i64 } %105, 1
  %115 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %113, 0
  %116 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %115, ptr %114, 1
  %117 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %116, i64 %112, 2
  %118 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %117, i64 %54, 3, 0
  %119 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %118, i64 250, 4, 0
  %120 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %119, i64 %56, 3, 1
  %121 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %120, i64 1, 4, 1
  br label %122

122:                                              ; preds = %164, %52
  %123 = phi i64 [ %165, %164 ], [ 0, %52 ]
  %124 = icmp slt i64 %123, %54
  br i1 %124, label %125, label %166

125:                                              ; preds = %162, %122
  %126 = phi i64 [ %163, %162 ], [ 0, %122 ]
  %127 = icmp slt i64 %126, %56
  br i1 %127, label %128, label %164

128:                                              ; preds = %131, %125
  %129 = phi i64 [ %161, %131 ], [ 0, %125 ]
  %130 = icmp slt i64 %129, %58
  br i1 %130, label %131, label %162

131:                                              ; preds = %128
  %132 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %79, 1
  %133 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %79, 2
  %134 = getelementptr float, ptr %132, i64 %133
  %135 = mul i64 %123, 250
  %136 = add i64 %135, %129
  %137 = getelementptr float, ptr %134, i64 %136
  %138 = load float, ptr %137, align 4
  %139 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %100, 1
  %140 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %100, 2
  %141 = getelementptr float, ptr %139, i64 %140
  %142 = mul i64 %129, 250
  %143 = add i64 %142, %126
  %144 = getelementptr float, ptr %141, i64 %143
  %145 = load float, ptr %144, align 4
  %146 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %121, 1
  %147 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %121, 2
  %148 = getelementptr float, ptr %146, i64 %147
  %149 = mul i64 %123, 250
  %150 = add i64 %149, %126
  %151 = getelementptr float, ptr %148, i64 %150
  %152 = load float, ptr %151, align 4
  %153 = fmul float %138, %145
  %154 = fadd float %152, %153
  %155 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %121, 1
  %156 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %121, 2
  %157 = getelementptr float, ptr %155, i64 %156
  %158 = mul i64 %123, 250
  %159 = add i64 %158, %126
  %160 = getelementptr float, ptr %157, i64 %159
  store float %154, ptr %160, align 4
  %161 = add i64 %129, 1
  br label %128

162:                                              ; preds = %128
  %163 = add i64 %126, 1
  br label %125

164:                                              ; preds = %125
  %165 = add i64 %123, 1
  br label %122

166:                                              ; preds = %122
  %167 = add i64 %50, 64
  br label %49

168:                                              ; preds = %49
  %169 = add i64 %47, 32
  br label %46

170:                                              ; preds = %46
  %171 = add i64 %44, 24
  br label %43

172:                                              ; preds = %43
  ret { ptr, ptr, i64, [2 x i64], [2 x i64] } %42
}

define void @_mlir_ciface_chapter4_adapt_mnk_tail(ptr %0, ptr %1, ptr %2, ptr %3) {
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
  %29 = call { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_adapt_mnk_tail(ptr %6, ptr %7, i64 %8, i64 %9, i64 %10, i64 %11, i64 %12, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20, ptr %22, ptr %23, i64 %24, i64 %25, i64 %26, i64 %27, i64 %28)
  store { ptr, ptr, i64, [2 x i64], [2 x i64] } %29, ptr %0, align 8
  ret void
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.smin.i64(i64, i64) #0

attributes #0 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
