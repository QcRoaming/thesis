; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

define { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_0005_m168_n256_k128_pab_v1(ptr %0, ptr %1, i64 %2, i64 %3, i64 %4, i64 %5, i64 %6, ptr %7, ptr %8, i64 %9, i64 %10, i64 %11, i64 %12, i64 %13, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20) {
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

43:                                               ; preds = %159, %21
  %44 = phi i64 [ %160, %159 ], [ 0, %21 ]
  %45 = icmp slt i64 %44, 192
  br i1 %45, label %46, label %161

46:                                               ; preds = %157, %43
  %47 = phi i64 [ %158, %157 ], [ 0, %43 ]
  %48 = icmp slt i64 %47, 256
  br i1 %48, label %49, label %159

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
  %63 = add i64 %62, %47
  %64 = extractvalue { ptr, ptr, i64 } %56, 0
  %65 = extractvalue { ptr, ptr, i64 } %56, 1
  %66 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %64, 0
  %67 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %66, ptr %65, 1
  %68 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %67, i64 %63, 2
  %69 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %68, i64 %51, 3, 0
  %70 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %69, i64 256, 4, 0
  %71 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %70, i64 128, 3, 1
  %72 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %71, i64 1, 4, 1
  %73 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 0
  %74 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 1
  %75 = insertvalue { ptr, ptr, i64 } undef, ptr %73, 0
  %76 = insertvalue { ptr, ptr, i64 } %75, ptr %74, 1
  %77 = insertvalue { ptr, ptr, i64 } %76, i64 0, 2
  %78 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 2
  %79 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 0
  %80 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 1
  %81 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 4, 0
  %82 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 4, 1
  %83 = mul nsw i64 %47, 256
  %84 = extractvalue { ptr, ptr, i64 } %77, 0
  %85 = extractvalue { ptr, ptr, i64 } %77, 1
  %86 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %84, 0
  %87 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %86, ptr %85, 1
  %88 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %87, i64 %83, 2
  %89 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %88, i64 128, 3, 0
  %90 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %89, i64 256, 4, 0
  %91 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %90, i64 256, 3, 1
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
  %104 = extractvalue { ptr, ptr, i64 } %97, 0
  %105 = extractvalue { ptr, ptr, i64 } %97, 1
  %106 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %104, 0
  %107 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %106, ptr %105, 1
  %108 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %107, i64 %103, 2
  %109 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %108, i64 %51, 3, 0
  %110 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %109, i64 256, 4, 0
  %111 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %110, i64 256, 3, 1
  %112 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %111, i64 1, 4, 1
  br label %113

113:                                              ; preds = %155, %49
  %114 = phi i64 [ %156, %155 ], [ 0, %49 ]
  %115 = icmp slt i64 %114, %51
  br i1 %115, label %116, label %157

116:                                              ; preds = %153, %113
  %117 = phi i64 [ %154, %153 ], [ 0, %113 ]
  %118 = icmp slt i64 %117, 256
  br i1 %118, label %119, label %155

119:                                              ; preds = %122, %116
  %120 = phi i64 [ %152, %122 ], [ 0, %116 ]
  %121 = icmp slt i64 %120, 128
  br i1 %121, label %122, label %153

122:                                              ; preds = %119
  %123 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %72, 1
  %124 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %72, 2
  %125 = getelementptr float, ptr %123, i64 %124
  %126 = mul i64 %114, 256
  %127 = add i64 %126, %120
  %128 = getelementptr float, ptr %125, i64 %127
  %129 = load float, ptr %128, align 4
  %130 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %92, 1
  %131 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %92, 2
  %132 = getelementptr float, ptr %130, i64 %131
  %133 = mul i64 %120, 256
  %134 = add i64 %133, %117
  %135 = getelementptr float, ptr %132, i64 %134
  %136 = load float, ptr %135, align 4
  %137 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %112, 1
  %138 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %112, 2
  %139 = getelementptr float, ptr %137, i64 %138
  %140 = mul i64 %114, 256
  %141 = add i64 %140, %117
  %142 = getelementptr float, ptr %139, i64 %141
  %143 = load float, ptr %142, align 4
  %144 = fmul float %129, %136
  %145 = fadd float %143, %144
  %146 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %112, 1
  %147 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %112, 2
  %148 = getelementptr float, ptr %146, i64 %147
  %149 = mul i64 %114, 256
  %150 = add i64 %149, %117
  %151 = getelementptr float, ptr %148, i64 %150
  store float %145, ptr %151, align 4
  %152 = add i64 %120, 1
  br label %119

153:                                              ; preds = %119
  %154 = add i64 %117, 1
  br label %116

155:                                              ; preds = %116
  %156 = add i64 %114, 1
  br label %113

157:                                              ; preds = %113
  %158 = add i64 %47, 128
  br label %46

159:                                              ; preds = %46
  %160 = add i64 %44, 168
  br label %43

161:                                              ; preds = %43
  ret { ptr, ptr, i64, [2 x i64], [2 x i64] } %42
}

define void @_mlir_ciface_chapter4_0005_m168_n256_k128_pab_v1(ptr %0, ptr %1, ptr %2, ptr %3) {
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
  %29 = call { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter4_0005_m168_n256_k128_pab_v1(ptr %6, ptr %7, i64 %8, i64 %9, i64 %10, i64 %11, i64 %12, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20, ptr %22, ptr %23, i64 %24, i64 %25, i64 %26, i64 %27, i64 %28)
  store { ptr, ptr, i64, [2 x i64], [2 x i64] } %29, ptr %0, align 8
  ret void
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.smin.i64(i64, i64) #0

attributes #0 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
