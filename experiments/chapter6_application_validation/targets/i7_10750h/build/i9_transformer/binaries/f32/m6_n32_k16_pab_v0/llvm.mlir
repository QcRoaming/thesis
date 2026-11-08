module {
  llvm.func @free(!llvm.ptr)
  llvm.func @malloc(i64) -> !llvm.ptr
  llvm.func @buddy_blis_sgemm_6x16_fringe(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_blis_sgemm_6x16(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_microkernel_fringe_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_microkernel_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @cgo_f32_m6_n32_k16_pab_v0(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: i64, %arg3: i64, %arg4: i64, %arg5: i64, %arg6: i64, %arg7: !llvm.ptr, %arg8: !llvm.ptr, %arg9: i64, %arg10: i64, %arg11: i64, %arg12: i64, %arg13: i64, %arg14: !llvm.ptr, %arg15: !llvm.ptr, %arg16: i64, %arg17: i64, %arg18: i64, %arg19: i64, %arg20: i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> attributes {llvm.emit_c_interface} {
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
    %25 = llvm.mlir.constant(256 : index) : i64
    %26 = llvm.mlir.constant(96 : index) : i64
    %27 = llvm.mlir.constant(16 : index) : i64
    %28 = llvm.mlir.constant(32 : index) : i64
    %29 = llvm.mlir.constant(6 : index) : i64
    %30 = llvm.mlir.constant(0 : index) : i64
    %31 = llvm.mlir.constant(1 : index) : i64
    %32 = llvm.extractvalue %15[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %33 = llvm.extractvalue %15[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %34 = llvm.extractvalue %7[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.br ^bb1(%30 : i64)
  ^bb1(%35: i64):  // 2 preds: ^bb0, ^bb46
    %36 = llvm.icmp "slt" %35, %34 : i64
    llvm.cond_br %36, ^bb2, ^bb47
  ^bb2:  // pred: ^bb1
    %37 = llvm.sub %34, %35 : i64
    %38 = llvm.intr.umin(%37, %28) : (i64, i64) -> i64
    %39 = llvm.mlir.constant(0 : index) : i64
    %40 = llvm.icmp "eq" %38, %39 : i64
    %41 = llvm.mlir.constant(1 : index) : i64
    %42 = llvm.sub %38, %41 : i64
    %43 = llvm.udiv %42, %27 : i64
    %44 = llvm.add %43, %41 : i64
    %45 = llvm.select %40, %39, %44 : i1, i64
    llvm.br ^bb3(%30 : i64)
  ^bb3(%46: i64):  // 2 preds: ^bb2, ^bb45
    %47 = llvm.icmp "slt" %46, %33 : i64
    llvm.cond_br %47, ^bb4, ^bb46
  ^bb4:  // pred: ^bb3
    %48 = llvm.sub %33, %46 : i64
    %49 = llvm.intr.umin(%48, %27) : (i64, i64) -> i64
    %50 = llvm.mlir.constant(2 : index) : i64
    %51 = llvm.mlir.constant(16 : index) : i64
    %52 = llvm.mlir.constant(16 : index) : i64
    %53 = llvm.mlir.constant(1 : index) : i64
    %54 = llvm.mlir.constant(256 : index) : i64
    %55 = llvm.mlir.constant(512 : index) : i64
    %56 = llvm.mlir.zero : !llvm.ptr
    %57 = llvm.getelementptr %56[%55] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %58 = llvm.ptrtoint %57 : !llvm.ptr to i64
    %59 = llvm.mlir.constant(64 : index) : i64
    %60 = llvm.add %58, %59 : i64
    %61 = llvm.call @malloc(%60) : (i64) -> !llvm.ptr
    %62 = llvm.ptrtoint %61 : !llvm.ptr to i64
    %63 = llvm.mlir.constant(1 : index) : i64
    %64 = llvm.sub %59, %63 : i64
    %65 = llvm.add %62, %64 : i64
    %66 = llvm.urem %65, %59 : i64
    %67 = llvm.sub %65, %66 : i64
    %68 = llvm.inttoptr %67 : i64 to !llvm.ptr
    %69 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %70 = llvm.insertvalue %61, %69[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %71 = llvm.insertvalue %68, %70[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %72 = llvm.mlir.constant(0 : index) : i64
    %73 = llvm.insertvalue %72, %71[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %74 = llvm.insertvalue %50, %73[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %75 = llvm.insertvalue %51, %74[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %76 = llvm.insertvalue %52, %75[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %77 = llvm.insertvalue %54, %76[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %78 = llvm.insertvalue %52, %77[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %79 = llvm.insertvalue %53, %78[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.br ^bb5(%30 : i64)
  ^bb5(%80: i64):  // 2 preds: ^bb4, ^bb12
    %81 = llvm.icmp "slt" %80, %45 : i64
    llvm.cond_br %81, ^bb6(%30 : i64), ^bb13
  ^bb6(%82: i64):  // 2 preds: ^bb5, ^bb11
    %83 = llvm.icmp "slt" %82, %27 : i64
    llvm.cond_br %83, ^bb7(%30 : i64), ^bb12
  ^bb7(%84: i64):  // 2 preds: ^bb6, ^bb10
    %85 = llvm.icmp "slt" %84, %27 : i64
    llvm.cond_br %85, ^bb8, ^bb11
  ^bb8:  // pred: ^bb7
    %86 = llvm.add %46, %82 : i64
    %87 = llvm.mul %80, %27 : i64
    %88 = llvm.add %87, %84 : i64
    %89 = llvm.add %35, %88 : i64
    %90 = llvm.icmp "ult" %86, %33 : i64
    %91 = llvm.icmp "ult" %89, %34 : i64
    %92 = llvm.and %90, %91 : i1
    llvm.cond_br %92, ^bb9, ^bb10(%24 : f32)
  ^bb9:  // pred: ^bb8
    %93 = llvm.extractvalue %7[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %94 = llvm.extractvalue %7[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %95 = llvm.mul %86, %94 : i64
    %96 = llvm.add %95, %89 : i64
    %97 = llvm.getelementptr %93[%96] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %98 = llvm.load %97 : !llvm.ptr -> f32
    llvm.br ^bb10(%98 : f32)
  ^bb10(%99: f32):  // 2 preds: ^bb8, ^bb9
    %100 = llvm.extractvalue %79[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %101 = llvm.mlir.constant(256 : index) : i64
    %102 = llvm.mul %80, %101 : i64
    %103 = llvm.mlir.constant(16 : index) : i64
    %104 = llvm.mul %82, %103 : i64
    %105 = llvm.add %102, %104 : i64
    %106 = llvm.add %105, %84 : i64
    %107 = llvm.getelementptr %100[%106] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %99, %107 : f32, !llvm.ptr
    %108 = llvm.add %84, %31 : i64
    llvm.br ^bb7(%108 : i64)
  ^bb11:  // pred: ^bb7
    %109 = llvm.add %82, %31 : i64
    llvm.br ^bb6(%109 : i64)
  ^bb12:  // pred: ^bb6
    %110 = llvm.add %80, %31 : i64
    llvm.br ^bb5(%110 : i64)
  ^bb13:  // pred: ^bb5
    %111 = llvm.extractvalue %79[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %112 = llvm.ptrtoint %111 : !llvm.ptr to i64
    llvm.br ^bb14(%30 : i64)
  ^bb14(%113: i64):  // 2 preds: ^bb13, ^bb44
    %114 = llvm.icmp "slt" %113, %32 : i64
    llvm.cond_br %114, ^bb15, ^bb45
  ^bb15:  // pred: ^bb14
    %115 = llvm.sub %32, %113 : i64
    %116 = llvm.intr.umin(%115, %29) : (i64, i64) -> i64
    %117 = llvm.mlir.constant(0 : index) : i64
    %118 = llvm.icmp "eq" %116, %117 : i64
    %119 = llvm.mlir.constant(1 : index) : i64
    %120 = llvm.sub %116, %119 : i64
    %121 = llvm.udiv %120, %29 : i64
    %122 = llvm.add %121, %119 : i64
    %123 = llvm.select %118, %117, %122 : i1, i64
    %124 = llvm.mlir.constant(1 : index) : i64
    %125 = llvm.mlir.constant(16 : index) : i64
    %126 = llvm.mlir.constant(6 : index) : i64
    %127 = llvm.mlir.constant(1 : index) : i64
    %128 = llvm.mlir.constant(96 : index) : i64
    %129 = llvm.mlir.constant(96 : index) : i64
    %130 = llvm.mlir.zero : !llvm.ptr
    %131 = llvm.getelementptr %130[%129] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %132 = llvm.ptrtoint %131 : !llvm.ptr to i64
    %133 = llvm.mlir.constant(64 : index) : i64
    %134 = llvm.add %132, %133 : i64
    %135 = llvm.call @malloc(%134) : (i64) -> !llvm.ptr
    %136 = llvm.ptrtoint %135 : !llvm.ptr to i64
    %137 = llvm.mlir.constant(1 : index) : i64
    %138 = llvm.sub %133, %137 : i64
    %139 = llvm.add %136, %138 : i64
    %140 = llvm.urem %139, %133 : i64
    %141 = llvm.sub %139, %140 : i64
    %142 = llvm.inttoptr %141 : i64 to !llvm.ptr
    %143 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %144 = llvm.insertvalue %135, %143[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %145 = llvm.insertvalue %142, %144[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %146 = llvm.mlir.constant(0 : index) : i64
    %147 = llvm.insertvalue %146, %145[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %148 = llvm.insertvalue %124, %147[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %149 = llvm.insertvalue %125, %148[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %150 = llvm.insertvalue %126, %149[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %151 = llvm.insertvalue %128, %150[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %152 = llvm.insertvalue %126, %151[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %153 = llvm.insertvalue %127, %152[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.br ^bb16(%30 : i64)
  ^bb16(%154: i64):  // 2 preds: ^bb15, ^bb23
    %155 = llvm.icmp "slt" %154, %123 : i64
    llvm.cond_br %155, ^bb17(%30 : i64), ^bb24
  ^bb17(%156: i64):  // 2 preds: ^bb16, ^bb22
    %157 = llvm.icmp "slt" %156, %27 : i64
    llvm.cond_br %157, ^bb18(%30 : i64), ^bb23
  ^bb18(%158: i64):  // 2 preds: ^bb17, ^bb21
    %159 = llvm.icmp "slt" %158, %29 : i64
    llvm.cond_br %159, ^bb19, ^bb22
  ^bb19:  // pred: ^bb18
    %160 = llvm.mul %154, %29 : i64
    %161 = llvm.add %160, %158 : i64
    %162 = llvm.add %113, %161 : i64
    %163 = llvm.add %46, %156 : i64
    %164 = llvm.icmp "ult" %162, %32 : i64
    %165 = llvm.icmp "ult" %163, %33 : i64
    %166 = llvm.and %164, %165 : i1
    llvm.cond_br %166, ^bb20, ^bb21(%24 : f32)
  ^bb20:  // pred: ^bb19
    %167 = llvm.extractvalue %15[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %168 = llvm.extractvalue %15[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %169 = llvm.mul %162, %168 : i64
    %170 = llvm.add %169, %163 : i64
    %171 = llvm.getelementptr %167[%170] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %172 = llvm.load %171 : !llvm.ptr -> f32
    llvm.br ^bb21(%172 : f32)
  ^bb21(%173: f32):  // 2 preds: ^bb19, ^bb20
    %174 = llvm.extractvalue %153[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %175 = llvm.mlir.constant(96 : index) : i64
    %176 = llvm.mul %154, %175 : i64
    %177 = llvm.mlir.constant(6 : index) : i64
    %178 = llvm.mul %156, %177 : i64
    %179 = llvm.add %176, %178 : i64
    %180 = llvm.add %179, %158 : i64
    %181 = llvm.getelementptr %174[%180] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %173, %181 : f32, !llvm.ptr
    %182 = llvm.add %158, %31 : i64
    llvm.br ^bb18(%182 : i64)
  ^bb22:  // pred: ^bb18
    %183 = llvm.add %156, %31 : i64
    llvm.br ^bb17(%183 : i64)
  ^bb23:  // pred: ^bb17
    %184 = llvm.add %154, %31 : i64
    llvm.br ^bb16(%184 : i64)
  ^bb24:  // pred: ^bb16
    %185 = llvm.extractvalue %153[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %186 = llvm.ptrtoint %185 : !llvm.ptr to i64
    %187 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %188 = llvm.ptrtoint %187 : !llvm.ptr to i64
    llvm.br ^bb25(%30 : i64)
  ^bb25(%189: i64):  // 2 preds: ^bb24, ^bb43
    %190 = llvm.icmp "slt" %189, %45 : i64
    llvm.cond_br %190, ^bb26(%30 : i64), ^bb44
  ^bb26(%191: i64):  // 2 preds: ^bb25, ^bb42
    %192 = llvm.icmp "slt" %191, %123 : i64
    llvm.cond_br %192, ^bb27, ^bb43
  ^bb27:  // pred: ^bb26
    %193 = llvm.mul %191, %26 : i64
    %194 = llvm.mul %189, %25 : i64
    %195 = llvm.mul %191, %29 : i64
    %196 = llvm.add %113, %195 : i64
    %197 = llvm.mul %189, %27 : i64
    %198 = llvm.add %35, %197 : i64
    %199 = llvm.sub %32, %196 : i64
    %200 = llvm.intr.umin(%199, %29) : (i64, i64) -> i64
    %201 = llvm.sub %34, %198 : i64
    %202 = llvm.intr.umin(%201, %27) : (i64, i64) -> i64
    %203 = llvm.icmp "eq" %200, %29 : i64
    %204 = llvm.icmp "eq" %202, %27 : i64
    %205 = llvm.and %203, %204 : i1
    llvm.cond_br %205, ^bb28, ^bb29
  ^bb28:  // pred: ^bb27
    %206 = llvm.mul %196, %34 : i64
    %207 = llvm.add %206, %198 : i64
    llvm.call @buddy_blis_sgemm_6x16(%49, %186, %193, %112, %194, %188, %207, %34, %31) : (i64, i64, i64, i64, i64, i64, i64, i64, i64) -> ()
    llvm.br ^bb42
  ^bb29:  // pred: ^bb27
    %208 = llvm.mlir.constant(6 : index) : i64
    %209 = llvm.mlir.constant(16 : index) : i64
    %210 = llvm.mlir.constant(1 : index) : i64
    %211 = llvm.mlir.constant(96 : index) : i64
    %212 = llvm.mlir.zero : !llvm.ptr
    %213 = llvm.getelementptr %212[%211] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %214 = llvm.ptrtoint %213 : !llvm.ptr to i64
    %215 = llvm.mlir.constant(64 : index) : i64
    %216 = llvm.add %214, %215 : i64
    %217 = llvm.call @malloc(%216) : (i64) -> !llvm.ptr
    %218 = llvm.ptrtoint %217 : !llvm.ptr to i64
    %219 = llvm.mlir.constant(1 : index) : i64
    %220 = llvm.sub %215, %219 : i64
    %221 = llvm.add %218, %220 : i64
    %222 = llvm.urem %221, %215 : i64
    %223 = llvm.sub %221, %222 : i64
    %224 = llvm.inttoptr %223 : i64 to !llvm.ptr
    %225 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %226 = llvm.insertvalue %217, %225[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %227 = llvm.insertvalue %224, %226[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %228 = llvm.mlir.constant(0 : index) : i64
    %229 = llvm.insertvalue %228, %227[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %230 = llvm.insertvalue %208, %229[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %231 = llvm.insertvalue %209, %230[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %232 = llvm.insertvalue %209, %231[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %233 = llvm.insertvalue %210, %232[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.br ^bb30(%30 : i64)
  ^bb30(%234: i64):  // 2 preds: ^bb29, ^bb35
    %235 = llvm.icmp "slt" %234, %29 : i64
    llvm.cond_br %235, ^bb31(%30 : i64), ^bb36
  ^bb31(%236: i64):  // 2 preds: ^bb30, ^bb34
    %237 = llvm.icmp "slt" %236, %27 : i64
    llvm.cond_br %237, ^bb32, ^bb35
  ^bb32:  // pred: ^bb31
    %238 = llvm.icmp "ult" %234, %200 : i64
    %239 = llvm.icmp "ult" %236, %202 : i64
    %240 = llvm.add %196, %234 : i64
    %241 = llvm.add %198, %236 : i64
    %242 = llvm.and %238, %239 : i1
    llvm.cond_br %242, ^bb33, ^bb34(%24 : f32)
  ^bb33:  // pred: ^bb32
    %243 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %244 = llvm.extractvalue %23[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %245 = llvm.mul %240, %244 : i64
    %246 = llvm.add %245, %241 : i64
    %247 = llvm.getelementptr %243[%246] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %248 = llvm.load %247 : !llvm.ptr -> f32
    llvm.br ^bb34(%248 : f32)
  ^bb34(%249: f32):  // 2 preds: ^bb32, ^bb33
    %250 = llvm.extractvalue %233[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %251 = llvm.mlir.constant(16 : index) : i64
    %252 = llvm.mul %234, %251 : i64
    %253 = llvm.add %252, %236 : i64
    %254 = llvm.getelementptr %250[%253] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %249, %254 : f32, !llvm.ptr
    %255 = llvm.add %236, %31 : i64
    llvm.br ^bb31(%255 : i64)
  ^bb35:  // pred: ^bb31
    %256 = llvm.add %234, %31 : i64
    llvm.br ^bb30(%256 : i64)
  ^bb36:  // pred: ^bb30
    %257 = llvm.extractvalue %233[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %258 = llvm.ptrtoint %257 : !llvm.ptr to i64
    llvm.call @buddy_blis_sgemm_6x16_fringe(%49, %186, %193, %112, %194, %258, %30, %27, %31) : (i64, i64, i64, i64, i64, i64, i64, i64, i64) -> ()
    llvm.br ^bb37(%30 : i64)
  ^bb37(%259: i64):  // 2 preds: ^bb36, ^bb40
    %260 = llvm.icmp "slt" %259, %200 : i64
    llvm.cond_br %260, ^bb38(%30 : i64), ^bb41
  ^bb38(%261: i64):  // 2 preds: ^bb37, ^bb39
    %262 = llvm.icmp "slt" %261, %202 : i64
    llvm.cond_br %262, ^bb39, ^bb40
  ^bb39:  // pred: ^bb38
    %263 = llvm.extractvalue %233[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %264 = llvm.mlir.constant(16 : index) : i64
    %265 = llvm.mul %259, %264 : i64
    %266 = llvm.add %265, %261 : i64
    %267 = llvm.getelementptr %263[%266] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %268 = llvm.load %267 : !llvm.ptr -> f32
    %269 = llvm.add %196, %259 : i64
    %270 = llvm.add %198, %261 : i64
    %271 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %272 = llvm.extractvalue %23[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %273 = llvm.mul %269, %272 : i64
    %274 = llvm.add %273, %270 : i64
    %275 = llvm.getelementptr %271[%274] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %268, %275 : f32, !llvm.ptr
    %276 = llvm.add %261, %31 : i64
    llvm.br ^bb38(%276 : i64)
  ^bb40:  // pred: ^bb38
    %277 = llvm.add %259, %31 : i64
    llvm.br ^bb37(%277 : i64)
  ^bb41:  // pred: ^bb37
    %278 = llvm.extractvalue %233[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.call @free(%278) : (!llvm.ptr) -> ()
    llvm.br ^bb42
  ^bb42:  // 2 preds: ^bb28, ^bb41
    %279 = llvm.add %191, %31 : i64
    llvm.br ^bb26(%279 : i64)
  ^bb43:  // pred: ^bb26
    %280 = llvm.add %189, %31 : i64
    llvm.br ^bb25(%280 : i64)
  ^bb44:  // pred: ^bb25
    %281 = llvm.extractvalue %153[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.call @free(%281) : (!llvm.ptr) -> ()
    %282 = llvm.add %113, %29 : i64
    llvm.br ^bb14(%282 : i64)
  ^bb45:  // pred: ^bb14
    %283 = llvm.extractvalue %79[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.call @free(%283) : (!llvm.ptr) -> ()
    %284 = llvm.add %46, %27 : i64
    llvm.br ^bb3(%284 : i64)
  ^bb46:  // pred: ^bb3
    %285 = llvm.add %35, %28 : i64
    llvm.br ^bb1(%285 : i64)
  ^bb47:  // pred: ^bb1
    llvm.return %23 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
  }
  llvm.func @_mlir_ciface_cgo_f32_m6_n32_k16_pab_v0(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: !llvm.ptr, %arg3: !llvm.ptr) attributes {llvm.emit_c_interface} {
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
    %24 = llvm.call @cgo_f32_m6_n32_k16_pab_v0(%1, %2, %3, %4, %5, %6, %7, %9, %10, %11, %12, %13, %14, %15, %17, %18, %19, %20, %21, %22, %23) : (!llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    llvm.store %24, %arg0 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>, !llvm.ptr
    llvm.return
  }
}

