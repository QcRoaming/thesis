module {
  llvm.func @free(!llvm.ptr)
  llvm.func @malloc(i64) -> !llvm.ptr
  llvm.func @buddy_blis_sgemm_6x16_fringe(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_blis_sgemm_6x16(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_microkernel_fringe_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_microkernel_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @cgo_f32_m6_n16_k16_pab_v0(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: i64, %arg3: i64, %arg4: i64, %arg5: i64, %arg6: i64, %arg7: !llvm.ptr, %arg8: !llvm.ptr, %arg9: i64, %arg10: i64, %arg11: i64, %arg12: i64, %arg13: i64, %arg14: !llvm.ptr, %arg15: !llvm.ptr, %arg16: i64, %arg17: i64, %arg18: i64, %arg19: i64, %arg20: i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> attributes {llvm.emit_c_interface} {
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
    %28 = llvm.mlir.constant(6 : index) : i64
    %29 = llvm.mlir.constant(0 : index) : i64
    %30 = llvm.mlir.constant(1 : index) : i64
    %31 = llvm.extractvalue %15[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %32 = llvm.extractvalue %15[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %33 = llvm.extractvalue %7[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.br ^bb1(%29 : i64)
  ^bb1(%34: i64):  // 2 preds: ^bb0, ^bb46
    %35 = llvm.icmp "slt" %34, %33 : i64
    llvm.cond_br %35, ^bb2, ^bb47
  ^bb2:  // pred: ^bb1
    %36 = llvm.sub %33, %34 : i64
    %37 = llvm.intr.umin(%36, %27) : (i64, i64) -> i64
    %38 = llvm.mlir.constant(0 : index) : i64
    %39 = llvm.icmp "eq" %37, %38 : i64
    %40 = llvm.mlir.constant(1 : index) : i64
    %41 = llvm.sub %37, %40 : i64
    %42 = llvm.udiv %41, %27 : i64
    %43 = llvm.add %42, %40 : i64
    %44 = llvm.select %39, %38, %43 : i1, i64
    llvm.br ^bb3(%29 : i64)
  ^bb3(%45: i64):  // 2 preds: ^bb2, ^bb45
    %46 = llvm.icmp "slt" %45, %32 : i64
    llvm.cond_br %46, ^bb4, ^bb46
  ^bb4:  // pred: ^bb3
    %47 = llvm.sub %32, %45 : i64
    %48 = llvm.intr.umin(%47, %27) : (i64, i64) -> i64
    %49 = llvm.mlir.constant(1 : index) : i64
    %50 = llvm.mlir.constant(16 : index) : i64
    %51 = llvm.mlir.constant(16 : index) : i64
    %52 = llvm.mlir.constant(1 : index) : i64
    %53 = llvm.mlir.constant(256 : index) : i64
    %54 = llvm.mlir.constant(256 : index) : i64
    %55 = llvm.mlir.zero : !llvm.ptr
    %56 = llvm.getelementptr %55[%54] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %57 = llvm.ptrtoint %56 : !llvm.ptr to i64
    %58 = llvm.mlir.constant(64 : index) : i64
    %59 = llvm.add %57, %58 : i64
    %60 = llvm.call @malloc(%59) : (i64) -> !llvm.ptr
    %61 = llvm.ptrtoint %60 : !llvm.ptr to i64
    %62 = llvm.mlir.constant(1 : index) : i64
    %63 = llvm.sub %58, %62 : i64
    %64 = llvm.add %61, %63 : i64
    %65 = llvm.urem %64, %58 : i64
    %66 = llvm.sub %64, %65 : i64
    %67 = llvm.inttoptr %66 : i64 to !llvm.ptr
    %68 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %69 = llvm.insertvalue %60, %68[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %70 = llvm.insertvalue %67, %69[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %71 = llvm.mlir.constant(0 : index) : i64
    %72 = llvm.insertvalue %71, %70[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %73 = llvm.insertvalue %49, %72[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %74 = llvm.insertvalue %50, %73[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %75 = llvm.insertvalue %51, %74[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %76 = llvm.insertvalue %53, %75[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %77 = llvm.insertvalue %51, %76[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %78 = llvm.insertvalue %52, %77[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.br ^bb5(%29 : i64)
  ^bb5(%79: i64):  // 2 preds: ^bb4, ^bb12
    %80 = llvm.icmp "slt" %79, %44 : i64
    llvm.cond_br %80, ^bb6(%29 : i64), ^bb13
  ^bb6(%81: i64):  // 2 preds: ^bb5, ^bb11
    %82 = llvm.icmp "slt" %81, %27 : i64
    llvm.cond_br %82, ^bb7(%29 : i64), ^bb12
  ^bb7(%83: i64):  // 2 preds: ^bb6, ^bb10
    %84 = llvm.icmp "slt" %83, %27 : i64
    llvm.cond_br %84, ^bb8, ^bb11
  ^bb8:  // pred: ^bb7
    %85 = llvm.add %45, %81 : i64
    %86 = llvm.mul %79, %27 : i64
    %87 = llvm.add %86, %83 : i64
    %88 = llvm.add %34, %87 : i64
    %89 = llvm.icmp "ult" %85, %32 : i64
    %90 = llvm.icmp "ult" %88, %33 : i64
    %91 = llvm.and %89, %90 : i1
    llvm.cond_br %91, ^bb9, ^bb10(%24 : f32)
  ^bb9:  // pred: ^bb8
    %92 = llvm.extractvalue %7[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %93 = llvm.extractvalue %7[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %94 = llvm.mul %85, %93 : i64
    %95 = llvm.add %94, %88 : i64
    %96 = llvm.getelementptr %92[%95] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %97 = llvm.load %96 : !llvm.ptr -> f32
    llvm.br ^bb10(%97 : f32)
  ^bb10(%98: f32):  // 2 preds: ^bb8, ^bb9
    %99 = llvm.extractvalue %78[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %100 = llvm.mlir.constant(256 : index) : i64
    %101 = llvm.mul %79, %100 : i64
    %102 = llvm.mlir.constant(16 : index) : i64
    %103 = llvm.mul %81, %102 : i64
    %104 = llvm.add %101, %103 : i64
    %105 = llvm.add %104, %83 : i64
    %106 = llvm.getelementptr %99[%105] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %98, %106 : f32, !llvm.ptr
    %107 = llvm.add %83, %30 : i64
    llvm.br ^bb7(%107 : i64)
  ^bb11:  // pred: ^bb7
    %108 = llvm.add %81, %30 : i64
    llvm.br ^bb6(%108 : i64)
  ^bb12:  // pred: ^bb6
    %109 = llvm.add %79, %30 : i64
    llvm.br ^bb5(%109 : i64)
  ^bb13:  // pred: ^bb5
    %110 = llvm.extractvalue %78[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %111 = llvm.ptrtoint %110 : !llvm.ptr to i64
    llvm.br ^bb14(%29 : i64)
  ^bb14(%112: i64):  // 2 preds: ^bb13, ^bb44
    %113 = llvm.icmp "slt" %112, %31 : i64
    llvm.cond_br %113, ^bb15, ^bb45
  ^bb15:  // pred: ^bb14
    %114 = llvm.sub %31, %112 : i64
    %115 = llvm.intr.umin(%114, %28) : (i64, i64) -> i64
    %116 = llvm.mlir.constant(0 : index) : i64
    %117 = llvm.icmp "eq" %115, %116 : i64
    %118 = llvm.mlir.constant(1 : index) : i64
    %119 = llvm.sub %115, %118 : i64
    %120 = llvm.udiv %119, %28 : i64
    %121 = llvm.add %120, %118 : i64
    %122 = llvm.select %117, %116, %121 : i1, i64
    %123 = llvm.mlir.constant(1 : index) : i64
    %124 = llvm.mlir.constant(16 : index) : i64
    %125 = llvm.mlir.constant(6 : index) : i64
    %126 = llvm.mlir.constant(1 : index) : i64
    %127 = llvm.mlir.constant(96 : index) : i64
    %128 = llvm.mlir.constant(96 : index) : i64
    %129 = llvm.mlir.zero : !llvm.ptr
    %130 = llvm.getelementptr %129[%128] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %131 = llvm.ptrtoint %130 : !llvm.ptr to i64
    %132 = llvm.mlir.constant(64 : index) : i64
    %133 = llvm.add %131, %132 : i64
    %134 = llvm.call @malloc(%133) : (i64) -> !llvm.ptr
    %135 = llvm.ptrtoint %134 : !llvm.ptr to i64
    %136 = llvm.mlir.constant(1 : index) : i64
    %137 = llvm.sub %132, %136 : i64
    %138 = llvm.add %135, %137 : i64
    %139 = llvm.urem %138, %132 : i64
    %140 = llvm.sub %138, %139 : i64
    %141 = llvm.inttoptr %140 : i64 to !llvm.ptr
    %142 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %143 = llvm.insertvalue %134, %142[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %144 = llvm.insertvalue %141, %143[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %145 = llvm.mlir.constant(0 : index) : i64
    %146 = llvm.insertvalue %145, %144[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %147 = llvm.insertvalue %123, %146[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %148 = llvm.insertvalue %124, %147[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %149 = llvm.insertvalue %125, %148[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %150 = llvm.insertvalue %127, %149[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %151 = llvm.insertvalue %125, %150[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %152 = llvm.insertvalue %126, %151[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.br ^bb16(%29 : i64)
  ^bb16(%153: i64):  // 2 preds: ^bb15, ^bb23
    %154 = llvm.icmp "slt" %153, %122 : i64
    llvm.cond_br %154, ^bb17(%29 : i64), ^bb24
  ^bb17(%155: i64):  // 2 preds: ^bb16, ^bb22
    %156 = llvm.icmp "slt" %155, %27 : i64
    llvm.cond_br %156, ^bb18(%29 : i64), ^bb23
  ^bb18(%157: i64):  // 2 preds: ^bb17, ^bb21
    %158 = llvm.icmp "slt" %157, %28 : i64
    llvm.cond_br %158, ^bb19, ^bb22
  ^bb19:  // pred: ^bb18
    %159 = llvm.mul %153, %28 : i64
    %160 = llvm.add %159, %157 : i64
    %161 = llvm.add %112, %160 : i64
    %162 = llvm.add %45, %155 : i64
    %163 = llvm.icmp "ult" %161, %31 : i64
    %164 = llvm.icmp "ult" %162, %32 : i64
    %165 = llvm.and %163, %164 : i1
    llvm.cond_br %165, ^bb20, ^bb21(%24 : f32)
  ^bb20:  // pred: ^bb19
    %166 = llvm.extractvalue %15[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %167 = llvm.extractvalue %15[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %168 = llvm.mul %161, %167 : i64
    %169 = llvm.add %168, %162 : i64
    %170 = llvm.getelementptr %166[%169] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %171 = llvm.load %170 : !llvm.ptr -> f32
    llvm.br ^bb21(%171 : f32)
  ^bb21(%172: f32):  // 2 preds: ^bb19, ^bb20
    %173 = llvm.extractvalue %152[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %174 = llvm.mlir.constant(96 : index) : i64
    %175 = llvm.mul %153, %174 : i64
    %176 = llvm.mlir.constant(6 : index) : i64
    %177 = llvm.mul %155, %176 : i64
    %178 = llvm.add %175, %177 : i64
    %179 = llvm.add %178, %157 : i64
    %180 = llvm.getelementptr %173[%179] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %172, %180 : f32, !llvm.ptr
    %181 = llvm.add %157, %30 : i64
    llvm.br ^bb18(%181 : i64)
  ^bb22:  // pred: ^bb18
    %182 = llvm.add %155, %30 : i64
    llvm.br ^bb17(%182 : i64)
  ^bb23:  // pred: ^bb17
    %183 = llvm.add %153, %30 : i64
    llvm.br ^bb16(%183 : i64)
  ^bb24:  // pred: ^bb16
    %184 = llvm.extractvalue %152[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %185 = llvm.ptrtoint %184 : !llvm.ptr to i64
    %186 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %187 = llvm.ptrtoint %186 : !llvm.ptr to i64
    llvm.br ^bb25(%29 : i64)
  ^bb25(%188: i64):  // 2 preds: ^bb24, ^bb43
    %189 = llvm.icmp "slt" %188, %44 : i64
    llvm.cond_br %189, ^bb26(%29 : i64), ^bb44
  ^bb26(%190: i64):  // 2 preds: ^bb25, ^bb42
    %191 = llvm.icmp "slt" %190, %122 : i64
    llvm.cond_br %191, ^bb27, ^bb43
  ^bb27:  // pred: ^bb26
    %192 = llvm.mul %190, %26 : i64
    %193 = llvm.mul %188, %25 : i64
    %194 = llvm.mul %190, %28 : i64
    %195 = llvm.add %112, %194 : i64
    %196 = llvm.mul %188, %27 : i64
    %197 = llvm.add %34, %196 : i64
    %198 = llvm.sub %31, %195 : i64
    %199 = llvm.intr.umin(%198, %28) : (i64, i64) -> i64
    %200 = llvm.sub %33, %197 : i64
    %201 = llvm.intr.umin(%200, %27) : (i64, i64) -> i64
    %202 = llvm.icmp "eq" %199, %28 : i64
    %203 = llvm.icmp "eq" %201, %27 : i64
    %204 = llvm.and %202, %203 : i1
    llvm.cond_br %204, ^bb28, ^bb29
  ^bb28:  // pred: ^bb27
    %205 = llvm.mul %195, %33 : i64
    %206 = llvm.add %205, %197 : i64
    llvm.call @buddy_blis_sgemm_6x16(%48, %185, %192, %111, %193, %187, %206, %33, %30) : (i64, i64, i64, i64, i64, i64, i64, i64, i64) -> ()
    llvm.br ^bb42
  ^bb29:  // pred: ^bb27
    %207 = llvm.mlir.constant(6 : index) : i64
    %208 = llvm.mlir.constant(16 : index) : i64
    %209 = llvm.mlir.constant(1 : index) : i64
    %210 = llvm.mlir.constant(96 : index) : i64
    %211 = llvm.mlir.zero : !llvm.ptr
    %212 = llvm.getelementptr %211[%210] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %213 = llvm.ptrtoint %212 : !llvm.ptr to i64
    %214 = llvm.mlir.constant(64 : index) : i64
    %215 = llvm.add %213, %214 : i64
    %216 = llvm.call @malloc(%215) : (i64) -> !llvm.ptr
    %217 = llvm.ptrtoint %216 : !llvm.ptr to i64
    %218 = llvm.mlir.constant(1 : index) : i64
    %219 = llvm.sub %214, %218 : i64
    %220 = llvm.add %217, %219 : i64
    %221 = llvm.urem %220, %214 : i64
    %222 = llvm.sub %220, %221 : i64
    %223 = llvm.inttoptr %222 : i64 to !llvm.ptr
    %224 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %225 = llvm.insertvalue %216, %224[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %226 = llvm.insertvalue %223, %225[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %227 = llvm.mlir.constant(0 : index) : i64
    %228 = llvm.insertvalue %227, %226[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %229 = llvm.insertvalue %207, %228[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %230 = llvm.insertvalue %208, %229[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %231 = llvm.insertvalue %208, %230[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %232 = llvm.insertvalue %209, %231[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.br ^bb30(%29 : i64)
  ^bb30(%233: i64):  // 2 preds: ^bb29, ^bb35
    %234 = llvm.icmp "slt" %233, %28 : i64
    llvm.cond_br %234, ^bb31(%29 : i64), ^bb36
  ^bb31(%235: i64):  // 2 preds: ^bb30, ^bb34
    %236 = llvm.icmp "slt" %235, %27 : i64
    llvm.cond_br %236, ^bb32, ^bb35
  ^bb32:  // pred: ^bb31
    %237 = llvm.icmp "ult" %233, %199 : i64
    %238 = llvm.icmp "ult" %235, %201 : i64
    %239 = llvm.add %195, %233 : i64
    %240 = llvm.add %197, %235 : i64
    %241 = llvm.and %237, %238 : i1
    llvm.cond_br %241, ^bb33, ^bb34(%24 : f32)
  ^bb33:  // pred: ^bb32
    %242 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %243 = llvm.extractvalue %23[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %244 = llvm.mul %239, %243 : i64
    %245 = llvm.add %244, %240 : i64
    %246 = llvm.getelementptr %242[%245] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %247 = llvm.load %246 : !llvm.ptr -> f32
    llvm.br ^bb34(%247 : f32)
  ^bb34(%248: f32):  // 2 preds: ^bb32, ^bb33
    %249 = llvm.extractvalue %232[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %250 = llvm.mlir.constant(16 : index) : i64
    %251 = llvm.mul %233, %250 : i64
    %252 = llvm.add %251, %235 : i64
    %253 = llvm.getelementptr %249[%252] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %248, %253 : f32, !llvm.ptr
    %254 = llvm.add %235, %30 : i64
    llvm.br ^bb31(%254 : i64)
  ^bb35:  // pred: ^bb31
    %255 = llvm.add %233, %30 : i64
    llvm.br ^bb30(%255 : i64)
  ^bb36:  // pred: ^bb30
    %256 = llvm.extractvalue %232[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %257 = llvm.ptrtoint %256 : !llvm.ptr to i64
    llvm.call @buddy_blis_sgemm_6x16_fringe(%48, %185, %192, %111, %193, %257, %29, %27, %30) : (i64, i64, i64, i64, i64, i64, i64, i64, i64) -> ()
    llvm.br ^bb37(%29 : i64)
  ^bb37(%258: i64):  // 2 preds: ^bb36, ^bb40
    %259 = llvm.icmp "slt" %258, %199 : i64
    llvm.cond_br %259, ^bb38(%29 : i64), ^bb41
  ^bb38(%260: i64):  // 2 preds: ^bb37, ^bb39
    %261 = llvm.icmp "slt" %260, %201 : i64
    llvm.cond_br %261, ^bb39, ^bb40
  ^bb39:  // pred: ^bb38
    %262 = llvm.extractvalue %232[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %263 = llvm.mlir.constant(16 : index) : i64
    %264 = llvm.mul %258, %263 : i64
    %265 = llvm.add %264, %260 : i64
    %266 = llvm.getelementptr %262[%265] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %267 = llvm.load %266 : !llvm.ptr -> f32
    %268 = llvm.add %195, %258 : i64
    %269 = llvm.add %197, %260 : i64
    %270 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %271 = llvm.extractvalue %23[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %272 = llvm.mul %268, %271 : i64
    %273 = llvm.add %272, %269 : i64
    %274 = llvm.getelementptr %270[%273] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %267, %274 : f32, !llvm.ptr
    %275 = llvm.add %260, %30 : i64
    llvm.br ^bb38(%275 : i64)
  ^bb40:  // pred: ^bb38
    %276 = llvm.add %258, %30 : i64
    llvm.br ^bb37(%276 : i64)
  ^bb41:  // pred: ^bb37
    %277 = llvm.extractvalue %232[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.call @free(%277) : (!llvm.ptr) -> ()
    llvm.br ^bb42
  ^bb42:  // 2 preds: ^bb28, ^bb41
    %278 = llvm.add %190, %30 : i64
    llvm.br ^bb26(%278 : i64)
  ^bb43:  // pred: ^bb26
    %279 = llvm.add %188, %30 : i64
    llvm.br ^bb25(%279 : i64)
  ^bb44:  // pred: ^bb25
    %280 = llvm.extractvalue %152[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.call @free(%280) : (!llvm.ptr) -> ()
    %281 = llvm.add %112, %28 : i64
    llvm.br ^bb14(%281 : i64)
  ^bb45:  // pred: ^bb14
    %282 = llvm.extractvalue %78[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.call @free(%282) : (!llvm.ptr) -> ()
    %283 = llvm.add %45, %27 : i64
    llvm.br ^bb3(%283 : i64)
  ^bb46:  // pred: ^bb3
    %284 = llvm.add %34, %27 : i64
    llvm.br ^bb1(%284 : i64)
  ^bb47:  // pred: ^bb1
    llvm.return %23 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
  }
  llvm.func @_mlir_ciface_cgo_f32_m6_n16_k16_pab_v0(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: !llvm.ptr, %arg3: !llvm.ptr) attributes {llvm.emit_c_interface} {
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
    %24 = llvm.call @cgo_f32_m6_n16_k16_pab_v0(%1, %2, %3, %4, %5, %6, %7, %9, %10, %11, %12, %13, %14, %15, %17, %18, %19, %20, %21, %22, %23) : (!llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    llvm.store %24, %arg0 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>, !llvm.ptr
    llvm.return
  }
}

