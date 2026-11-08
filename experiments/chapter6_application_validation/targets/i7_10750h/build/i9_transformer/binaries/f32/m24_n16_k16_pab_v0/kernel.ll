; ModuleID = 'LLVMDialectModule'
source_filename = "LLVMDialectModule"

declare void @free(ptr)

declare ptr @malloc(i64)

declare void @buddy_blis_sgemm_6x16_fringe(i64, i64, i64, i64, i64, i64, i64, i64, i64)

declare void @buddy_blis_sgemm_6x16(i64, i64, i64, i64, i64, i64, i64, i64, i64)

declare void @buddy_microkernel_fringe_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64)

declare void @buddy_microkernel_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64)

define { ptr, ptr, i64, [2 x i64], [2 x i64] } @cgo_f32_m24_n16_k16_pab_v0(ptr %0, ptr %1, i64 %2, i64 %3, i64 %4, i64 %5, i64 %6, ptr %7, ptr %8, i64 %9, i64 %10, i64 %11, i64 %12, i64 %13, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20) {
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
  %43 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 0
  %44 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 3, 1
  %45 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 3, 1
  br label %46

46:                                               ; preds = %288, %21
  %47 = phi i64 [ %289, %288 ], [ 0, %21 ]
  %48 = icmp slt i64 %47, %45
  br i1 %48, label %49, label %290

49:                                               ; preds = %46
  %50 = sub i64 %45, %47
  %51 = call i64 @llvm.umin.i64(i64 %50, i64 16)
  %52 = icmp eq i64 %51, 0
  %53 = sub i64 %51, 1
  %54 = udiv i64 %53, 16
  %55 = add i64 %54, 1
  %56 = select i1 %52, i64 0, i64 %55
  br label %57

57:                                               ; preds = %285, %49
  %58 = phi i64 [ %287, %285 ], [ 0, %49 ]
  %59 = icmp slt i64 %58, %44
  br i1 %59, label %60, label %288

60:                                               ; preds = %57
  %61 = sub i64 %44, %58
  %62 = call i64 @llvm.umin.i64(i64 %61, i64 16)
  %63 = call ptr @malloc(i64 add (i64 ptrtoint (ptr getelementptr (float, ptr null, i64 256) to i64), i64 64))
  %64 = ptrtoint ptr %63 to i64
  %65 = add i64 %64, 63
  %66 = urem i64 %65, 64
  %67 = sub i64 %65, %66
  %68 = inttoptr i64 %67 to ptr
  %69 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } undef, ptr %63, 0
  %70 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %69, ptr %68, 1
  %71 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %70, i64 0, 2
  %72 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %71, i64 1, 3, 0
  %73 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %72, i64 16, 3, 1
  %74 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %73, i64 16, 3, 2
  %75 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %74, i64 256, 4, 0
  %76 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %75, i64 16, 4, 1
  %77 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %76, i64 1, 4, 2
  br label %78

78:                                               ; preds = %113, %60
  %79 = phi i64 [ %114, %113 ], [ 0, %60 ]
  %80 = icmp slt i64 %79, %56
  br i1 %80, label %81, label %115

81:                                               ; preds = %111, %78
  %82 = phi i64 [ %112, %111 ], [ 0, %78 ]
  %83 = icmp slt i64 %82, 16
  br i1 %83, label %84, label %113

84:                                               ; preds = %102, %81
  %85 = phi i64 [ %110, %102 ], [ 0, %81 ]
  %86 = icmp slt i64 %85, 16
  br i1 %86, label %87, label %111

87:                                               ; preds = %84
  %88 = add i64 %58, %82
  %89 = mul i64 %79, 16
  %90 = add i64 %89, %85
  %91 = add i64 %47, %90
  %92 = icmp ult i64 %88, %44
  %93 = icmp ult i64 %91, %45
  %94 = and i1 %92, %93
  br i1 %94, label %95, label %102

95:                                               ; preds = %87
  %96 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 1
  %97 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %28, 4, 0
  %98 = mul i64 %88, %97
  %99 = add i64 %98, %91
  %100 = getelementptr float, ptr %96, i64 %99
  %101 = load float, ptr %100, align 4
  br label %102

102:                                              ; preds = %95, %87
  %103 = phi float [ %101, %95 ], [ 0.000000e+00, %87 ]
  %104 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %77, 1
  %105 = mul i64 %79, 256
  %106 = mul i64 %82, 16
  %107 = add i64 %105, %106
  %108 = add i64 %107, %85
  %109 = getelementptr float, ptr %104, i64 %108
  store float %103, ptr %109, align 4
  %110 = add i64 %85, 1
  br label %84

111:                                              ; preds = %84
  %112 = add i64 %82, 1
  br label %81

113:                                              ; preds = %81
  %114 = add i64 %79, 1
  br label %78

115:                                              ; preds = %78
  %116 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %77, 1
  %117 = ptrtoint ptr %116 to i64
  br label %118

118:                                              ; preds = %282, %115
  %119 = phi i64 [ %284, %282 ], [ 0, %115 ]
  %120 = icmp slt i64 %119, %43
  br i1 %120, label %121, label %285

121:                                              ; preds = %118
  %122 = sub i64 %43, %119
  %123 = call i64 @llvm.umin.i64(i64 %122, i64 24)
  %124 = icmp eq i64 %123, 0
  %125 = sub i64 %123, 1
  %126 = udiv i64 %125, 6
  %127 = add i64 %126, 1
  %128 = select i1 %124, i64 0, i64 %127
  %129 = call ptr @malloc(i64 add (i64 ptrtoint (ptr getelementptr (float, ptr null, i64 384) to i64), i64 64))
  %130 = ptrtoint ptr %129 to i64
  %131 = add i64 %130, 63
  %132 = urem i64 %131, 64
  %133 = sub i64 %131, %132
  %134 = inttoptr i64 %133 to ptr
  %135 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } undef, ptr %129, 0
  %136 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %135, ptr %134, 1
  %137 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %136, i64 0, 2
  %138 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %137, i64 4, 3, 0
  %139 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %138, i64 16, 3, 1
  %140 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %139, i64 6, 3, 2
  %141 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %140, i64 96, 4, 0
  %142 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %141, i64 6, 4, 1
  %143 = insertvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %142, i64 1, 4, 2
  br label %144

144:                                              ; preds = %179, %121
  %145 = phi i64 [ %180, %179 ], [ 0, %121 ]
  %146 = icmp slt i64 %145, %128
  br i1 %146, label %147, label %181

147:                                              ; preds = %177, %144
  %148 = phi i64 [ %178, %177 ], [ 0, %144 ]
  %149 = icmp slt i64 %148, 16
  br i1 %149, label %150, label %179

150:                                              ; preds = %168, %147
  %151 = phi i64 [ %176, %168 ], [ 0, %147 ]
  %152 = icmp slt i64 %151, 6
  br i1 %152, label %153, label %177

153:                                              ; preds = %150
  %154 = mul i64 %145, 6
  %155 = add i64 %154, %151
  %156 = add i64 %119, %155
  %157 = add i64 %58, %148
  %158 = icmp ult i64 %156, %43
  %159 = icmp ult i64 %157, %44
  %160 = and i1 %158, %159
  br i1 %160, label %161, label %168

161:                                              ; preds = %153
  %162 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 1
  %163 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %35, 4, 0
  %164 = mul i64 %156, %163
  %165 = add i64 %164, %157
  %166 = getelementptr float, ptr %162, i64 %165
  %167 = load float, ptr %166, align 4
  br label %168

168:                                              ; preds = %161, %153
  %169 = phi float [ %167, %161 ], [ 0.000000e+00, %153 ]
  %170 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %143, 1
  %171 = mul i64 %145, 96
  %172 = mul i64 %148, 6
  %173 = add i64 %171, %172
  %174 = add i64 %173, %151
  %175 = getelementptr float, ptr %170, i64 %174
  store float %169, ptr %175, align 4
  %176 = add i64 %151, 1
  br label %150

177:                                              ; preds = %150
  %178 = add i64 %148, 1
  br label %147

179:                                              ; preds = %147
  %180 = add i64 %145, 1
  br label %144

181:                                              ; preds = %144
  %182 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %143, 1
  %183 = ptrtoint ptr %182 to i64
  %184 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %185 = ptrtoint ptr %184 to i64
  br label %186

186:                                              ; preds = %280, %181
  %187 = phi i64 [ %281, %280 ], [ 0, %181 ]
  %188 = icmp slt i64 %187, %56
  br i1 %188, label %189, label %282

189:                                              ; preds = %278, %186
  %190 = phi i64 [ %279, %278 ], [ 0, %186 ]
  %191 = icmp slt i64 %190, %128
  br i1 %191, label %192, label %280

192:                                              ; preds = %189
  %193 = mul i64 %190, 96
  %194 = mul i64 %187, 256
  %195 = mul i64 %190, 6
  %196 = add i64 %119, %195
  %197 = mul i64 %187, 16
  %198 = add i64 %47, %197
  %199 = sub i64 %43, %196
  %200 = call i64 @llvm.umin.i64(i64 %199, i64 6)
  %201 = sub i64 %45, %198
  %202 = call i64 @llvm.umin.i64(i64 %201, i64 16)
  %203 = icmp eq i64 %200, 6
  %204 = icmp eq i64 %202, 16
  %205 = and i1 %203, %204
  br i1 %205, label %206, label %209

206:                                              ; preds = %192
  %207 = mul i64 %196, %45
  %208 = add i64 %207, %198
  call void @buddy_blis_sgemm_6x16(i64 %62, i64 %183, i64 %193, i64 %117, i64 %194, i64 %185, i64 %208, i64 %45, i64 1)
  br label %278

209:                                              ; preds = %192
  %210 = call ptr @malloc(i64 add (i64 ptrtoint (ptr getelementptr (float, ptr null, i64 96) to i64), i64 64))
  %211 = ptrtoint ptr %210 to i64
  %212 = add i64 %211, 63
  %213 = urem i64 %212, 64
  %214 = sub i64 %212, %213
  %215 = inttoptr i64 %214 to ptr
  %216 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } undef, ptr %210, 0
  %217 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %216, ptr %215, 1
  %218 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %217, i64 0, 2
  %219 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %218, i64 6, 3, 0
  %220 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %219, i64 16, 3, 1
  %221 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %220, i64 16, 4, 0
  %222 = insertvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %221, i64 1, 4, 1
  br label %223

223:                                              ; preds = %249, %209
  %224 = phi i64 [ %250, %249 ], [ 0, %209 ]
  %225 = icmp slt i64 %224, 6
  br i1 %225, label %226, label %251

226:                                              ; preds = %242, %223
  %227 = phi i64 [ %248, %242 ], [ 0, %223 ]
  %228 = icmp slt i64 %227, 16
  br i1 %228, label %229, label %249

229:                                              ; preds = %226
  %230 = icmp ult i64 %224, %200
  %231 = icmp ult i64 %227, %202
  %232 = add i64 %196, %224
  %233 = add i64 %198, %227
  %234 = and i1 %230, %231
  br i1 %234, label %235, label %242

235:                                              ; preds = %229
  %236 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %237 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 0
  %238 = mul i64 %232, %237
  %239 = add i64 %238, %233
  %240 = getelementptr float, ptr %236, i64 %239
  %241 = load float, ptr %240, align 4
  br label %242

242:                                              ; preds = %235, %229
  %243 = phi float [ %241, %235 ], [ 0.000000e+00, %229 ]
  %244 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %222, 1
  %245 = mul i64 %224, 16
  %246 = add i64 %245, %227
  %247 = getelementptr float, ptr %244, i64 %246
  store float %243, ptr %247, align 4
  %248 = add i64 %227, 1
  br label %226

249:                                              ; preds = %226
  %250 = add i64 %224, 1
  br label %223

251:                                              ; preds = %223
  %252 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %222, 1
  %253 = ptrtoint ptr %252 to i64
  call void @buddy_blis_sgemm_6x16_fringe(i64 %62, i64 %183, i64 %193, i64 %117, i64 %194, i64 %253, i64 0, i64 16, i64 1)
  br label %254

254:                                              ; preds = %274, %251
  %255 = phi i64 [ %275, %274 ], [ 0, %251 ]
  %256 = icmp slt i64 %255, %200
  br i1 %256, label %257, label %276

257:                                              ; preds = %260, %254
  %258 = phi i64 [ %273, %260 ], [ 0, %254 ]
  %259 = icmp slt i64 %258, %202
  br i1 %259, label %260, label %274

260:                                              ; preds = %257
  %261 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %222, 1
  %262 = mul i64 %255, 16
  %263 = add i64 %262, %258
  %264 = getelementptr float, ptr %261, i64 %263
  %265 = load float, ptr %264, align 4
  %266 = add i64 %196, %255
  %267 = add i64 %198, %258
  %268 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 1
  %269 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %42, 4, 0
  %270 = mul i64 %266, %269
  %271 = add i64 %270, %267
  %272 = getelementptr float, ptr %268, i64 %271
  store float %265, ptr %272, align 4
  %273 = add i64 %258, 1
  br label %257

274:                                              ; preds = %257
  %275 = add i64 %255, 1
  br label %254

276:                                              ; preds = %254
  %277 = extractvalue { ptr, ptr, i64, [2 x i64], [2 x i64] } %222, 0
  call void @free(ptr %277)
  br label %278

278:                                              ; preds = %206, %276
  %279 = add i64 %190, 1
  br label %189

280:                                              ; preds = %189
  %281 = add i64 %187, 1
  br label %186

282:                                              ; preds = %186
  %283 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %143, 0
  call void @free(ptr %283)
  %284 = add i64 %119, 24
  br label %118

285:                                              ; preds = %118
  %286 = extractvalue { ptr, ptr, i64, [3 x i64], [3 x i64] } %77, 0
  call void @free(ptr %286)
  %287 = add i64 %58, 16
  br label %57

288:                                              ; preds = %57
  %289 = add i64 %47, 16
  br label %46

290:                                              ; preds = %46
  ret { ptr, ptr, i64, [2 x i64], [2 x i64] } %42
}

define void @_mlir_ciface_cgo_f32_m24_n16_k16_pab_v0(ptr %0, ptr %1, ptr %2, ptr %3) {
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
  %29 = call { ptr, ptr, i64, [2 x i64], [2 x i64] } @cgo_f32_m24_n16_k16_pab_v0(ptr %6, ptr %7, i64 %8, i64 %9, i64 %10, i64 %11, i64 %12, ptr %14, ptr %15, i64 %16, i64 %17, i64 %18, i64 %19, i64 %20, ptr %22, ptr %23, i64 %24, i64 %25, i64 %26, i64 %27, i64 %28)
  store { ptr, ptr, i64, [2 x i64], [2 x i64] } %29, ptr %0, align 8
  ret void
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare i64 @llvm.umin.i64(i64, i64) #0

attributes #0 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }

!llvm.module.flags = !{!0}

!0 = !{i32 2, !"Debug Info Version", i32 3}
