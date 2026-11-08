; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

define { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_0001_m168_n128_k256_pab_v1(ptr %0, ptr %1, i64 %2, i64 %3, i64 %4, i64 %5, i64 %6, ptr %7, ptr %8, i64 %9, i64 %10, i64 %11, i64 %12, i64 %13, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20) {
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

43:                                               ; preds = %158, %21
  %44 = phi i64 [ %159, %158 ], [ 0, %21 ]
  %45 = icmp slt i64 %44, 192
  br i1 %45, label %46, label %160

46:                                               ; preds = %156, %43
  %47 = phi i64 [ %157, %156 ], [ 0, %43 ]
  %48 = icmp slt i64 %47, 256
  br i1 %48, label %49, label %158

49:                                               ; preds = %46
  %50 = sub i64 192, %44
  %51 = call i64 @llvm.smin.i64(i64 %50, i64 168)
  %52 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 0
  %53 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 1
  %54 = insertvalue { ptr, ptr, i64 } undef, ptr %52, 0
  %55 = insertvalue { ptr, ptr, i64 } %54, ptr %53, 1
  %56 = insertvalue { ptr, ptr, i64 } %55, i64 0, 2
  %57 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 2
  %58 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 0
  %59 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 1
  %60 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 0
  %61 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 1
  %62 = mul nsw i64 %44, 256
  %63 = extractvalue { ptr, ptr, i64 } %56, 0
  %64 = extractvalue { ptr, ptr, i64 } %56, 1
  %65 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %63, 0
  %66 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %65, ptr %64, 1
  %67 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %66, i64 %62, 2
  %68 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %67, i64 %51, 3, 0
  %69 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %68, i64 256, 4, 0
  %70 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %69, i64 256, 3, 1
  %71 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %70, i64 1, 4, 1
  %72 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 0
  %73 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 1
  %74 = insertvalue { ptr, ptr, i64 } undef, ptr %72, 0
  %75 = insertvalue { ptr, ptr, i64 } %74, ptr %73, 1
  %76 = insertvalue { ptr, ptr, i64 } %75, i64 0, 2
  %77 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 2
  %78 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 0
  %79 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 1
  %80 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 4, 0
  %81 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 4, 1
  %82 = extractvalue { ptr, ptr, i64 } %76, 0
  %83 = extractvalue { ptr, ptr, i64 } %76, 1
  %84 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %82, 0
  %85 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %84, ptr %83, 1
  %86 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %85, i64 %47, 2
  %87 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %86, i64 256, 3, 0
  %88 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %87, i64 256, 4, 0
  %89 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %88, i64 128, 3, 1
  %90 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %89, i64 1, 4, 1
  %91 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 0
  %92 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %93 = insertvalue { ptr, ptr, i64 } undef, ptr %91, 0
  %94 = insertvalue { ptr, ptr, i64 } %93, ptr %92, 1
  %95 = insertvalue { ptr, ptr, i64 } %94, i64 0, 2
  %96 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 2
  %97 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 0
  %98 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 3, 1
  %99 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 0
  %100 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 1
  %101 = mul nsw i64 %44, 256
  %102 = add i64 %101, %47
  %103 = extractvalue { ptr, ptr, i64 } %95, 0
  %104 = extractvalue { ptr, ptr, i64 } %95, 1
  %105 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %103, 0
  %106 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %105, ptr %104, 1
  %107 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %106, i64 %102, 2
  %108 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %107, i64 %51, 3, 0
  %109 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %108, i64 256, 4, 0
  %110 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %109, i64 128, 3, 1
  %111 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %110, i64 1, 4, 1
  br label %112

112:                                              ; preds = %154, %49
  %113 = phi i64 [ %155, %154 ], [ 0, %49 ]
  %114 = icmp slt i64 %113, %51
  br i1 %114, label %115, label %156

115:                                              ; preds = %152, %112
  %116 = phi i64 [ %153, %152 ], [ 0, %112 ]
  %117 = icmp slt i64 %116, 128
  br i1 %117, label %118, label %154

118:                                              ; preds = %121, %115
  %119 = phi i64 [ %151, %121 ], [ 0, %115 ]
  %120 = icmp slt i64 %119, 256
  br i1 %120, label %121, label %152

121:                                              ; preds = %118
  %122 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %71, 1
  %123 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %71, 2
  %124 = getelementptr float, ptr %122, i64 %123
  %125 = mul i64 %113, 256
  %126 = add i64 %125, %119
  %127 = getelementptr float, ptr %124, i64 %126
  %128 = load float, ptr %127, align 4
  %129 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %90, 1
  %130 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %90, 2
  %131 = getelementptr float, ptr %129, i64 %130
  %132 = mul i64 %119, 256
  %133 = add i64 %132, %116
  %134 = getelementptr float, ptr %131, i64 %133
  %135 = load float, ptr %134, align 4
  %136 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %111, 1
  %137 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %111, 2
  %138 = getelementptr float, ptr %136, i64 %137
  %139 = mul i64 %113, 256
  %140 = add i64 %139, %116
  %141 = getelementptr float, ptr %138, i64 %140
  %142 = load float, ptr %141, align 4
  %143 = fmul float %128, %135
  %144 = fadd float %142, %143
  %145 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %111, 1
  %146 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %111, 2
  %147 = getelementptr float, ptr %145, i64 %146
  %148 = mul i64 %113, 256
  %149 = add i64 %148, %116
  %150 = getelementptr float, ptr %147, i64 %149
  store float %144, ptr %150, align 4
  %151 = add i64 %119, 1
  br label %118

152:                                              ; preds = %118
  %153 = add i64 %116, 1
  br label %115

154:                                              ; preds = %115
  %155 = add i64 %113, 1
  br label %112

156:                                              ; preds = %112
  %157 = add i64 %47, 128
  br label %46

158:                                              ; preds = %46
  %159 = add i64 %44, 168
  br label %43

160:                                              ; preds = %43
  ret { ptr, ptr, i64, [2 x i64], [2 x i64] } %42
}

define void @_mlir_ciface_chapter4_0001_m168_n128_k256_pab_v1(ptr %0, ptr %1, ptr %2, ptr %3) {
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
  %29 = call { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_0001_m168_n128_k256_pab_v1(ptr %6, ptr %7, i64 %8, i64 %9, i64 %10, i64 %11, i64 %12, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20, ptr %22, ptr %23, i64 %24, i64 %25, i64 %26, i64 %27, i64 %28)
  store { ptr, ptr, i64, [2 x i64], [2 x i64] } %29, ptr %0, align 8
  ret void
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.smin.i64(i64, i64) #0

attributes #0 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
