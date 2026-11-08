; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

define { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_0013_m168_n192_k256_pab_v1(ptr %0, ptr %1, i64 %2, i64 %3, i64 %4, i64 %5, i64 %6, ptr %7, ptr %8, i64 %9, i64 %10, i64 %11, i64 %12, i64 %13, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20) {
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

43:                                               ; preds = %160, %21
  %44 = phi i64 [ %161, %160 ], [ 0, %21 ]
  %45 = icmp slt i64 %44, 192
  br i1 %45, label %46, label %162

46:                                               ; preds = %158, %43
  %47 = phi i64 [ %159, %158 ], [ 0, %43 ]
  %48 = icmp slt i64 %47, 256
  br i1 %48, label %49, label %160

49:                                               ; preds = %46
  %50 = sub i64 192, %44
  %51 = call i64 @llvm.smin.i64(i64 %50, i64 168)
  %52 = sub i64 256, %47
  %53 = call i64 @llvm.smin.i64(i64 %52, i64 192)
  %54 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 0
  %55 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 1
  %56 = insertvalue { ptr, ptr, i64 } undef, ptr %54, 0
  %57 = insertvalue { ptr, ptr, i64 } %56, ptr %55, 1
  %58 = insertvalue { ptr, ptr, i64 } %57, i64 0, 2
  %59 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 2
  %60 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 0
  %61 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 1
  %62 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 0
  %63 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 1
  %64 = mul nsw i64 %44, 256
  %65 = extractvalue { ptr, ptr, i64 } %58, 0
  %66 = extractvalue { ptr, ptr, i64 } %58, 1
  %67 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %65, 0
  %68 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %67, ptr %66, 1
  %69 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %68, i64 %64, 2
  %70 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %69, i64 %51, 3, 0
  %71 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %70, i64 256, 4, 0
  %72 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %71, i64 256, 3, 1
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
  %84 = extractvalue { ptr, ptr, i64 } %78, 0
  %85 = extractvalue { ptr, ptr, i64 } %78, 1
  %86 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %84, 0
  %87 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %86, ptr %85, 1
  %88 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %87, i64 %47, 2
  %89 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %88, i64 256, 3, 0
  %90 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %89, i64 256, 4, 0
  %91 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %90, i64 %53, 3, 1
  %92 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %91, i64 1, 4, 1
  %93 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 0
  %94 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %95 = insertvalue { ptr, ptr, i64 } undef, ptr %93, 0
  %96 = insertvalue { ptr, ptr, i64 } %95, ptr %94, 1
  %97 = insertvalue { ptr, ptr, i64 } %96, i64 0, 2
  %98 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 2
  %99 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 0
  %100 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 1
  %101 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 0
  %102 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 1
  %103 = mul nsw i64 %44, 256
  %104 = add i64 %103, %47
  %105 = extractvalue { ptr, ptr, i64 } %97, 0
  %106 = extractvalue { ptr, ptr, i64 } %97, 1
  %107 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %105, 0
  %108 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %107, ptr %106, 1
  %109 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %108, i64 %104, 2
  %110 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %109, i64 %51, 3, 0
  %111 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %110, i64 256, 4, 0
  %112 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %111, i64 %53, 3, 1
  %113 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %112, i64 1, 4, 1
  br label %114

114:                                              ; preds = %156, %49
  %115 = phi i64 [ %157, %156 ], [ 0, %49 ]
  %116 = icmp slt i64 %115, %51
  br i1 %116, label %117, label %158

117:                                              ; preds = %154, %114
  %118 = phi i64 [ %155, %154 ], [ 0, %114 ]
  %119 = icmp slt i64 %118, %53
  br i1 %119, label %120, label %156

120:                                              ; preds = %123, %117
  %121 = phi i64 [ %153, %123 ], [ 0, %117 ]
  %122 = icmp slt i64 %121, 256
  br i1 %122, label %123, label %154

123:                                              ; preds = %120
  %124 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %73, 1
  %125 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %73, 2
  %126 = getelementptr float, ptr %124, i64 %125
  %127 = mul i64 %115, 256
  %128 = add i64 %127, %121
  %129 = getelementptr float, ptr %126, i64 %128
  %130 = load float, ptr %129, align 4
  %131 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %92, 1
  %132 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %92, 2
  %133 = getelementptr float, ptr %131, i64 %132
  %134 = mul i64 %121, 256
  %135 = add i64 %134, %118
  %136 = getelementptr float, ptr %133, i64 %135
  %137 = load float, ptr %136, align 4
  %138 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %113, 1
  %139 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %113, 2
  %140 = getelementptr float, ptr %138, i64 %139
  %141 = mul i64 %115, 256
  %142 = add i64 %141, %118
  %143 = getelementptr float, ptr %140, i64 %142
  %144 = load float, ptr %143, align 4
  %145 = fmul float %130, %137
  %146 = fadd float %144, %145
  %147 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %113, 1
  %148 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %113, 2
  %149 = getelementptr float, ptr %147, i64 %148
  %150 = mul i64 %115, 256
  %151 = add i64 %150, %118
  %152 = getelementptr float, ptr %149, i64 %151
  store float %146, ptr %152, align 4
  %153 = add i64 %121, 1
  br label %120

154:                                              ; preds = %120
  %155 = add i64 %118, 1
  br label %117

156:                                              ; preds = %117
  %157 = add i64 %115, 1
  br label %114

158:                                              ; preds = %114
  %159 = add i64 %47, 192
  br label %46

160:                                              ; preds = %46
  %161 = add i64 %44, 168
  br label %43

162:                                              ; preds = %43
  ret { ptr, ptr, i64, [2 x i64], [2 x i64] } %42
}

define void @_mlir_ciface_chapter4_0013_m168_n192_k256_pab_v1(ptr %0, ptr %1, ptr %2, ptr %3) {
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
  %29 = call { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_0013_m168_n192_k256_pab_v1(ptr %6, ptr %7, i64 %8, i64 %9, i64 %10, i64 %11, i64 %12, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20, ptr %22, ptr %23, i64 %24, i64 %25, i64 %26, i64 %27, i64 %28)
  store { ptr, ptr, i64, [2 x i64], [2 x i64] } %29, ptr %0, align 8
  ret void
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.smin.i64(i64, i64) #0

attributes #0 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
