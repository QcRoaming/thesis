module {
  llvm.func @free(!llvm.ptr)
  llvm.func @malloc(i64) -> !llvm.ptr
  llvm.func @buddy_blis_sgemm_6x16_fringe(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_blis_sgemm_6x16(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_microkernel_fringe_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_microkernel_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @integrated_anchor_192x256x256_f32_m48_n32_k64_pab_v1(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: i64, %arg3: i64, %arg4: i64, %arg5: i64, %arg6: i64, %arg7: !llvm.ptr, %arg8: !llvm.ptr, %arg9: i64, %arg10: i64, %arg11: i64, %arg12: i64, %arg13: i64, %arg14: !llvm.ptr, %arg15: !llvm.ptr, %arg16: i64, %arg17: i64, %arg18: i64, %arg19: i64, %arg20: i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> attributes {llvm.emit_c_interface} {
    %0 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %1 = llvm.insertvalue %arg7, %0[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %2 = llvm.insertvalue %arg8, %1[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %3 = llvm.insertvalue %arg9, %2[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %4 = llvm.insertvalue %arg10, %3[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %5 = llvm.insertvalue %arg12, %4[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %6 = llvm.insertvalue %arg11, %5[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %7 = llvm.insertvalue %arg13, %6[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %8 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %9 = llvm.insertvalue %arg0, %8[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %10 = llvm.insertvalue %arg1, %9[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %11 = llvm.insertvalue %arg2, %10[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %12 = llvm.insertvalue %arg3, %11[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %13 = llvm.insertvalue %arg5, %12[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %14 = llvm.insertvalue %arg4, %13[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %15 = llvm.insertvalue %arg6, %14[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %16 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %17 = llvm.insertvalue %arg14, %16[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %18 = llvm.insertvalue %arg15, %17[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %19 = llvm.insertvalue %arg16, %18[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %20 = llvm.insertvalue %arg17, %19[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %21 = llvm.insertvalue %arg19, %20[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %22 = llvm.insertvalue %arg18, %21[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %23 = llvm.insertvalue %arg20, %22[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %24 = llvm.mlir.constant(0.000000e+00 : f32) : f32
    %25 = llvm.mlir.constant(1024 : index) : i64
    %26 = llvm.mlir.constant(384 : index) : i64
    %27 = llvm.mlir.constant(16 : index) : i64
    %28 = llvm.mlir.constant(6 : index) : i64
    %29 = llvm.mlir.constant(64 : index) : i64
    %30 = llvm.mlir.constant(32 : index) : i64
    %31 = llvm.mlir.constant(48 : index) : i64
    %32 = llvm.mlir.constant(0 : index) : i64
    %33 = llvm.mlir.constant(1 : index) : i64
    %34 = llvm.extractvalue %15[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %35 = llvm.extractvalue %15[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %36 = llvm.extractvalue %7[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.br ^bb1(%32 : i64)
  ^bb1(%37: i64):  // 2 preds: ^bb0, ^bb46
    %38 = llvm.icmp "slt" %37, %36 : i64
    llvm.cond_br %38, ^bb2, ^bb47
  ^bb2:  // pred: ^bb1
    %39 = llvm.sub %36, %37 : i64
    %40 = llvm.intr.umin(%39, %30) : (i64, i64) -> i64
    %41 = llvm.mlir.constant(0 : index) : i64
    %42 = llvm.icmp "eq" %40, %41 : i64
    %43 = llvm.mlir.constant(1 : index) : i64
    %44 = llvm.sub %40, %43 : i64
    %45 = llvm.udiv %44, %27 : i64
    %46 = llvm.add %45, %43 : i64
    %47 = llvm.select %42, %41, %46 : i1, i64
    llvm.br ^bb3(%32 : i64)
  ^bb3(%48: i64):  // 2 preds: ^bb2, ^bb45
    %49 = llvm.icmp "slt" %48, %35 : i64
    llvm.cond_br %49, ^bb4, ^bb46
  ^bb4:  // pred: ^bb3
    %50 = llvm.sub %35, %48 : i64
    %51 = llvm.intr.umin(%50, %29) : (i64, i64) -> i64
    %52 = llvm.mlir.constant(2 : index) : i64
    %53 = llvm.mlir.constant(64 : index) : i64
    %54 = llvm.mlir.constant(16 : index) : i64
    %55 = llvm.mlir.constant(1 : index) : i64
    %56 = llvm.mlir.constant(1024 : index) : i64
    %57 = llvm.mlir.constant(2048 : index) : i64
    %58 = llvm.mlir.zero : !llvm.ptr
    %59 = llvm.getelementptr %58[%57] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %60 = llvm.ptrtoint %59 : !llvm.ptr to i64
    %61 = llvm.mlir.constant(64 : index) : i64
    %62 = llvm.add %60, %61 : i64
    %63 = llvm.call @malloc(%62) : (i64) -> !llvm.ptr
    %64 = llvm.ptrtoint %63 : !llvm.ptr to i64
    %65 = llvm.mlir.constant(1 : index) : i64
    %66 = llvm.sub %61, %65 : i64
    %67 = llvm.add %64, %66 : i64
    %68 = llvm.urem %67, %61 : i64
    %69 = llvm.sub %67, %68 : i64
    %70 = llvm.inttoptr %69 : i64 to !llvm.ptr
    %71 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %72 = llvm.insertvalue %63, %71[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %73 = llvm.insertvalue %70, %72[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %74 = llvm.mlir.constant(0 : index) : i64
    %75 = llvm.insertvalue %74, %73[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %76 = llvm.insertvalue %52, %75[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %77 = llvm.insertvalue %53, %76[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %78 = llvm.insertvalue %54, %77[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %79 = llvm.insertvalue %56, %78[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %80 = llvm.insertvalue %54, %79[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %81 = llvm.insertvalue %55, %80[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.br ^bb5(%32 : i64)
  ^bb5(%82: i64):  // 2 preds: ^bb4, ^bb12
    %83 = llvm.icmp "slt" %82, %47 : i64
    llvm.cond_br %83, ^bb6(%32 : i64), ^bb13
  ^bb6(%84: i64):  // 2 preds: ^bb5, ^bb11
    %85 = llvm.icmp "slt" %84, %29 : i64
    llvm.cond_br %85, ^bb7(%32 : i64), ^bb12
  ^bb7(%86: i64):  // 2 preds: ^bb6, ^bb10
    %87 = llvm.icmp "slt" %86, %27 : i64
    llvm.cond_br %87, ^bb8, ^bb11
  ^bb8:  // pred: ^bb7
    %88 = llvm.add %48, %84 : i64
    %89 = llvm.mul %82, %27 : i64
    %90 = llvm.add %89, %86 : i64
    %91 = llvm.add %37, %90 : i64
    %92 = llvm.icmp "ult" %88, %35 : i64
    %93 = llvm.icmp "ult" %91, %36 : i64
    %94 = llvm.and %92, %93 : i1
    llvm.cond_br %94, ^bb9, ^bb10(%24 : f32)
  ^bb9:  // pred: ^bb8
    %95 = llvm.extractvalue %7[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %96 = llvm.extractvalue %7[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %97 = llvm.mul %88, %96 : i64
    %98 = llvm.add %97, %91 : i64
    %99 = llvm.getelementptr %95[%98] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %100 = llvm.load %99 : !llvm.ptr -> f32
    llvm.br ^bb10(%100 : f32)
  ^bb10(%101: f32):  // 2 preds: ^bb8, ^bb9
    %102 = llvm.extractvalue %81[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %103 = llvm.mlir.constant(1024 : index) : i64
    %104 = llvm.mul %82, %103 : i64
    %105 = llvm.mlir.constant(16 : index) : i64
    %106 = llvm.mul %84, %105 : i64
    %107 = llvm.add %104, %106 : i64
    %108 = llvm.add %107, %86 : i64
    %109 = llvm.getelementptr %102[%108] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %101, %109 : f32, !llvm.ptr
    %110 = llvm.add %86, %33 : i64
    llvm.br ^bb7(%110 : i64)
  ^bb11:  // pred: ^bb7
    %111 = llvm.add %84, %33 : i64
    llvm.br ^bb6(%111 : i64)
  ^bb12:  // pred: ^bb6
    %112 = llvm.add %82, %33 : i64
    llvm.br ^bb5(%112 : i64)
  ^bb13:  // pred: ^bb5
    %113 = llvm.extractvalue %81[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %114 = llvm.ptrtoint %113 : !llvm.ptr to i64
    llvm.br ^bb14(%32 : i64)
  ^bb14(%115: i64):  // 2 preds: ^bb13, ^bb44
    %116 = llvm.icmp "slt" %115, %34 : i64
    llvm.cond_br %116, ^bb15, ^bb45
  ^bb15:  // pred: ^bb14
    %117 = llvm.sub %34, %115 : i64
    %118 = llvm.intr.umin(%117, %31) : (i64, i64) -> i64
    %119 = llvm.mlir.constant(0 : index) : i64
    %120 = llvm.icmp "eq" %118, %119 : i64
    %121 = llvm.mlir.constant(1 : index) : i64
    %122 = llvm.sub %118, %121 : i64
    %123 = llvm.udiv %122, %28 : i64
    %124 = llvm.add %123, %121 : i64
    %125 = llvm.select %120, %119, %124 : i1, i64
    %126 = llvm.mlir.constant(8 : index) : i64
    %127 = llvm.mlir.constant(64 : index) : i64
    %128 = llvm.mlir.constant(6 : index) : i64
    %129 = llvm.mlir.constant(1 : index) : i64
    %130 = llvm.mlir.constant(384 : index) : i64
    %131 = llvm.mlir.constant(3072 : index) : i64
    %132 = llvm.mlir.zero : !llvm.ptr
    %133 = llvm.getelementptr %132[%131] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %134 = llvm.ptrtoint %133 : !llvm.ptr to i64
    %135 = llvm.mlir.constant(64 : index) : i64
    %136 = llvm.add %134, %135 : i64
    %137 = llvm.call @malloc(%136) : (i64) -> !llvm.ptr
    %138 = llvm.ptrtoint %137 : !llvm.ptr to i64
    %139 = llvm.mlir.constant(1 : index) : i64
    %140 = llvm.sub %135, %139 : i64
    %141 = llvm.add %138, %140 : i64
    %142 = llvm.urem %141, %135 : i64
    %143 = llvm.sub %141, %142 : i64
    %144 = llvm.inttoptr %143 : i64 to !llvm.ptr
    %145 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %146 = llvm.insertvalue %137, %145[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %147 = llvm.insertvalue %144, %146[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %148 = llvm.mlir.constant(0 : index) : i64
    %149 = llvm.insertvalue %148, %147[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %150 = llvm.insertvalue %126, %149[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %151 = llvm.insertvalue %127, %150[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %152 = llvm.insertvalue %128, %151[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %153 = llvm.insertvalue %130, %152[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %154 = llvm.insertvalue %128, %153[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %155 = llvm.insertvalue %129, %154[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.br ^bb16(%32 : i64)
  ^bb16(%156: i64):  // 2 preds: ^bb15, ^bb23
    %157 = llvm.icmp "slt" %156, %125 : i64
    llvm.cond_br %157, ^bb17(%32 : i64), ^bb24
  ^bb17(%158: i64):  // 2 preds: ^bb16, ^bb22
    %159 = llvm.icmp "slt" %158, %29 : i64
    llvm.cond_br %159, ^bb18(%32 : i64), ^bb23
  ^bb18(%160: i64):  // 2 preds: ^bb17, ^bb21
    %161 = llvm.icmp "slt" %160, %28 : i64
    llvm.cond_br %161, ^bb19, ^bb22
  ^bb19:  // pred: ^bb18
    %162 = llvm.mul %156, %28 : i64
    %163 = llvm.add %162, %160 : i64
    %164 = llvm.add %115, %163 : i64
    %165 = llvm.add %48, %158 : i64
    %166 = llvm.icmp "ult" %164, %34 : i64
    %167 = llvm.icmp "ult" %165, %35 : i64
    %168 = llvm.and %166, %167 : i1
    llvm.cond_br %168, ^bb20, ^bb21(%24 : f32)
  ^bb20:  // pred: ^bb19
    %169 = llvm.extractvalue %15[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %170 = llvm.extractvalue %15[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %171 = llvm.mul %164, %170 : i64
    %172 = llvm.add %171, %165 : i64
    %173 = llvm.getelementptr %169[%172] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %174 = llvm.load %173 : !llvm.ptr -> f32
    llvm.br ^bb21(%174 : f32)
  ^bb21(%175: f32):  // 2 preds: ^bb19, ^bb20
    %176 = llvm.extractvalue %155[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %177 = llvm.mlir.constant(384 : index) : i64
    %178 = llvm.mul %156, %177 : i64
    %179 = llvm.mlir.constant(6 : index) : i64
    %180 = llvm.mul %158, %179 : i64
    %181 = llvm.add %178, %180 : i64
    %182 = llvm.add %181, %160 : i64
    %183 = llvm.getelementptr %176[%182] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %175, %183 : f32, !llvm.ptr
    %184 = llvm.add %160, %33 : i64
    llvm.br ^bb18(%184 : i64)
  ^bb22:  // pred: ^bb18
    %185 = llvm.add %158, %33 : i64
    llvm.br ^bb17(%185 : i64)
  ^bb23:  // pred: ^bb17
    %186 = llvm.add %156, %33 : i64
    llvm.br ^bb16(%186 : i64)
  ^bb24:  // pred: ^bb16
    %187 = llvm.extractvalue %155[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %188 = llvm.ptrtoint %187 : !llvm.ptr to i64
    %189 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %190 = llvm.ptrtoint %189 : !llvm.ptr to i64
    llvm.br ^bb25(%32 : i64)
  ^bb25(%191: i64):  // 2 preds: ^bb24, ^bb43
    %192 = llvm.icmp "slt" %191, %47 : i64
    llvm.cond_br %192, ^bb26(%32 : i64), ^bb44
  ^bb26(%193: i64):  // 2 preds: ^bb25, ^bb42
    %194 = llvm.icmp "slt" %193, %125 : i64
    llvm.cond_br %194, ^bb27, ^bb43
  ^bb27:  // pred: ^bb26
    %195 = llvm.mul %193, %26 : i64
    %196 = llvm.mul %191, %25 : i64
    %197 = llvm.mul %193, %28 : i64
    %198 = llvm.add %115, %197 : i64
    %199 = llvm.mul %191, %27 : i64
    %200 = llvm.add %37, %199 : i64
    %201 = llvm.sub %34, %198 : i64
    %202 = llvm.intr.umin(%201, %28) : (i64, i64) -> i64
    %203 = llvm.sub %36, %200 : i64
    %204 = llvm.intr.umin(%203, %27) : (i64, i64) -> i64
    %205 = llvm.icmp "eq" %202, %28 : i64
    %206 = llvm.icmp "eq" %204, %27 : i64
    %207 = llvm.and %205, %206 : i1
    llvm.cond_br %207, ^bb28, ^bb29
  ^bb28:  // pred: ^bb27
    %208 = llvm.mul %198, %36 : i64
    %209 = llvm.add %208, %200 : i64
    llvm.call @buddy_blis_sgemm_6x16(%51, %188, %195, %114, %196, %190, %209, %36, %33) : (i64, i64, i64, i64, i64, i64, i64, i64, i64) -> ()
    llvm.br ^bb42
  ^bb29:  // pred: ^bb27
    %210 = llvm.mlir.constant(6 : index) : i64
    %211 = llvm.mlir.constant(16 : index) : i64
    %212 = llvm.mlir.constant(1 : index) : i64
    %213 = llvm.mlir.constant(96 : index) : i64
    %214 = llvm.mlir.zero : !llvm.ptr
    %215 = llvm.getelementptr %214[%213] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %216 = llvm.ptrtoint %215 : !llvm.ptr to i64
    %217 = llvm.mlir.constant(64 : index) : i64
    %218 = llvm.add %216, %217 : i64
    %219 = llvm.call @malloc(%218) : (i64) -> !llvm.ptr
    %220 = llvm.ptrtoint %219 : !llvm.ptr to i64
    %221 = llvm.mlir.constant(1 : index) : i64
    %222 = llvm.sub %217, %221 : i64
    %223 = llvm.add %220, %222 : i64
    %224 = llvm.urem %223, %217 : i64
    %225 = llvm.sub %223, %224 : i64
    %226 = llvm.inttoptr %225 : i64 to !llvm.ptr
    %227 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %228 = llvm.insertvalue %219, %227[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %229 = llvm.insertvalue %226, %228[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %230 = llvm.mlir.constant(0 : index) : i64
    %231 = llvm.insertvalue %230, %229[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %232 = llvm.insertvalue %210, %231[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %233 = llvm.insertvalue %211, %232[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %234 = llvm.insertvalue %211, %233[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %235 = llvm.insertvalue %212, %234[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.br ^bb30(%32 : i64)
  ^bb30(%236: i64):  // 2 preds: ^bb29, ^bb35
    %237 = llvm.icmp "slt" %236, %28 : i64
    llvm.cond_br %237, ^bb31(%32 : i64), ^bb36
  ^bb31(%238: i64):  // 2 preds: ^bb30, ^bb34
    %239 = llvm.icmp "slt" %238, %27 : i64
    llvm.cond_br %239, ^bb32, ^bb35
  ^bb32:  // pred: ^bb31
    %240 = llvm.icmp "ult" %236, %202 : i64
    %241 = llvm.icmp "ult" %238, %204 : i64
    %242 = llvm.add %198, %236 : i64
    %243 = llvm.add %200, %238 : i64
    %244 = llvm.and %240, %241 : i1
    llvm.cond_br %244, ^bb33, ^bb34(%24 : f32)
  ^bb33:  // pred: ^bb32
    %245 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %246 = llvm.extractvalue %23[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %247 = llvm.mul %242, %246 : i64
    %248 = llvm.add %247, %243 : i64
    %249 = llvm.getelementptr %245[%248] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %250 = llvm.load %249 : !llvm.ptr -> f32
    llvm.br ^bb34(%250 : f32)
  ^bb34(%251: f32):  // 2 preds: ^bb32, ^bb33
    %252 = llvm.extractvalue %235[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %253 = llvm.mlir.constant(16 : index) : i64
    %254 = llvm.mul %236, %253 : i64
    %255 = llvm.add %254, %238 : i64
    %256 = llvm.getelementptr %252[%255] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %251, %256 : f32, !llvm.ptr
    %257 = llvm.add %238, %33 : i64
    llvm.br ^bb31(%257 : i64)
  ^bb35:  // pred: ^bb31
    %258 = llvm.add %236, %33 : i64
    llvm.br ^bb30(%258 : i64)
  ^bb36:  // pred: ^bb30
    %259 = llvm.extractvalue %235[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %260 = llvm.ptrtoint %259 : !llvm.ptr to i64
    llvm.call @buddy_blis_sgemm_6x16_fringe(%51, %188, %195, %114, %196, %260, %32, %27, %33) : (i64, i64, i64, i64, i64, i64, i64, i64, i64) -> ()
    llvm.br ^bb37(%32 : i64)
  ^bb37(%261: i64):  // 2 preds: ^bb36, ^bb40
    %262 = llvm.icmp "slt" %261, %202 : i64
    llvm.cond_br %262, ^bb38(%32 : i64), ^bb41
  ^bb38(%263: i64):  // 2 preds: ^bb37, ^bb39
    %264 = llvm.icmp "slt" %263, %204 : i64
    llvm.cond_br %264, ^bb39, ^bb40
  ^bb39:  // pred: ^bb38
    %265 = llvm.extractvalue %235[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %266 = llvm.mlir.constant(16 : index) : i64
    %267 = llvm.mul %261, %266 : i64
    %268 = llvm.add %267, %263 : i64
    %269 = llvm.getelementptr %265[%268] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %270 = llvm.load %269 : !llvm.ptr -> f32
    %271 = llvm.add %198, %261 : i64
    %272 = llvm.add %200, %263 : i64
    %273 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %274 = llvm.extractvalue %23[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %275 = llvm.mul %271, %274 : i64
    %276 = llvm.add %275, %272 : i64
    %277 = llvm.getelementptr %273[%276] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %270, %277 : f32, !llvm.ptr
    %278 = llvm.add %263, %33 : i64
    llvm.br ^bb38(%278 : i64)
  ^bb40:  // pred: ^bb38
    %279 = llvm.add %261, %33 : i64
    llvm.br ^bb37(%279 : i64)
  ^bb41:  // pred: ^bb37
    %280 = llvm.extractvalue %235[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.call @free(%280) : (!llvm.ptr) -> ()
    llvm.br ^bb42
  ^bb42:  // 2 preds: ^bb28, ^bb41
    %281 = llvm.add %193, %33 : i64
    llvm.br ^bb26(%281 : i64)
  ^bb43:  // pred: ^bb26
    %282 = llvm.add %191, %33 : i64
    llvm.br ^bb25(%282 : i64)
  ^bb44:  // pred: ^bb25
    %283 = llvm.extractvalue %155[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.call @free(%283) : (!llvm.ptr) -> ()
    %284 = llvm.add %115, %31 : i64
    llvm.br ^bb14(%284 : i64)
  ^bb45:  // pred: ^bb14
    %285 = llvm.extractvalue %81[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.call @free(%285) : (!llvm.ptr) -> ()
    %286 = llvm.add %48, %29 : i64
    llvm.br ^bb3(%286 : i64)
  ^bb46:  // pred: ^bb3
    %287 = llvm.add %37, %30 : i64
    llvm.br ^bb1(%287 : i64)
  ^bb47:  // pred: ^bb1
    llvm.return %23 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
  }
  llvm.func @_mlir_ciface_integrated_anchor_192x256x256_f32_m48_n32_k64_pab_v1(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: !llvm.ptr, %arg3: !llvm.ptr) attributes {llvm.emit_c_interface} {
    %0 = llvm.load %arg1 : !llvm.ptr -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %1 = llvm.extractvalue %0[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %2 = llvm.extractvalue %0[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %3 = llvm.extractvalue %0[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %4 = llvm.extractvalue %0[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %5 = llvm.extractvalue %0[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %6 = llvm.extractvalue %0[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %7 = llvm.extractvalue %0[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %8 = llvm.load %arg2 : !llvm.ptr -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %9 = llvm.extractvalue %8[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %10 = llvm.extractvalue %8[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %11 = llvm.extractvalue %8[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %12 = llvm.extractvalue %8[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %13 = llvm.extractvalue %8[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %14 = llvm.extractvalue %8[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %15 = llvm.extractvalue %8[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %16 = llvm.load %arg3 : !llvm.ptr -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %17 = llvm.extractvalue %16[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %18 = llvm.extractvalue %16[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %19 = llvm.extractvalue %16[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %20 = llvm.extractvalue %16[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %21 = llvm.extractvalue %16[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %22 = llvm.extractvalue %16[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %23 = llvm.extractvalue %16[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %24 = llvm.call @integrated_anchor_192x256x256_f32_m48_n32_k64_pab_v1(%1, %2, %3, %4, %5, %6, %7, %9, %10, %11, %12, %13, %14, %15, %17, %18, %19, %20, %21, %22, %23) : (!llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    llvm.store %24, %arg0 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>, !llvm.ptr
    llvm.return
  }
}

