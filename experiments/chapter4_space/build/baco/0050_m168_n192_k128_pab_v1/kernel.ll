; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

define { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_0050_m168_n192_k128_pab_v1(ptr %0, ptr %1, i64 %2, i64 %3, i64 %4, i64 %5, i64 %6, ptr %7, ptr %8, i64 %9, i64 %10, i64 %11, i64 %12, i64 %13, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20) {
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

43:                                               ; preds = %168, %21
  %44 = phi i64 [ %169, %168 ], [ 0, %21 ]
  %45 = icmp slt i64 %44, 192
  br i1 %45, label %46, label %170

46:                                               ; preds = %166, %43
  %47 = phi i64 [ %167, %166 ], [ 0, %43 ]
  %48 = icmp slt i64 %47, 256
  br i1 %48, label %49, label %168

49:                                               ; preds = %164, %46
  %50 = phi i64 [ %165, %164 ], [ 0, %46 ]
  %51 = icmp slt i64 %50, 256
  br i1 %51, label %52, label %166

52:                                               ; preds = %49
  %53 = sub i64 192, %44
  %54 = call i64 @llvm.smin.i64(i64 %53, i64 168)
  %55 = sub i64 256, %47
  %56 = call i64 @llvm.smin.i64(i64 %55, i64 192)
  %57 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 0
  %58 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 1
  %59 = insertvalue { ptr, ptr, i64 } undef, ptr %57, 0
  %60 = insertvalue { ptr, ptr, i64 } %59, ptr %58, 1
  %61 = insertvalue { ptr, ptr, i64 } %60, i64 0, 2
  %62 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 2
  %63 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 0
  %64 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 1
  %65 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 0
  %66 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 1
  %67 = mul nsw i64 %44, 256
  %68 = add i64 %67, %50
  %69 = extractvalue { ptr, ptr, i64 } %61, 0
  %70 = extractvalue { ptr, ptr, i64 } %61, 1
  %71 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %69, 0
  %72 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %71, ptr %70, 1
  %73 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %72, i64 %68, 2
  %74 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %73, i64 %54, 3, 0
  %75 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %74, i64 256, 4, 0
  %76 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %75, i64 128, 3, 1
  %77 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %76, i64 1, 4, 1
  %78 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 0
  %79 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 1
  %80 = insertvalue { ptr, ptr, i64 } undef, ptr %78, 0
  %81 = insertvalue { ptr, ptr, i64 } %80, ptr %79, 1
  %82 = insertvalue { ptr, ptr, i64 } %81, i64 0, 2
  %83 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 2
  %84 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 0
  %85 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 1
  %86 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 4, 0
  %87 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 4, 1
  %88 = mul nsw i64 %50, 256
  %89 = add i64 %88, %47
  %90 = extractvalue { ptr, ptr, i64 } %82, 0
  %91 = extractvalue { ptr, ptr, i64 } %82, 1
  %92 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %90, 0
  %93 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %92, ptr %91, 1
  %94 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %93, i64 %89, 2
  %95 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %94, i64 128, 3, 0
  %96 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %95, i64 256, 4, 0
  %97 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %96, i64 %56, 3, 1
  %98 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %97, i64 1, 4, 1
  %99 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 0
  %100 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %101 = insertvalue { ptr, ptr, i64 } undef, ptr %99, 0
  %102 = insertvalue { ptr, ptr, i64 } %101, ptr %100, 1
  %103 = insertvalue { ptr, ptr, i64 } %102, i64 0, 2
  %104 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 2
  %105 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 0
  %106 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 1
  %107 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 0
  %108 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 1
  %109 = mul nsw i64 %44, 256
  %110 = add i64 %109, %47
  %111 = extractvalue { ptr, ptr, i64 } %103, 0
  %112 = extractvalue { ptr, ptr, i64 } %103, 1
  %113 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %111, 0
  %114 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %113, ptr %112, 1
  %115 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %114, i64 %110, 2
  %116 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %115, i64 %54, 3, 0
  %117 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %116, i64 256, 4, 0
  %118 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %117, i64 %56, 3, 1
  %119 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %118, i64 1, 4, 1
  br label %120

120:                                              ; preds = %162, %52
  %121 = phi i64 [ %163, %162 ], [ 0, %52 ]
  %122 = icmp slt i64 %121, %54
  br i1 %122, label %123, label %164

123:                                              ; preds = %160, %120
  %124 = phi i64 [ %161, %160 ], [ 0, %120 ]
  %125 = icmp slt i64 %124, %56
  br i1 %125, label %126, label %162

126:                                              ; preds = %129, %123
  %127 = phi i64 [ %159, %129 ], [ 0, %123 ]
  %128 = icmp slt i64 %127, 128
  br i1 %128, label %129, label %160

129:                                              ; preds = %126
  %130 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %77, 1
  %131 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %77, 2
  %132 = getelementptr float, ptr %130, i64 %131
  %133 = mul i64 %121, 256
  %134 = add i64 %133, %127
  %135 = getelementptr float, ptr %132, i64 %134
  %136 = load float, ptr %135, align 4
  %137 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %98, 1
  %138 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %98, 2
  %139 = getelementptr float, ptr %137, i64 %138
  %140 = mul i64 %127, 256
  %141 = add i64 %140, %124
  %142 = getelementptr float, ptr %139, i64 %141
  %143 = load float, ptr %142, align 4
  %144 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %119, 1
  %145 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %119, 2
  %146 = getelementptr float, ptr %144, i64 %145
  %147 = mul i64 %121, 256
  %148 = add i64 %147, %124
  %149 = getelementptr float, ptr %146, i64 %148
  %150 = load float, ptr %149, align 4
  %151 = fmul float %136, %143
  %152 = fadd float %150, %151
  %153 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %119, 1
  %154 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %119, 2
  %155 = getelementptr float, ptr %153, i64 %154
  %156 = mul i64 %121, 256
  %157 = add i64 %156, %124
  %158 = getelementptr float, ptr %155, i64 %157
  store float %152, ptr %158, align 4
  %159 = add i64 %127, 1
  br label %126

160:                                              ; preds = %126
  %161 = add i64 %124, 1
  br label %123

162:                                              ; preds = %123
  %163 = add i64 %121, 1
  br label %120

164:                                              ; preds = %120
  %165 = add i64 %50, 128
  br label %49

166:                                              ; preds = %49
  %167 = add i64 %47, 192
  br label %46

168:                                              ; preds = %46
  %169 = add i64 %44, 168
  br label %43

170:                                              ; preds = %43
  ret { ptr, ptr, i64, [2 x i64], [2 x i64] } %42
}

define void @_mlir_ciface_chapter4_0050_m168_n192_k128_pab_v1(ptr %0, ptr %1, ptr %2, ptr %3) {
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
  %29 = call { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_0050_m168_n192_k128_pab_v1(ptr %6, ptr %7, i64 %8, i64 %9, i64 %10, i64 %11, i64 %12, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20, ptr %22, ptr %23, i64 %24, i64 %25, i64 %26, i64 %27, i64 %28)
  store { ptr, ptr, i64, [2 x i64], [2 x i64] } %29, ptr %0, align 8
  ret void
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.smin.i64(i64, i64) #0

attributes #0 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
