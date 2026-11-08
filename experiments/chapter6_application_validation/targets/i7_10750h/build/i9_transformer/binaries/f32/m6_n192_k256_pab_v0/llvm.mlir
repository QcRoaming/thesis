module {
  llvm.func @free(!llvm.ptr)
  llvm.func @malloc(i64) -> !llvm.ptr
  llvm.func @buddy_blis_sgemm_6x16_fringe(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_blis_sgemm_6x16(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_microkernel_fringe_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_microkernel_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @cgo_f32_m6_n192_k256_pab_v0(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: i64, %arg3: i64, %arg4: i64, %arg5: i64, %arg6: i64, %arg7: !llvm.ptr, %arg8: !llvm.ptr, %arg9: i64, %arg10: i64, %arg11: i64, %arg12: i64, %arg13: i64, %arg14: !llvm.ptr, %arg15: !llvm.ptr, %arg16: i64, %arg17: i64, %arg18: i64, %arg19: i64, %arg20: i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> attributes {llvm.emit_c_interface} {
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
    %25 = llvm.mlir.constant(4096 : index) : i64
    %26 = llvm.mlir.constant(1536 : index) : i64
    %27 = llvm.mlir.constant(16 : index) : i64
    %28 = llvm.mlir.constant(256 : index) : i64
    %29 = llvm.mlir.constant(192 : index) : i64
    %30 = llvm.mlir.constant(6 : index) : i64
    %31 = llvm.mlir.constant(0 : index) : i64
    %32 = llvm.mlir.constant(1 : index) : i64
    %33 = llvm.extractvalue %15[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %34 = llvm.extractvalue %15[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %35 = llvm.extractvalue %7[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.br ^bb1(%31 : i64)
  ^bb1(%36: i64):  // 2 preds: ^bb0, ^bb46
    %37 = llvm.icmp "slt" %36, %35 : i64
    llvm.cond_br %37, ^bb2, ^bb47
  ^bb2:  // pred: ^bb1
    %38 = llvm.sub %35, %36 : i64
    %39 = llvm.intr.umin(%38, %29) : (i64, i64) -> i64
    %40 = llvm.mlir.constant(0 : index) : i64
    %41 = llvm.icmp "eq" %39, %40 : i64
    %42 = llvm.mlir.constant(1 : index) : i64
    %43 = llvm.sub %39, %42 : i64
    %44 = llvm.udiv %43, %27 : i64
    %45 = llvm.add %44, %42 : i64
    %46 = llvm.select %41, %40, %45 : i1, i64
    llvm.br ^bb3(%31 : i64)
  ^bb3(%47: i64):  // 2 preds: ^bb2, ^bb45
    %48 = llvm.icmp "slt" %47, %34 : i64
    llvm.cond_br %48, ^bb4, ^bb46
  ^bb4:  // pred: ^bb3
    %49 = llvm.sub %34, %47 : i64
    %50 = llvm.intr.umin(%49, %28) : (i64, i64) -> i64
    %51 = llvm.mlir.constant(12 : index) : i64
    %52 = llvm.mlir.constant(256 : index) : i64
    %53 = llvm.mlir.constant(16 : index) : i64
    %54 = llvm.mlir.constant(1 : index) : i64
    %55 = llvm.mlir.constant(4096 : index) : i64
    %56 = llvm.mlir.constant(49152 : index) : i64
    %57 = llvm.mlir.zero : !llvm.ptr
    %58 = llvm.getelementptr %57[%56] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %59 = llvm.ptrtoint %58 : !llvm.ptr to i64
    %60 = llvm.mlir.constant(64 : index) : i64
    %61 = llvm.add %59, %60 : i64
    %62 = llvm.call @malloc(%61) : (i64) -> !llvm.ptr
    %63 = llvm.ptrtoint %62 : !llvm.ptr to i64
    %64 = llvm.mlir.constant(1 : index) : i64
    %65 = llvm.sub %60, %64 : i64
    %66 = llvm.add %63, %65 : i64
    %67 = llvm.urem %66, %60 : i64
    %68 = llvm.sub %66, %67 : i64
    %69 = llvm.inttoptr %68 : i64 to !llvm.ptr
    %70 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %71 = llvm.insertvalue %62, %70[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %72 = llvm.insertvalue %69, %71[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %73 = llvm.mlir.constant(0 : index) : i64
    %74 = llvm.insertvalue %73, %72[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %75 = llvm.insertvalue %51, %74[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %76 = llvm.insertvalue %52, %75[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %77 = llvm.insertvalue %53, %76[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %78 = llvm.insertvalue %55, %77[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %79 = llvm.insertvalue %53, %78[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %80 = llvm.insertvalue %54, %79[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.br ^bb5(%31 : i64)
  ^bb5(%81: i64):  // 2 preds: ^bb4, ^bb12
    %82 = llvm.icmp "slt" %81, %46 : i64
    llvm.cond_br %82, ^bb6(%31 : i64), ^bb13
  ^bb6(%83: i64):  // 2 preds: ^bb5, ^bb11
    %84 = llvm.icmp "slt" %83, %28 : i64
    llvm.cond_br %84, ^bb7(%31 : i64), ^bb12
  ^bb7(%85: i64):  // 2 preds: ^bb6, ^bb10
    %86 = llvm.icmp "slt" %85, %27 : i64
    llvm.cond_br %86, ^bb8, ^bb11
  ^bb8:  // pred: ^bb7
    %87 = llvm.add %47, %83 : i64
    %88 = llvm.mul %81, %27 : i64
    %89 = llvm.add %88, %85 : i64
    %90 = llvm.add %36, %89 : i64
    %91 = llvm.icmp "ult" %87, %34 : i64
    %92 = llvm.icmp "ult" %90, %35 : i64
    %93 = llvm.and %91, %92 : i1
    llvm.cond_br %93, ^bb9, ^bb10(%24 : f32)
  ^bb9:  // pred: ^bb8
    %94 = llvm.extractvalue %7[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %95 = llvm.extractvalue %7[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %96 = llvm.mul %87, %95 : i64
    %97 = llvm.add %96, %90 : i64
    %98 = llvm.getelementptr %94[%97] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %99 = llvm.load %98 : !llvm.ptr -> f32
    llvm.br ^bb10(%99 : f32)
  ^bb10(%100: f32):  // 2 preds: ^bb8, ^bb9
    %101 = llvm.extractvalue %80[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %102 = llvm.mlir.constant(4096 : index) : i64
    %103 = llvm.mul %81, %102 : i64
    %104 = llvm.mlir.constant(16 : index) : i64
    %105 = llvm.mul %83, %104 : i64
    %106 = llvm.add %103, %105 : i64
    %107 = llvm.add %106, %85 : i64
    %108 = llvm.getelementptr %101[%107] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %100, %108 : f32, !llvm.ptr
    %109 = llvm.add %85, %32 : i64
    llvm.br ^bb7(%109 : i64)
  ^bb11:  // pred: ^bb7
    %110 = llvm.add %83, %32 : i64
    llvm.br ^bb6(%110 : i64)
  ^bb12:  // pred: ^bb6
    %111 = llvm.add %81, %32 : i64
    llvm.br ^bb5(%111 : i64)
  ^bb13:  // pred: ^bb5
    %112 = llvm.extractvalue %80[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %113 = llvm.ptrtoint %112 : !llvm.ptr to i64
    llvm.br ^bb14(%31 : i64)
  ^bb14(%114: i64):  // 2 preds: ^bb13, ^bb44
    %115 = llvm.icmp "slt" %114, %33 : i64
    llvm.cond_br %115, ^bb15, ^bb45
  ^bb15:  // pred: ^bb14
    %116 = llvm.sub %33, %114 : i64
    %117 = llvm.intr.umin(%116, %30) : (i64, i64) -> i64
    %118 = llvm.mlir.constant(0 : index) : i64
    %119 = llvm.icmp "eq" %117, %118 : i64
    %120 = llvm.mlir.constant(1 : index) : i64
    %121 = llvm.sub %117, %120 : i64
    %122 = llvm.udiv %121, %30 : i64
    %123 = llvm.add %122, %120 : i64
    %124 = llvm.select %119, %118, %123 : i1, i64
    %125 = llvm.mlir.constant(1 : index) : i64
    %126 = llvm.mlir.constant(256 : index) : i64
    %127 = llvm.mlir.constant(6 : index) : i64
    %128 = llvm.mlir.constant(1 : index) : i64
    %129 = llvm.mlir.constant(1536 : index) : i64
    %130 = llvm.mlir.constant(1536 : index) : i64
    %131 = llvm.mlir.zero : !llvm.ptr
    %132 = llvm.getelementptr %131[%130] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %133 = llvm.ptrtoint %132 : !llvm.ptr to i64
    %134 = llvm.mlir.constant(64 : index) : i64
    %135 = llvm.add %133, %134 : i64
    %136 = llvm.call @malloc(%135) : (i64) -> !llvm.ptr
    %137 = llvm.ptrtoint %136 : !llvm.ptr to i64
    %138 = llvm.mlir.constant(1 : index) : i64
    %139 = llvm.sub %134, %138 : i64
    %140 = llvm.add %137, %139 : i64
    %141 = llvm.urem %140, %134 : i64
    %142 = llvm.sub %140, %141 : i64
    %143 = llvm.inttoptr %142 : i64 to !llvm.ptr
    %144 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %145 = llvm.insertvalue %136, %144[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %146 = llvm.insertvalue %143, %145[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %147 = llvm.mlir.constant(0 : index) : i64
    %148 = llvm.insertvalue %147, %146[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %149 = llvm.insertvalue %125, %148[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %150 = llvm.insertvalue %126, %149[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %151 = llvm.insertvalue %127, %150[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %152 = llvm.insertvalue %129, %151[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %153 = llvm.insertvalue %127, %152[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %154 = llvm.insertvalue %128, %153[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.br ^bb16(%31 : i64)
  ^bb16(%155: i64):  // 2 preds: ^bb15, ^bb23
    %156 = llvm.icmp "slt" %155, %124 : i64
    llvm.cond_br %156, ^bb17(%31 : i64), ^bb24
  ^bb17(%157: i64):  // 2 preds: ^bb16, ^bb22
    %158 = llvm.icmp "slt" %157, %28 : i64
    llvm.cond_br %158, ^bb18(%31 : i64), ^bb23
  ^bb18(%159: i64):  // 2 preds: ^bb17, ^bb21
    %160 = llvm.icmp "slt" %159, %30 : i64
    llvm.cond_br %160, ^bb19, ^bb22
  ^bb19:  // pred: ^bb18
    %161 = llvm.mul %155, %30 : i64
    %162 = llvm.add %161, %159 : i64
    %163 = llvm.add %114, %162 : i64
    %164 = llvm.add %47, %157 : i64
    %165 = llvm.icmp "ult" %163, %33 : i64
    %166 = llvm.icmp "ult" %164, %34 : i64
    %167 = llvm.and %165, %166 : i1
    llvm.cond_br %167, ^bb20, ^bb21(%24 : f32)
  ^bb20:  // pred: ^bb19
    %168 = llvm.extractvalue %15[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %169 = llvm.extractvalue %15[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %170 = llvm.mul %163, %169 : i64
    %171 = llvm.add %170, %164 : i64
    %172 = llvm.getelementptr %168[%171] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %173 = llvm.load %172 : !llvm.ptr -> f32
    llvm.br ^bb21(%173 : f32)
  ^bb21(%174: f32):  // 2 preds: ^bb19, ^bb20
    %175 = llvm.extractvalue %154[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %176 = llvm.mlir.constant(1536 : index) : i64
    %177 = llvm.mul %155, %176 : i64
    %178 = llvm.mlir.constant(6 : index) : i64
    %179 = llvm.mul %157, %178 : i64
    %180 = llvm.add %177, %179 : i64
    %181 = llvm.add %180, %159 : i64
    %182 = llvm.getelementptr %175[%181] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %174, %182 : f32, !llvm.ptr
    %183 = llvm.add %159, %32 : i64
    llvm.br ^bb18(%183 : i64)
  ^bb22:  // pred: ^bb18
    %184 = llvm.add %157, %32 : i64
    llvm.br ^bb17(%184 : i64)
  ^bb23:  // pred: ^bb17
    %185 = llvm.add %155, %32 : i64
    llvm.br ^bb16(%185 : i64)
  ^bb24:  // pred: ^bb16
    %186 = llvm.extractvalue %154[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %187 = llvm.ptrtoint %186 : !llvm.ptr to i64
    %188 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %189 = llvm.ptrtoint %188 : !llvm.ptr to i64
    llvm.br ^bb25(%31 : i64)
  ^bb25(%190: i64):  // 2 preds: ^bb24, ^bb43
    %191 = llvm.icmp "slt" %190, %46 : i64
    llvm.cond_br %191, ^bb26(%31 : i64), ^bb44
  ^bb26(%192: i64):  // 2 preds: ^bb25, ^bb42
    %193 = llvm.icmp "slt" %192, %124 : i64
    llvm.cond_br %193, ^bb27, ^bb43
  ^bb27:  // pred: ^bb26
    %194 = llvm.mul %192, %26 : i64
    %195 = llvm.mul %190, %25 : i64
    %196 = llvm.mul %192, %30 : i64
    %197 = llvm.add %114, %196 : i64
    %198 = llvm.mul %190, %27 : i64
    %199 = llvm.add %36, %198 : i64
    %200 = llvm.sub %33, %197 : i64
    %201 = llvm.intr.umin(%200, %30) : (i64, i64) -> i64
    %202 = llvm.sub %35, %199 : i64
    %203 = llvm.intr.umin(%202, %27) : (i64, i64) -> i64
    %204 = llvm.icmp "eq" %201, %30 : i64
    %205 = llvm.icmp "eq" %203, %27 : i64
    %206 = llvm.and %204, %205 : i1
    llvm.cond_br %206, ^bb28, ^bb29
  ^bb28:  // pred: ^bb27
    %207 = llvm.mul %197, %35 : i64
    %208 = llvm.add %207, %199 : i64
    llvm.call @buddy_blis_sgemm_6x16(%50, %187, %194, %113, %195, %189, %208, %35, %32) : (i64, i64, i64, i64, i64, i64, i64, i64, i64) -> ()
    llvm.br ^bb42
  ^bb29:  // pred: ^bb27
    %209 = llvm.mlir.constant(6 : index) : i64
    %210 = llvm.mlir.constant(16 : index) : i64
    %211 = llvm.mlir.constant(1 : index) : i64
    %212 = llvm.mlir.constant(96 : index) : i64
    %213 = llvm.mlir.zero : !llvm.ptr
    %214 = llvm.getelementptr %213[%212] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %215 = llvm.ptrtoint %214 : !llvm.ptr to i64
    %216 = llvm.mlir.constant(64 : index) : i64
    %217 = llvm.add %215, %216 : i64
    %218 = llvm.call @malloc(%217) : (i64) -> !llvm.ptr
    %219 = llvm.ptrtoint %218 : !llvm.ptr to i64
    %220 = llvm.mlir.constant(1 : index) : i64
    %221 = llvm.sub %216, %220 : i64
    %222 = llvm.add %219, %221 : i64
    %223 = llvm.urem %222, %216 : i64
    %224 = llvm.sub %222, %223 : i64
    %225 = llvm.inttoptr %224 : i64 to !llvm.ptr
    %226 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %227 = llvm.insertvalue %218, %226[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %228 = llvm.insertvalue %225, %227[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %229 = llvm.mlir.constant(0 : index) : i64
    %230 = llvm.insertvalue %229, %228[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %231 = llvm.insertvalue %209, %230[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %232 = llvm.insertvalue %210, %231[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %233 = llvm.insertvalue %210, %232[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %234 = llvm.insertvalue %211, %233[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.br ^bb30(%31 : i64)
  ^bb30(%235: i64):  // 2 preds: ^bb29, ^bb35
    %236 = llvm.icmp "slt" %235, %30 : i64
    llvm.cond_br %236, ^bb31(%31 : i64), ^bb36
  ^bb31(%237: i64):  // 2 preds: ^bb30, ^bb34
    %238 = llvm.icmp "slt" %237, %27 : i64
    llvm.cond_br %238, ^bb32, ^bb35
  ^bb32:  // pred: ^bb31
    %239 = llvm.icmp "ult" %235, %201 : i64
    %240 = llvm.icmp "ult" %237, %203 : i64
    %241 = llvm.add %197, %235 : i64
    %242 = llvm.add %199, %237 : i64
    %243 = llvm.and %239, %240 : i1
    llvm.cond_br %243, ^bb33, ^bb34(%24 : f32)
  ^bb33:  // pred: ^bb32
    %244 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %245 = llvm.extractvalue %23[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %246 = llvm.mul %241, %245 : i64
    %247 = llvm.add %246, %242 : i64
    %248 = llvm.getelementptr %244[%247] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %249 = llvm.load %248 : !llvm.ptr -> f32
    llvm.br ^bb34(%249 : f32)
  ^bb34(%250: f32):  // 2 preds: ^bb32, ^bb33
    %251 = llvm.extractvalue %234[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %252 = llvm.mlir.constant(16 : index) : i64
    %253 = llvm.mul %235, %252 : i64
    %254 = llvm.add %253, %237 : i64
    %255 = llvm.getelementptr %251[%254] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %250, %255 : f32, !llvm.ptr
    %256 = llvm.add %237, %32 : i64
    llvm.br ^bb31(%256 : i64)
  ^bb35:  // pred: ^bb31
    %257 = llvm.add %235, %32 : i64
    llvm.br ^bb30(%257 : i64)
  ^bb36:  // pred: ^bb30
    %258 = llvm.extractvalue %234[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %259 = llvm.ptrtoint %258 : !llvm.ptr to i64
    llvm.call @buddy_blis_sgemm_6x16_fringe(%50, %187, %194, %113, %195, %259, %31, %27, %32) : (i64, i64, i64, i64, i64, i64, i64, i64, i64) -> ()
    llvm.br ^bb37(%31 : i64)
  ^bb37(%260: i64):  // 2 preds: ^bb36, ^bb40
    %261 = llvm.icmp "slt" %260, %201 : i64
    llvm.cond_br %261, ^bb38(%31 : i64), ^bb41
  ^bb38(%262: i64):  // 2 preds: ^bb37, ^bb39
    %263 = llvm.icmp "slt" %262, %203 : i64
    llvm.cond_br %263, ^bb39, ^bb40
  ^bb39:  // pred: ^bb38
    %264 = llvm.extractvalue %234[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %265 = llvm.mlir.constant(16 : index) : i64
    %266 = llvm.mul %260, %265 : i64
    %267 = llvm.add %266, %262 : i64
    %268 = llvm.getelementptr %264[%267] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %269 = llvm.load %268 : !llvm.ptr -> f32
    %270 = llvm.add %197, %260 : i64
    %271 = llvm.add %199, %262 : i64
    %272 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %273 = llvm.extractvalue %23[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %274 = llvm.mul %270, %273 : i64
    %275 = llvm.add %274, %271 : i64
    %276 = llvm.getelementptr %272[%275] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %269, %276 : f32, !llvm.ptr
    %277 = llvm.add %262, %32 : i64
    llvm.br ^bb38(%277 : i64)
  ^bb40:  // pred: ^bb38
    %278 = llvm.add %260, %32 : i64
    llvm.br ^bb37(%278 : i64)
  ^bb41:  // pred: ^bb37
    %279 = llvm.extractvalue %234[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.call @free(%279) : (!llvm.ptr) -> ()
    llvm.br ^bb42
  ^bb42:  // 2 preds: ^bb28, ^bb41
    %280 = llvm.add %192, %32 : i64
    llvm.br ^bb26(%280 : i64)
  ^bb43:  // pred: ^bb26
    %281 = llvm.add %190, %32 : i64
    llvm.br ^bb25(%281 : i64)
  ^bb44:  // pred: ^bb25
    %282 = llvm.extractvalue %154[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.call @free(%282) : (!llvm.ptr) -> ()
    %283 = llvm.add %114, %30 : i64
    llvm.br ^bb14(%283 : i64)
  ^bb45:  // pred: ^bb14
    %284 = llvm.extractvalue %80[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.call @free(%284) : (!llvm.ptr) -> ()
    %285 = llvm.add %47, %28 : i64
    llvm.br ^bb3(%285 : i64)
  ^bb46:  // pred: ^bb3
    %286 = llvm.add %36, %29 : i64
    llvm.br ^bb1(%286 : i64)
  ^bb47:  // pred: ^bb1
    llvm.return %23 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
  }
  llvm.func @_mlir_ciface_cgo_f32_m6_n192_k256_pab_v0(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: !llvm.ptr, %arg3: !llvm.ptr) attributes {llvm.emit_c_interface} {
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
    %24 = llvm.call @cgo_f32_m6_n192_k256_pab_v0(%1, %2, %3, %4, %5, %6, %7, %9, %10, %11, %12, %13, %14, %15, %17, %18, %19, %20, %21, %22, %23) : (!llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    llvm.store %24, %arg0 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>, !llvm.ptr
    llvm.return
  }
}

