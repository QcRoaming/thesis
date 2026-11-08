; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

declare void @free(ptr)

declare ptr @malloc(i64)

declare void @buddy_blis_sgemm_6x16_fringe(i64, i64, i64, i64, i64, i64, i64, i64, i64)

declare void @buddy_blis_sgemm_6x16(i64, i64, i64, i64, i64, i64, i64, i64, i64)

declare void @buddy_microkernel_fringe_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64)

declare void @buddy_microkernel_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64)

define { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter5_direct_blis_6x16(ptr %0, ptr %1, i64 %2, i64 %3, i64 %4, i64 %5, i64 %6, ptr %7, ptr %8, i64 %9, i64 %10, i64 %11, i64 %12, i64 %13, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20) {
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

43:                                               ; preds = %281, %21
  %44 = phi i64 [ %282, %281 ], [ 0, %21 ]
  %45 = icmp slt i64 %44, 256
  br i1 %45, label %46, label %283

46:                                               ; preds = %43
  %47 = sub i64 256, %44
  %48 = call i64 @llvm.umin.i64(i64 %47, i64 32)
  %49 = icmp eq i64 %48, 0
  %50 = sub i64 %48, 1
  %51 = udiv i64 %50, 16
  %52 = add i64 %51, 1
  %53 = select i1 %49, i64 0, i64 %52
  br label %54

54:                                               ; preds = %278, %46
  %55 = phi i64 [ %280, %278 ], [ 0, %46 ]
  %56 = icmp slt i64 %55, 256
  br i1 %56, label %57, label %281

57:                                               ; preds = %54
  %58 = sub i64 256, %55
  %59 = call i64 @llvm.umin.i64(i64 %58, i64 64)
  %60 = call ptr @malloc(i64 add (i64 ptrtoint (ptr getelementptr (float, ptr null, i64 2048) to i64), i64 64))
  %61 = ptrtoint ptr %60 to i64
  %62 = add i64 %61, 63
  %63 = urem i64 %62, 64
  %64 = sub i64 %62, %63
  %65 = inttoptr i64 %64 to ptr
  %66 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } undef, ptr %60, 0
  %67 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %66, ptr %65, 1
  %68 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %67, i64 0, 2
  %69 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %68, i64 2, 3, 0
  %70 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %69, i64 64, 3, 1
  %71 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %70, i64 16, 3, 2
  %72 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %71, i64 1024, 4, 0
  %73 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %72, i64 16, 4, 1
  %74 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %73, i64 1, 4, 2
  br label %75

75:                                               ; preds = %109, %57
  %76 = phi i64 [ %110, %109 ], [ 0, %57 ]
  %77 = icmp slt i64 %76, %53
  br i1 %77, label %78, label %111

78:                                               ; preds = %107, %75
  %79 = phi i64 [ %108, %107 ], [ 0, %75 ]
  %80 = icmp slt i64 %79, 64
  br i1 %80, label %81, label %109

81:                                               ; preds = %98, %78
  %82 = phi i64 [ %106, %98 ], [ 0, %78 ]
  %83 = icmp slt i64 %82, 16
  br i1 %83, label %84, label %107

84:                                               ; preds = %81
  %85 = add i64 %55, %79
  %86 = mul i64 %76, 16
  %87 = add i64 %86, %82
  %88 = add i64 %44, %87
  %89 = icmp ult i64 %85, 256
  %90 = icmp ult i64 %88, 256
  %91 = and i1 %89, %90
  br i1 %91, label %92, label %98

92:                                               ; preds = %84
  %93 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 1
  %94 = mul i64 %85, 256
  %95 = add i64 %94, %88
  %96 = getelementptr float, ptr %93, i64 %95
  %97 = load float, ptr %96, align 4
  br label %98

98:                                               ; preds = %92, %84
  %99 = phi float [ %97, %92 ], [ 0.000000e+00, %84 ]
  %100 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %74, 1
  %101 = mul i64 %76, 1024
  %102 = mul i64 %79, 16
  %103 = add i64 %101, %102
  %104 = add i64 %103, %82
  %105 = getelementptr float, ptr %100, i64 %104
  store float %99, ptr %105, align 4
  %106 = add i64 %82, 1
  br label %81

107:                                              ; preds = %81
  %108 = add i64 %79, 1
  br label %78

109:                                              ; preds = %78
  %110 = add i64 %76, 1
  br label %75

111:                                              ; preds = %75
  %112 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %74, 1
  %113 = ptrtoint ptr %112 to i64
  br label %114

114:                                              ; preds = %275, %111
  %115 = phi i64 [ %277, %275 ], [ 0, %111 ]
  %116 = icmp slt i64 %115, 192
  br i1 %116, label %117, label %278

117:                                              ; preds = %114
  %118 = sub i64 192, %115
  %119 = call i64 @llvm.umin.i64(i64 %118, i64 24)
  %120 = icmp eq i64 %119, 0
  %121 = sub i64 %119, 1
  %122 = udiv i64 %121, 6
  %123 = add i64 %122, 1
  %124 = select i1 %120, i64 0, i64 %123
  %125 = call ptr @malloc(i64 add (i64 ptrtoint (ptr getelementptr (float, ptr null, i64 1536) to i64), i64 64))
  %126 = ptrtoint ptr %125 to i64
  %127 = add i64 %126, 63
  %128 = urem i64 %127, 64
  %129 = sub i64 %127, %128
  %130 = inttoptr i64 %129 to ptr
  %131 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } undef, ptr %125, 0
  %132 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %131, ptr %130, 1
  %133 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %132, i64 0, 2
  %134 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %133, i64 4, 3, 0
  %135 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %134, i64 64, 3, 1
  %136 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %135, i64 6, 3, 2
  %137 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %136, i64 384, 4, 0
  %138 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %137, i64 6, 4, 1
  %139 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %138, i64 1, 4, 2
  br label %140

140:                                              ; preds = %174, %117
  %141 = phi i64 [ %175, %174 ], [ 0, %117 ]
  %142 = icmp slt i64 %141, %124
  br i1 %142, label %143, label %176

143:                                              ; preds = %172, %140
  %144 = phi i64 [ %173, %172 ], [ 0, %140 ]
  %145 = icmp slt i64 %144, 64
  br i1 %145, label %146, label %174

146:                                              ; preds = %163, %143
  %147 = phi i64 [ %171, %163 ], [ 0, %143 ]
  %148 = icmp slt i64 %147, 6
  br i1 %148, label %149, label %172

149:                                              ; preds = %146
  %150 = mul i64 %141, 6
  %151 = add i64 %150, %147
  %152 = add i64 %115, %151
  %153 = add i64 %55, %144
  %154 = icmp ult i64 %152, 192
  %155 = icmp ult i64 %153, 256
  %156 = and i1 %154, %155
  br i1 %156, label %157, label %163

157:                                              ; preds = %149
  %158 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 1
  %159 = mul i64 %152, 256
  %160 = add i64 %159, %153
  %161 = getelementptr float, ptr %158, i64 %160
  %162 = load float, ptr %161, align 4
  br label %163

163:                                              ; preds = %157, %149
  %164 = phi float [ %162, %157 ], [ 0.000000e+00, %149 ]
  %165 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %139, 1
  %166 = mul i64 %141, 384
  %167 = mul i64 %144, 6
  %168 = add i64 %166, %167
  %169 = add i64 %168, %147
  %170 = getelementptr float, ptr %165, i64 %169
  store float %164, ptr %170, align 4
  %171 = add i64 %147, 1
  br label %146

172:                                              ; preds = %146
  %173 = add i64 %144, 1
  br label %143

174:                                              ; preds = %143
  %175 = add i64 %141, 1
  br label %140

176:                                              ; preds = %140
  %177 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %139, 1
  %178 = ptrtoint ptr %177 to i64
  %179 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %180 = ptrtoint ptr %179 to i64
  br label %181

181:                                              ; preds = %273, %176
  %182 = phi i64 [ %274, %273 ], [ 0, %176 ]
  %183 = icmp slt i64 %182, %53
  br i1 %183, label %184, label %275

184:                                              ; preds = %271, %181
  %185 = phi i64 [ %272, %271 ], [ 0, %181 ]
  %186 = icmp slt i64 %185, %124
  br i1 %186, label %187, label %273

187:                                              ; preds = %184
  %188 = mul i64 %185, 384
  %189 = mul i64 %182, 1024
  %190 = mul i64 %185, 6
  %191 = add i64 %115, %190
  %192 = mul i64 %182, 16
  %193 = add i64 %44, %192
  %194 = sub i64 192, %191
  %195 = call i64 @llvm.umin.i64(i64 %194, i64 6)
  %196 = sub i64 256, %193
  %197 = call i64 @llvm.umin.i64(i64 %196, i64 16)
  %198 = icmp eq i64 %195, 6
  %199 = icmp eq i64 %197, 16
  %200 = and i1 %198, %199
  br i1 %200, label %201, label %204

201:                                              ; preds = %187
  %202 = mul i64 %191, 256
  %203 = add i64 %202, %193
  call void @buddy_blis_sgemm_6x16(i64 %59, i64 %178, i64 %188, i64 %113, i64 %189, i64 %180, i64 %203, i64 256, i64 1)
  br label %271

204:                                              ; preds = %187
  %205 = call ptr @malloc(i64 add (i64 ptrtoint (ptr getelementptr (float, ptr null, i64 96) to i64), i64 64))
  %206 = ptrtoint ptr %205 to i64
  %207 = add i64 %206, 63
  %208 = urem i64 %207, 64
  %209 = sub i64 %207, %208
  %210 = inttoptr i64 %209 to ptr
  %211 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %205, 0
  %212 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %211, ptr %210, 1
  %213 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %212, i64 0, 2
  %214 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %213, i64 6, 3, 0
  %215 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %214, i64 16, 3, 1
  %216 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %215, i64 16, 4, 0
  %217 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %216, i64 1, 4, 1
  br label %218

218:                                              ; preds = %243, %204
  %219 = phi i64 [ %244, %243 ], [ 0, %204 ]
  %220 = icmp slt i64 %219, 6
  br i1 %220, label %221, label %245

221:                                              ; preds = %236, %218
  %222 = phi i64 [ %242, %236 ], [ 0, %218 ]
  %223 = icmp slt i64 %222, 16
  br i1 %223, label %224, label %243

224:                                              ; preds = %221
  %225 = icmp ult i64 %219, %195
  %226 = icmp ult i64 %222, %197
  %227 = add i64 %191, %219
  %228 = add i64 %193, %222
  %229 = and i1 %225, %226
  br i1 %229, label %230, label %236

230:                                              ; preds = %224
  %231 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %232 = mul i64 %227, 256
  %233 = add i64 %232, %228
  %234 = getelementptr float, ptr %231, i64 %233
  %235 = load float, ptr %234, align 4
  br label %236

236:                                              ; preds = %230, %224
  %237 = phi float [ %235, %230 ], [ 0.000000e+00, %224 ]
  %238 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %217, 1
  %239 = mul i64 %219, 16
  %240 = add i64 %239, %222
  %241 = getelementptr float, ptr %238, i64 %240
  store float %237, ptr %241, align 4
  %242 = add i64 %222, 1
  br label %221

243:                                              ; preds = %221
  %244 = add i64 %219, 1
  br label %218

245:                                              ; preds = %218
  %246 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %217, 1
  %247 = ptrtoint ptr %246 to i64
  call void @buddy_blis_sgemm_6x16_fringe(i64 %59, i64 %178, i64 %188, i64 %113, i64 %189, i64 %247, i64 0, i64 16, i64 1)
  br label %248

248:                                              ; preds = %267, %245
  %249 = phi i64 [ %268, %267 ], [ 0, %245 ]
  %250 = icmp slt i64 %249, %195
  br i1 %250, label %251, label %269

251:                                              ; preds = %254, %248
  %252 = phi i64 [ %266, %254 ], [ 0, %248 ]
  %253 = icmp slt i64 %252, %197
  br i1 %253, label %254, label %267

254:                                              ; preds = %251
  %255 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %217, 1
  %256 = mul i64 %249, 16
  %257 = add i64 %256, %252
  %258 = getelementptr float, ptr %255, i64 %257
  %259 = load float, ptr %258, align 4
  %260 = add i64 %191, %249
  %261 = add i64 %193, %252
  %262 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %263 = mul i64 %260, 256
  %264 = add i64 %263, %261
  %265 = getelementptr float, ptr %262, i64 %264
  store float %259, ptr %265, align 4
  %266 = add i64 %252, 1
  br label %251

267:                                              ; preds = %251
  %268 = add i64 %249, 1
  br label %248

269:                                              ; preds = %248
  %270 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %217, 0
  call void @free(ptr %270)
  br label %271

271:                                              ; preds = %201, %269
  %272 = add i64 %185, 1
  br label %184

273:                                              ; preds = %184
  %274 = add i64 %182, 1
  br label %181

275:                                              ; preds = %181
  %276 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %139, 0
  call void @free(ptr %276)
  %277 = add i64 %115, 24
  br label %114

278:                                              ; preds = %114
  %279 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %74, 0
  call void @free(ptr %279)
  %280 = add i64 %55, 64
  br label %54

281:                                              ; preds = %54
  %282 = add i64 %44, 32
  br label %43

283:                                              ; preds = %43
  ret { ptr, ptr, i64, [2 x i64], [2 x i64] } %42
}

define void @_mlir_ciface_chapter5_direct_blis_6x16(ptr %0, ptr %1, ptr %2, ptr %3) {
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
  %29 = call { ptr, ptr, i64, [2 x i64], [2 x i64] } @chapter5_direct_blis_6x16(ptr %6, ptr %7, i64 %8, i64 %9, i64 %10, i64 %11, i64 %12, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20, ptr %22, ptr %23, i64 %24, i64 %25, i64 %26, i64 %27, i64 %28)
  store { ptr, ptr, i64, [2 x i64], [2 x i64] } %29, ptr %0, align 8
  ret void
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.umin.i64(i64, i64) #0

attributes #0 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
