; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

declare void @free(ptr)

declare ptr @malloc(i64)

declare void @buddy_blis_sgemm_6x16_fringe(i64, i64, i64, i64, i64, i64, i64, i64, i64)

declare void @buddy_blis_sgemm_6x16(i64, i64, i64, i64, i64, i64, i64, i64, i64)

declare void @buddy_microkernel_fringe_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64)

declare void @buddy_microkernel_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64)

define { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter5_fringe_dev(ptr %0, ptr %1, i64 %2, i64 %3, i64 %4, i64 %5, i64 %6, ptr %7, ptr %8, i64 %9, i64 %10, i64 %11, i64 %12, i64 %13, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20) {
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

43:                                               ; preds = %249, %21
  %44 = phi i64 [ %252, %249 ], [ 0, %21 ]
  %45 = icmp slt i64 %44, 65
  br i1 %45, label %46, label %253

46:                                               ; preds = %43
  %47 = sub i64 65, %44
  %48 = call i64 @llvm.umin.i64(i64 %47, i64 64)
  %49 = call ptr @malloc(i64 add (i64 ptrtoint (ptr getelementptr (float, ptr null, i64 2048) to i64), i64 64))
  %50 = ptrtoint ptr %49 to i64
  %51 = add i64 %50, 63
  %52 = urem i64 %51, 64
  %53 = sub i64 %51, %52
  %54 = inttoptr i64 %53 to ptr
  %55 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } undef, ptr %49, 0
  %56 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %55, ptr %54, 1
  %57 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %56, i64 0, 2
  %58 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %57, i64 2, 3, 0
  %59 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %58, i64 64, 3, 1
  %60 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %59, i64 16, 3, 2
  %61 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %60, i64 1024, 4, 0
  %62 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %61, i64 16, 4, 1
  %63 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %62, i64 1, 4, 2
  br label %64

64:                                               ; preds = %97, %46
  %65 = phi i64 [ %98, %97 ], [ 0, %46 ]
  %66 = icmp slt i64 %65, 2
  br i1 %66, label %67, label %99

67:                                               ; preds = %95, %64
  %68 = phi i64 [ %96, %95 ], [ 0, %64 ]
  %69 = icmp slt i64 %68, 64
  br i1 %69, label %70, label %97

70:                                               ; preds = %86, %67
  %71 = phi i64 [ %94, %86 ], [ 0, %67 ]
  %72 = icmp slt i64 %71, 16
  br i1 %72, label %73, label %95

73:                                               ; preds = %70
  %74 = add i64 %44, %68
  %75 = mul i64 %65, 16
  %76 = add i64 %75, %71
  %77 = icmp ult i64 %74, 65
  %78 = icmp ult i64 %76, 17
  %79 = and i1 %77, %78
  br i1 %79, label %80, label %86

80:                                               ; preds = %73
  %81 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 1
  %82 = mul i64 %74, 17
  %83 = add i64 %82, %76
  %84 = getelementptr float, ptr %81, i64 %83
  %85 = load float, ptr %84, align 4
  br label %86

86:                                               ; preds = %80, %73
  %87 = phi float [ %85, %80 ], [ 0.000000e+00, %73 ]
  %88 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %63, 1
  %89 = mul i64 %65, 1024
  %90 = mul i64 %68, 16
  %91 = add i64 %89, %90
  %92 = add i64 %91, %71
  %93 = getelementptr float, ptr %88, i64 %92
  store float %87, ptr %93, align 4
  %94 = add i64 %71, 1
  br label %70

95:                                               ; preds = %70
  %96 = add i64 %68, 1
  br label %67

97:                                               ; preds = %67
  %98 = add i64 %65, 1
  br label %64

99:                                               ; preds = %64
  %100 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %63, 1
  %101 = ptrtoint ptr %100 to i64
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

117:                                              ; preds = %150, %99
  %118 = phi i64 [ %151, %150 ], [ 0, %99 ]
  %119 = icmp slt i64 %118, 4
  br i1 %119, label %120, label %152

120:                                              ; preds = %148, %117
  %121 = phi i64 [ %149, %148 ], [ 0, %117 ]
  %122 = icmp slt i64 %121, 64
  br i1 %122, label %123, label %150

123:                                              ; preds = %139, %120
  %124 = phi i64 [ %147, %139 ], [ 0, %120 ]
  %125 = icmp slt i64 %124, 6
  br i1 %125, label %126, label %148

126:                                              ; preds = %123
  %127 = mul i64 %118, 6
  %128 = add i64 %127, %124
  %129 = add i64 %44, %121
  %130 = icmp ult i64 %128, 19
  %131 = icmp ult i64 %129, 65
  %132 = and i1 %130, %131
  br i1 %132, label %133, label %139

133:                                              ; preds = %126
  %134 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 1
  %135 = mul i64 %128, 65
  %136 = add i64 %135, %129
  %137 = getelementptr float, ptr %134, i64 %136
  %138 = load float, ptr %137, align 4
  br label %139

139:                                              ; preds = %133, %126
  %140 = phi float [ %138, %133 ], [ 0.000000e+00, %126 ]
  %141 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %116, 1
  %142 = mul i64 %118, 384
  %143 = mul i64 %121, 6
  %144 = add i64 %142, %143
  %145 = add i64 %144, %124
  %146 = getelementptr float, ptr %141, i64 %145
  store float %140, ptr %146, align 4
  %147 = add i64 %124, 1
  br label %123

148:                                              ; preds = %123
  %149 = add i64 %121, 1
  br label %120

150:                                              ; preds = %120
  %151 = add i64 %118, 1
  br label %117

152:                                              ; preds = %117
  %153 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %116, 1
  %154 = ptrtoint ptr %153 to i64
  %155 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %156 = ptrtoint ptr %155 to i64
  br label %157

157:                                              ; preds = %247, %152
  %158 = phi i64 [ %248, %247 ], [ 0, %152 ]
  %159 = icmp slt i64 %158, 2
  br i1 %159, label %160, label %249

160:                                              ; preds = %245, %157
  %161 = phi i64 [ %246, %245 ], [ 0, %157 ]
  %162 = icmp slt i64 %161, 4
  br i1 %162, label %163, label %247

163:                                              ; preds = %160
  %164 = mul i64 %161, 384
  %165 = mul i64 %158, 1024
  %166 = mul i64 %161, 6
  %167 = mul i64 %158, 16
  %168 = sub i64 19, %166
  %169 = call i64 @llvm.umin.i64(i64 %168, i64 6)
  %170 = sub i64 17, %167
  %171 = call i64 @llvm.umin.i64(i64 %170, i64 16)
  %172 = icmp eq i64 %169, 6
  %173 = icmp eq i64 %171, 16
  %174 = and i1 %172, %173
  br i1 %174, label %175, label %178

175:                                              ; preds = %163
  %176 = mul i64 %161, 102
  %177 = add i64 %176, %167
  call void @buddy_blis_sgemm_6x16(i64 %48, i64 %154, i64 %164, i64 %101, i64 %165, i64 %156, i64 %177, i64 17, i64 1)
  br label %245

178:                                              ; preds = %163
  %179 = call ptr @malloc(i64 add (i64 ptrtoint (ptr getelementptr (float, ptr null, i64 96) to i64), i64 64))
  %180 = ptrtoint ptr %179 to i64
  %181 = add i64 %180, 63
  %182 = urem i64 %181, 64
  %183 = sub i64 %181, %182
  %184 = inttoptr i64 %183 to ptr
  %185 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %179, 0
  %186 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %185, ptr %184, 1
  %187 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %186, i64 0, 2
  %188 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %187, i64 6, 3, 0
  %189 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %188, i64 16, 3, 1
  %190 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %189, i64 16, 4, 0
  %191 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %190, i64 1, 4, 1
  br label %192

192:                                              ; preds = %217, %178
  %193 = phi i64 [ %218, %217 ], [ 0, %178 ]
  %194 = icmp slt i64 %193, 6
  br i1 %194, label %195, label %219

195:                                              ; preds = %210, %192
  %196 = phi i64 [ %216, %210 ], [ 0, %192 ]
  %197 = icmp slt i64 %196, 16
  br i1 %197, label %198, label %217

198:                                              ; preds = %195
  %199 = icmp ult i64 %193, %169
  %200 = icmp ult i64 %196, %171
  %201 = add i64 %166, %193
  %202 = add i64 %167, %196
  %203 = and i1 %199, %200
  br i1 %203, label %204, label %210

204:                                              ; preds = %198
  %205 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %206 = mul i64 %201, 17
  %207 = add i64 %206, %202
  %208 = getelementptr float, ptr %205, i64 %207
  %209 = load float, ptr %208, align 4
  br label %210

210:                                              ; preds = %204, %198
  %211 = phi float [ %209, %204 ], [ 0.000000e+00, %198 ]
  %212 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %191, 1
  %213 = mul i64 %193, 16
  %214 = add i64 %213, %196
  %215 = getelementptr float, ptr %212, i64 %214
  store float %211, ptr %215, align 4
  %216 = add i64 %196, 1
  br label %195

217:                                              ; preds = %195
  %218 = add i64 %193, 1
  br label %192

219:                                              ; preds = %192
  %220 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %191, 1
  %221 = ptrtoint ptr %220 to i64
  call void @buddy_blis_sgemm_6x16_fringe(i64 %48, i64 %154, i64 %164, i64 %101, i64 %165, i64 %221, i64 0, i64 16, i64 1)
  br label %222

222:                                              ; preds = %241, %219
  %223 = phi i64 [ %242, %241 ], [ 0, %219 ]
  %224 = icmp slt i64 %223, %169
  br i1 %224, label %225, label %243

225:                                              ; preds = %228, %222
  %226 = phi i64 [ %240, %228 ], [ 0, %222 ]
  %227 = icmp slt i64 %226, %171
  br i1 %227, label %228, label %241

228:                                              ; preds = %225
  %229 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %191, 1
  %230 = mul i64 %223, 16
  %231 = add i64 %230, %226
  %232 = getelementptr float, ptr %229, i64 %231
  %233 = load float, ptr %232, align 4
  %234 = add i64 %166, %223
  %235 = add i64 %167, %226
  %236 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %237 = mul i64 %234, 17
  %238 = add i64 %237, %235
  %239 = getelementptr float, ptr %236, i64 %238
  store float %233, ptr %239, align 4
  %240 = add i64 %226, 1
  br label %225

241:                                              ; preds = %225
  %242 = add i64 %223, 1
  br label %222

243:                                              ; preds = %222
  %244 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %191, 0
  call void @free(ptr %244)
  br label %245

245:                                              ; preds = %175, %243
  %246 = add i64 %161, 1
  br label %160

247:                                              ; preds = %160
  %248 = add i64 %158, 1
  br label %157

249:                                              ; preds = %157
  %250 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %116, 0
  call void @free(ptr %250)
  %251 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %63, 0
  call void @free(ptr %251)
  %252 = add i64 %44, 64
  br label %43

253:                                              ; preds = %43
  ret { ptr, ptr, i64, [2 x i64], [2 x i64] } %42
}

define void @_mlir_ciface_chapter5_fringe_dev(ptr %0, ptr %1, ptr %2, ptr %3) {
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
  %29 = call { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter5_fringe_dev(ptr %6, ptr %7, i64 %8, i64 %9, i64 %10, i64 %11, i64 %12, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20, ptr %22, ptr %23, i64 %24, i64 %25, i64 %26, i64 %27, i64 %28)
  store { ptr, ptr, i64, [2 x i64], [2 x i64] } %29, ptr %0, align 8
  ret void
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.umin.i64(i64, i64) #0

attributes #0 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
