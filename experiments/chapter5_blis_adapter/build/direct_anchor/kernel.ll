; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

declare void @free(ptr)

declare ptr @malloc(i64)

declare void @buddy_blis_sgemm_6x16(i64, i64, i64, i64, i64, i64, i64, i64, i64)

declare void @buddy_microkernel_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64)

define { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter5_direct_anchor(ptr %0, ptr %1, i64 %2, i64 %3, i64 %4, i64 %5, i64 %6, ptr %7, ptr %8, i64 %9, i64 %10, i64 %11, i64 %12, i64 %13, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20) {
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

43:                                               ; preds = %176, %21
  %44 = phi i64 [ %177, %176 ], [ 0, %21 ]
  %45 = icmp slt i64 %44, 256
  br i1 %45, label %46, label %178

46:                                               ; preds = %173, %43
  %47 = phi i64 [ %175, %173 ], [ 0, %43 ]
  %48 = icmp slt i64 %47, 256
  br i1 %48, label %49, label %176

49:                                               ; preds = %46
  %50 = call ptr @malloc(i64 add (i64 ptrtoint (ptr getelementptr (float, ptr null, i64 2048) to i64), i64 64))
  %51 = ptrtoint ptr %50 to i64
  %52 = add i64 %51, 63
  %53 = urem i64 %52, 64
  %54 = sub i64 %52, %53
  %55 = inttoptr i64 %54 to ptr
  %56 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } undef, ptr %50, 0
  %57 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %56, ptr %55, 1
  %58 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %57, i64 0, 2
  %59 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %58, i64 2, 3, 0
  %60 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %59, i64 64, 3, 1
  %61 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %60, i64 16, 3, 2
  %62 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %61, i64 1024, 4, 0
  %63 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %62, i64 16, 4, 1
  %64 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %63, i64 1, 4, 2
  br label %65

65:                                               ; preds = %93, %49
  %66 = phi i64 [ %94, %93 ], [ 0, %49 ]
  %67 = icmp slt i64 %66, 2
  br i1 %67, label %68, label %95

68:                                               ; preds = %91, %65
  %69 = phi i64 [ %92, %91 ], [ 0, %65 ]
  %70 = icmp slt i64 %69, 64
  br i1 %70, label %71, label %93

71:                                               ; preds = %74, %68
  %72 = phi i64 [ %90, %74 ], [ 0, %68 ]
  %73 = icmp slt i64 %72, 16
  br i1 %73, label %74, label %91

74:                                               ; preds = %71
  %75 = add i64 %47, %69
  %76 = mul i64 %66, 16
  %77 = add i64 %76, %72
  %78 = add i64 %44, %77
  %79 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 1
  %80 = mul i64 %75, 256
  %81 = add i64 %80, %78
  %82 = getelementptr float, ptr %79, i64 %81
  %83 = load float, ptr %82, align 4
  %84 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %64, 1
  %85 = mul i64 %66, 1024
  %86 = mul i64 %69, 16
  %87 = add i64 %85, %86
  %88 = add i64 %87, %72
  %89 = getelementptr float, ptr %84, i64 %88
  store float %83, ptr %89, align 4
  %90 = add i64 %72, 1
  br label %71

91:                                               ; preds = %71
  %92 = add i64 %69, 1
  br label %68

93:                                               ; preds = %68
  %94 = add i64 %66, 1
  br label %65

95:                                               ; preds = %65
  %96 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %64, 1
  %97 = ptrtoint ptr %96 to i64
  br label %98

98:                                               ; preds = %170, %95
  %99 = phi i64 [ %172, %170 ], [ 0, %95 ]
  %100 = icmp slt i64 %99, 192
  br i1 %100, label %101, label %173

101:                                              ; preds = %98
  %102 = call ptr @malloc(i64 add (i64 ptrtoint (ptr getelementptr (float, ptr null, i64 1536) to i64), i64 64))
  %103 = ptrtoint ptr %102 to i64
  %104 = add i64 %103, 63
  %105 = urem i64 %104, 64
  %106 = sub i64 %104, %105
  %107 = inttoptr i64 %106 to ptr
  %108 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } undef, ptr %102, 0
  %109 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %108, ptr %107, 1
  %110 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %109, i64 0, 2
  %111 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %110, i64 4, 3, 0
  %112 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %111, i64 64, 3, 1
  %113 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %112, i64 6, 3, 2
  %114 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %113, i64 384, 4, 0
  %115 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %114, i64 6, 4, 1
  %116 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %115, i64 1, 4, 2
  br label %117

117:                                              ; preds = %145, %101
  %118 = phi i64 [ %146, %145 ], [ 0, %101 ]
  %119 = icmp slt i64 %118, 4
  br i1 %119, label %120, label %147

120:                                              ; preds = %143, %117
  %121 = phi i64 [ %144, %143 ], [ 0, %117 ]
  %122 = icmp slt i64 %121, 64
  br i1 %122, label %123, label %145

123:                                              ; preds = %126, %120
  %124 = phi i64 [ %142, %126 ], [ 0, %120 ]
  %125 = icmp slt i64 %124, 6
  br i1 %125, label %126, label %143

126:                                              ; preds = %123
  %127 = mul i64 %118, 6
  %128 = add i64 %127, %124
  %129 = add i64 %99, %128
  %130 = add i64 %47, %121
  %131 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 1
  %132 = mul i64 %129, 256
  %133 = add i64 %132, %130
  %134 = getelementptr float, ptr %131, i64 %133
  %135 = load float, ptr %134, align 4
  %136 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %116, 1
  %137 = mul i64 %118, 384
  %138 = mul i64 %121, 6
  %139 = add i64 %137, %138
  %140 = add i64 %139, %124
  %141 = getelementptr float, ptr %136, i64 %140
  store float %135, ptr %141, align 4
  %142 = add i64 %124, 1
  br label %123

143:                                              ; preds = %123
  %144 = add i64 %121, 1
  br label %120

145:                                              ; preds = %120
  %146 = add i64 %118, 1
  br label %117

147:                                              ; preds = %117
  %148 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %116, 1
  %149 = ptrtoint ptr %148 to i64
  %150 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %151 = ptrtoint ptr %150 to i64
  br label %152

152:                                              ; preds = %168, %147
  %153 = phi i64 [ %169, %168 ], [ 0, %147 ]
  %154 = icmp slt i64 %153, 2
  br i1 %154, label %155, label %170

155:                                              ; preds = %158, %152
  %156 = phi i64 [ %167, %158 ], [ 0, %152 ]
  %157 = icmp slt i64 %156, 4
  br i1 %157, label %158, label %168

158:                                              ; preds = %155
  %159 = mul i64 %156, 384
  %160 = mul i64 %153, 1024
  %161 = mul i64 %156, 6
  %162 = add i64 %99, %161
  %163 = mul i64 %153, 16
  %164 = add i64 %44, %163
  %165 = mul i64 %162, 256
  %166 = add i64 %165, %164
  call void @buddy_blis_sgemm_6x16(i64 64, i64 %149, i64 %159, i64 %97, i64 %160, i64 %151, i64 %166, i64 256, i64 1)
  %167 = add i64 %156, 1
  br label %155

168:                                              ; preds = %155
  %169 = add i64 %153, 1
  br label %152

170:                                              ; preds = %152
  %171 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %116, 0
  call void @free(ptr %171)
  %172 = add i64 %99, 24
  br label %98

173:                                              ; preds = %98
  %174 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %64, 0
  call void @free(ptr %174)
  %175 = add i64 %47, 64
  br label %46

176:                                              ; preds = %46
  %177 = add i64 %44, 32
  br label %43

178:                                              ; preds = %43
  ret { ptr, ptr, i64, [2 x i64], [2 x i64] } %42
}

define void @_mlir_ciface_chapter5_direct_anchor(ptr %0, ptr %1, ptr %2, ptr %3) {
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
  %29 = call { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter5_direct_anchor(ptr %6, ptr %7, i64 %8, i64 %9, i64 %10, i64 %11, i64 %12, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20, ptr %22, ptr %23, i64 %24, i64 %25, i64 %26, i64 %27, i64 %28)
  store { ptr, ptr, i64, [2 x i64], [2 x i64] } %29, ptr %0, align 8
  ret void
}

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
