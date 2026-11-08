; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

define { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_0000_m168_n256_k256_pab_v1(ptr %0, ptr %1, i64 %2, i64 %3, i64 %4, i64 %5, i64 %6, ptr %7, ptr %8, i64 %9, i64 %10, i64 %11, i64 %12, i64 %13, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20) {
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

43:                                               ; preds = %131, %21
  %44 = phi i64 [ %132, %131 ], [ 0, %21 ]
  %45 = icmp slt i64 %44, 192
  br i1 %45, label %46, label %133

46:                                               ; preds = %43
  %47 = sub i64 192, %44
  %48 = call i64 @llvm.smin.i64(i64 %47, i64 168)
  %49 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 0
  %50 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 1
  %51 = insertvalue { ptr, ptr, i64 } undef, ptr %49, 0
  %52 = insertvalue { ptr, ptr, i64 } %51, ptr %50, 1
  %53 = insertvalue { ptr, ptr, i64 } %52, i64 0, 2
  %54 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 2
  %55 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 0
  %56 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 1
  %57 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 0
  %58 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 1
  %59 = mul nsw i64 %44, 256
  %60 = extractvalue { ptr, ptr, i64 } %53, 0
  %61 = extractvalue { ptr, ptr, i64 } %53, 1
  %62 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %60, 0
  %63 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %62, ptr %61, 1
  %64 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %63, i64 %59, 2
  %65 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %64, i64 %48, 3, 0
  %66 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %65, i64 256, 4, 0
  %67 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %66, i64 256, 3, 1
  %68 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %67, i64 1, 4, 1
  %69 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 0
  %70 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %71 = insertvalue { ptr, ptr, i64 } undef, ptr %69, 0
  %72 = insertvalue { ptr, ptr, i64 } %71, ptr %70, 1
  %73 = insertvalue { ptr, ptr, i64 } %72, i64 0, 2
  %74 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 2
  %75 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 0
  %76 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 1
  %77 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 0
  %78 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 1
  %79 = mul nsw i64 %44, 256
  %80 = extractvalue { ptr, ptr, i64 } %73, 0
  %81 = extractvalue { ptr, ptr, i64 } %73, 1
  %82 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %80, 0
  %83 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %82, ptr %81, 1
  %84 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %83, i64 %79, 2
  %85 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %84, i64 %48, 3, 0
  %86 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %85, i64 256, 4, 0
  %87 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %86, i64 256, 3, 1
  %88 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %87, i64 1, 4, 1
  br label %89

89:                                               ; preds = %129, %46
  %90 = phi i64 [ %130, %129 ], [ 0, %46 ]
  %91 = icmp slt i64 %90, %48
  br i1 %91, label %92, label %131

92:                                               ; preds = %127, %89
  %93 = phi i64 [ %128, %127 ], [ 0, %89 ]
  %94 = icmp slt i64 %93, 256
  br i1 %94, label %95, label %129

95:                                               ; preds = %98, %92
  %96 = phi i64 [ %126, %98 ], [ 0, %92 ]
  %97 = icmp slt i64 %96, 256
  br i1 %97, label %98, label %127

98:                                               ; preds = %95
  %99 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %68, 1
  %100 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %68, 2
  %101 = getelementptr float, ptr %99, i64 %100
  %102 = mul i64 %90, 256
  %103 = add i64 %102, %96
  %104 = getelementptr float, ptr %101, i64 %103
  %105 = load float, ptr %104, align 4
  %106 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 1
  %107 = mul i64 %96, 256
  %108 = add i64 %107, %93
  %109 = getelementptr float, ptr %106, i64 %108
  %110 = load float, ptr %109, align 4
  %111 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %88, 1
  %112 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %88, 2
  %113 = getelementptr float, ptr %111, i64 %112
  %114 = mul i64 %90, 256
  %115 = add i64 %114, %93
  %116 = getelementptr float, ptr %113, i64 %115
  %117 = load float, ptr %116, align 4
  %118 = fmul float %105, %110
  %119 = fadd float %117, %118
  %120 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %88, 1
  %121 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %88, 2
  %122 = getelementptr float, ptr %120, i64 %121
  %123 = mul i64 %90, 256
  %124 = add i64 %123, %93
  %125 = getelementptr float, ptr %122, i64 %124
  store float %119, ptr %125, align 4
  %126 = add i64 %96, 1
  br label %95

127:                                              ; preds = %95
  %128 = add i64 %93, 1
  br label %92

129:                                              ; preds = %92
  %130 = add i64 %90, 1
  br label %89

131:                                              ; preds = %89
  %132 = add i64 %44, 168
  br label %43

133:                                              ; preds = %43
  ret { ptr, ptr, i64, [2 x i64], [2 x i64] } %42
}

define void @_mlir_ciface_chapter4_0000_m168_n256_k256_pab_v1(ptr %0, ptr %1, ptr %2, ptr %3) {
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
  %29 = call { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_0000_m168_n256_k256_pab_v1(ptr %6, ptr %7, i64 %8, i64 %9, i64 %10, i64 %11, i64 %12, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20, ptr %22, ptr %23, i64 %24, i64 %25, i64 %26, i64 %27, i64 %28)
  store { ptr, ptr, i64, [2 x i64], [2 x i64] } %29, ptr %0, align 8
  ret void
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.smin.i64(i64, i64) #0

attributes #0 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
