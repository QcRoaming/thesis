; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

define { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_fallback_feature_miss(ptr %0, ptr %1, i64 %2, i64 %3, i64 %4, i64 %5, i64 %6, ptr %7, ptr %8, i64 %9, i64 %10, i64 %11, i64 %12, i64 %13, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20) {
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

43:                                               ; preds = %164, %21
  %44 = phi i64 [ %165, %164 ], [ 0, %21 ]
  %45 = icmp slt i64 %44, 192
  br i1 %45, label %46, label %166

46:                                               ; preds = %162, %43
  %47 = phi i64 [ %163, %162 ], [ 0, %43 ]
  %48 = icmp slt i64 %47, 256
  br i1 %48, label %49, label %164

49:                                               ; preds = %160, %46
  %50 = phi i64 [ %161, %160 ], [ 0, %46 ]
  %51 = icmp slt i64 %50, 256
  br i1 %51, label %52, label %162

52:                                               ; preds = %49
  %53 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 0
  %54 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 1
  %55 = insertvalue { ptr, ptr, i64 } undef, ptr %53, 0
  %56 = insertvalue { ptr, ptr, i64 } %55, ptr %54, 1
  %57 = insertvalue { ptr, ptr, i64 } %56, i64 0, 2
  %58 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 2
  %59 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 0
  %60 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 1
  %61 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 0
  %62 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 1
  %63 = mul nsw i64 %44, 256
  %64 = add i64 %63, %50
  %65 = extractvalue { ptr, ptr, i64 } %57, 0
  %66 = extractvalue { ptr, ptr, i64 } %57, 1
  %67 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %65, 0
  %68 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %67, ptr %66, 1
  %69 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %68, i64 %64, 2
  %70 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %69, i64 24, 3, 0
  %71 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %70, i64 256, 4, 0
  %72 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %71, i64 64, 3, 1
  %73 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %72, i64 1, 4, 1
  %74 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 0
  %75 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 1
  %76 = insertvalue { ptr, ptr, i64 } undef, ptr %74, 0
  %77 = insertvalue { ptr, ptr, i64 } %76, ptr %75, 1
  %78 = insertvalue { ptr, ptr, i64 } %77, i64 0, 2
  %79 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 2
  %80 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 0
  %81 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 1
  %82 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 4, 0
  %83 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 4, 1
  %84 = mul nsw i64 %50, 256
  %85 = add i64 %84, %47
  %86 = extractvalue { ptr, ptr, i64 } %78, 0
  %87 = extractvalue { ptr, ptr, i64 } %78, 1
  %88 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %86, 0
  %89 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %88, ptr %87, 1
  %90 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %89, i64 %85, 2
  %91 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %90, i64 64, 3, 0
  %92 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %91, i64 256, 4, 0
  %93 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %92, i64 32, 3, 1
  %94 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %93, i64 1, 4, 1
  %95 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 0
  %96 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %97 = insertvalue { ptr, ptr, i64 } undef, ptr %95, 0
  %98 = insertvalue { ptr, ptr, i64 } %97, ptr %96, 1
  %99 = insertvalue { ptr, ptr, i64 } %98, i64 0, 2
  %100 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 2
  %101 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 0
  %102 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 1
  %103 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 0
  %104 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 1
  %105 = mul nsw i64 %44, 256
  %106 = add i64 %105, %47
  %107 = extractvalue { ptr, ptr, i64 } %99, 0
  %108 = extractvalue { ptr, ptr, i64 } %99, 1
  %109 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %107, 0
  %110 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %109, ptr %108, 1
  %111 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %110, i64 %106, 2
  %112 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %111, i64 24, 3, 0
  %113 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %112, i64 256, 4, 0
  %114 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %113, i64 32, 3, 1
  %115 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %114, i64 1, 4, 1
  br label %116

116:                                              ; preds = %158, %52
  %117 = phi i64 [ %159, %158 ], [ 0, %52 ]
  %118 = icmp slt i64 %117, 24
  br i1 %118, label %119, label %160

119:                                              ; preds = %156, %116
  %120 = phi i64 [ %157, %156 ], [ 0, %116 ]
  %121 = icmp slt i64 %120, 32
  br i1 %121, label %122, label %158

122:                                              ; preds = %125, %119
  %123 = phi i64 [ %155, %125 ], [ 0, %119 ]
  %124 = icmp slt i64 %123, 64
  br i1 %124, label %125, label %156

125:                                              ; preds = %122
  %126 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %73, 1
  %127 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %73, 2
  %128 = getelementptr float, ptr %126, i64 %127
  %129 = mul i64 %117, 256
  %130 = add i64 %129, %123
  %131 = getelementptr float, ptr %128, i64 %130
  %132 = load float, ptr %131, align 4
  %133 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %94, 1
  %134 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %94, 2
  %135 = getelementptr float, ptr %133, i64 %134
  %136 = mul i64 %123, 256
  %137 = add i64 %136, %120
  %138 = getelementptr float, ptr %135, i64 %137
  %139 = load float, ptr %138, align 4
  %140 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %115, 1
  %141 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %115, 2
  %142 = getelementptr float, ptr %140, i64 %141
  %143 = mul i64 %117, 256
  %144 = add i64 %143, %120
  %145 = getelementptr float, ptr %142, i64 %144
  %146 = load float, ptr %145, align 4
  %147 = fmul float %132, %139
  %148 = fadd float %146, %147
  %149 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %115, 1
  %150 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %115, 2
  %151 = getelementptr float, ptr %149, i64 %150
  %152 = mul i64 %117, 256
  %153 = add i64 %152, %120
  %154 = getelementptr float, ptr %151, i64 %153
  store float %148, ptr %154, align 4
  %155 = add i64 %123, 1
  br label %122

156:                                              ; preds = %122
  %157 = add i64 %120, 1
  br label %119

158:                                              ; preds = %119
  %159 = add i64 %117, 1
  br label %116

160:                                              ; preds = %116
  %161 = add i64 %50, 64
  br label %49

162:                                              ; preds = %49
  %163 = add i64 %47, 32
  br label %46

164:                                              ; preds = %46
  %165 = add i64 %44, 24
  br label %43

166:                                              ; preds = %43
  ret { ptr, ptr, i64, [2 x i64], [2 x i64] } %42
}

define void @_mlir_ciface_chapter4_fallback_feature_miss(ptr %0, ptr %1, ptr %2, ptr %3) {
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
  %29 = call { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_fallback_feature_miss(ptr %6, ptr %7, i64 %8, i64 %9, i64 %10, i64 %11, i64 %12, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20, ptr %22, ptr %23, i64 %24, i64 %25, i64 %26, i64 %27, i64 %28)
  store { ptr, ptr, i64, [2 x i64], [2 x i64] } %29, ptr %0, align 8
  ret void
}

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
