module {
  llvm.func @free(!llvm.ptr)
  llvm.func @malloc(i64) -> !llvm.ptr
  llvm.func @buddy_blis_sgemm_6x16_fringe(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_blis_sgemm_6x16(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_microkernel_fringe_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_microkernel_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @chapter5_fringe_dev(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: i64, %arg3: i64, %arg4: i64, %arg5: i64, %arg6: i64, %arg7: !llvm.ptr, %arg8: !llvm.ptr, %arg9: i64, %arg10: i64, %arg11: i64, %arg12: i64, %arg13: i64, %arg14: !llvm.ptr, %arg15: !llvm.ptr, %arg16: i64, %arg17: i64, %arg18: i64, %arg19: i64, %arg20: i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> attributes {llvm.emit_c_interface} {
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
    %24 = llvm.mlir.constant(102 : index) : i64
    %25 = llvm.mlir.constant(4 : index) : i64
    %26 = llvm.mlir.constant(0 : index) : i64
    %27 = llvm.mlir.constant(1 : index) : i64
    %28 = llvm.mlir.constant(19 : index) : i64
    %29 = llvm.mlir.constant(65 : index) : i64
    %30 = llvm.mlir.constant(17 : index) : i64
    %31 = llvm.mlir.constant(64 : index) : i64
    %32 = llvm.mlir.constant(6 : index) : i64
    %33 = llvm.mlir.constant(16 : index) : i64
    %34 = llvm.mlir.constant(384 : index) : i64
    %35 = llvm.mlir.constant(1024 : index) : i64
    %36 = llvm.mlir.constant(0.000000e+00 : f32) : f32
    %37 = llvm.mlir.constant(2 : index) : i64
    llvm.br ^bb1(%26 : i64)
  ^bb1(%38: i64):  // 2 preds: ^bb0, ^bb40
    %39 = llvm.icmp "slt" %38, %29 : i64
    llvm.cond_br %39, ^bb2, ^bb41
  ^bb2:  // pred: ^bb1
    %40 = llvm.sub %29, %38 : i64
    %41 = llvm.intr.umin(%40, %31) : (i64, i64) -> i64
    %42 = llvm.mlir.constant(2 : index) : i64
    %43 = llvm.mlir.constant(64 : index) : i64
    %44 = llvm.mlir.constant(16 : index) : i64
    %45 = llvm.mlir.constant(1 : index) : i64
    %46 = llvm.mlir.constant(1024 : index) : i64
    %47 = llvm.mlir.constant(2048 : index) : i64
    %48 = llvm.mlir.zero : !llvm.ptr
    %49 = llvm.getelementptr %48[%47] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %50 = llvm.ptrtoint %49 : !llvm.ptr to i64
    %51 = llvm.mlir.constant(64 : index) : i64
    %52 = llvm.add %50, %51 : i64
    %53 = llvm.call @malloc(%52) : (i64) -> !llvm.ptr
    %54 = llvm.ptrtoint %53 : !llvm.ptr to i64
    %55 = llvm.mlir.constant(1 : index) : i64
    %56 = llvm.sub %51, %55 : i64
    %57 = llvm.add %54, %56 : i64
    %58 = llvm.urem %57, %51 : i64
    %59 = llvm.sub %57, %58 : i64
    %60 = llvm.inttoptr %59 : i64 to !llvm.ptr
    %61 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %62 = llvm.insertvalue %53, %61[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %63 = llvm.insertvalue %60, %62[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %64 = llvm.mlir.constant(0 : index) : i64
    %65 = llvm.insertvalue %64, %63[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %66 = llvm.insertvalue %42, %65[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %67 = llvm.insertvalue %43, %66[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %68 = llvm.insertvalue %44, %67[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %69 = llvm.insertvalue %46, %68[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %70 = llvm.insertvalue %44, %69[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %71 = llvm.insertvalue %45, %70[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.br ^bb3(%26 : i64)
  ^bb3(%72: i64):  // 2 preds: ^bb2, ^bb10
    %73 = llvm.icmp "slt" %72, %37 : i64
    llvm.cond_br %73, ^bb4(%26 : i64), ^bb11
  ^bb4(%74: i64):  // 2 preds: ^bb3, ^bb9
    %75 = llvm.icmp "slt" %74, %31 : i64
    llvm.cond_br %75, ^bb5(%26 : i64), ^bb10
  ^bb5(%76: i64):  // 2 preds: ^bb4, ^bb8
    %77 = llvm.icmp "slt" %76, %33 : i64
    llvm.cond_br %77, ^bb6, ^bb9
  ^bb6:  // pred: ^bb5
    %78 = llvm.add %38, %74 : i64
    %79 = llvm.mul %72, %33 : i64
    %80 = llvm.add %79, %76 : i64
    %81 = llvm.icmp "ult" %78, %29 : i64
    %82 = llvm.icmp "ult" %80, %30 : i64
    %83 = llvm.and %81, %82 : i1
    llvm.cond_br %83, ^bb7, ^bb8(%36 : f32)
  ^bb7:  // pred: ^bb6
    %84 = llvm.extractvalue %7[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %85 = llvm.mlir.constant(17 : index) : i64
    %86 = llvm.mul %78, %85 : i64
    %87 = llvm.add %86, %80 : i64
    %88 = llvm.getelementptr %84[%87] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %89 = llvm.load %88 : !llvm.ptr -> f32
    llvm.br ^bb8(%89 : f32)
  ^bb8(%90: f32):  // 2 preds: ^bb6, ^bb7
    %91 = llvm.extractvalue %71[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %92 = llvm.mlir.constant(1024 : index) : i64
    %93 = llvm.mul %72, %92 : i64
    %94 = llvm.mlir.constant(16 : index) : i64
    %95 = llvm.mul %74, %94 : i64
    %96 = llvm.add %93, %95 : i64
    %97 = llvm.add %96, %76 : i64
    %98 = llvm.getelementptr %91[%97] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %90, %98 : f32, !llvm.ptr
    %99 = llvm.add %76, %27 : i64
    llvm.br ^bb5(%99 : i64)
  ^bb9:  // pred: ^bb5
    %100 = llvm.add %74, %27 : i64
    llvm.br ^bb4(%100 : i64)
  ^bb10:  // pred: ^bb4
    %101 = llvm.add %72, %27 : i64
    llvm.br ^bb3(%101 : i64)
  ^bb11:  // pred: ^bb3
    %102 = llvm.extractvalue %71[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %103 = llvm.ptrtoint %102 : !llvm.ptr to i64
    %104 = llvm.mlir.constant(4 : index) : i64
    %105 = llvm.mlir.constant(64 : index) : i64
    %106 = llvm.mlir.constant(6 : index) : i64
    %107 = llvm.mlir.constant(1 : index) : i64
    %108 = llvm.mlir.constant(384 : index) : i64
    %109 = llvm.mlir.constant(1536 : index) : i64
    %110 = llvm.mlir.zero : !llvm.ptr
    %111 = llvm.getelementptr %110[%109] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %112 = llvm.ptrtoint %111 : !llvm.ptr to i64
    %113 = llvm.mlir.constant(64 : index) : i64
    %114 = llvm.add %112, %113 : i64
    %115 = llvm.call @malloc(%114) : (i64) -> !llvm.ptr
    %116 = llvm.ptrtoint %115 : !llvm.ptr to i64
    %117 = llvm.mlir.constant(1 : index) : i64
    %118 = llvm.sub %113, %117 : i64
    %119 = llvm.add %116, %118 : i64
    %120 = llvm.urem %119, %113 : i64
    %121 = llvm.sub %119, %120 : i64
    %122 = llvm.inttoptr %121 : i64 to !llvm.ptr
    %123 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %124 = llvm.insertvalue %115, %123[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %125 = llvm.insertvalue %122, %124[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %126 = llvm.mlir.constant(0 : index) : i64
    %127 = llvm.insertvalue %126, %125[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %128 = llvm.insertvalue %104, %127[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %129 = llvm.insertvalue %105, %128[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %130 = llvm.insertvalue %106, %129[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %131 = llvm.insertvalue %108, %130[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %132 = llvm.insertvalue %106, %131[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %133 = llvm.insertvalue %107, %132[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.br ^bb12(%26 : i64)
  ^bb12(%134: i64):  // 2 preds: ^bb11, ^bb19
    %135 = llvm.icmp "slt" %134, %25 : i64
    llvm.cond_br %135, ^bb13(%26 : i64), ^bb20
  ^bb13(%136: i64):  // 2 preds: ^bb12, ^bb18
    %137 = llvm.icmp "slt" %136, %31 : i64
    llvm.cond_br %137, ^bb14(%26 : i64), ^bb19
  ^bb14(%138: i64):  // 2 preds: ^bb13, ^bb17
    %139 = llvm.icmp "slt" %138, %32 : i64
    llvm.cond_br %139, ^bb15, ^bb18
  ^bb15:  // pred: ^bb14
    %140 = llvm.mul %134, %32 : i64
    %141 = llvm.add %140, %138 : i64
    %142 = llvm.add %38, %136 : i64
    %143 = llvm.icmp "ult" %141, %28 : i64
    %144 = llvm.icmp "ult" %142, %29 : i64
    %145 = llvm.and %143, %144 : i1
    llvm.cond_br %145, ^bb16, ^bb17(%36 : f32)
  ^bb16:  // pred: ^bb15
    %146 = llvm.extractvalue %15[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %147 = llvm.mlir.constant(65 : index) : i64
    %148 = llvm.mul %141, %147 : i64
    %149 = llvm.add %148, %142 : i64
    %150 = llvm.getelementptr %146[%149] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %151 = llvm.load %150 : !llvm.ptr -> f32
    llvm.br ^bb17(%151 : f32)
  ^bb17(%152: f32):  // 2 preds: ^bb15, ^bb16
    %153 = llvm.extractvalue %133[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %154 = llvm.mlir.constant(384 : index) : i64
    %155 = llvm.mul %134, %154 : i64
    %156 = llvm.mlir.constant(6 : index) : i64
    %157 = llvm.mul %136, %156 : i64
    %158 = llvm.add %155, %157 : i64
    %159 = llvm.add %158, %138 : i64
    %160 = llvm.getelementptr %153[%159] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %152, %160 : f32, !llvm.ptr
    %161 = llvm.add %138, %27 : i64
    llvm.br ^bb14(%161 : i64)
  ^bb18:  // pred: ^bb14
    %162 = llvm.add %136, %27 : i64
    llvm.br ^bb13(%162 : i64)
  ^bb19:  // pred: ^bb13
    %163 = llvm.add %134, %27 : i64
    llvm.br ^bb12(%163 : i64)
  ^bb20:  // pred: ^bb12
    %164 = llvm.extractvalue %133[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %165 = llvm.ptrtoint %164 : !llvm.ptr to i64
    %166 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %167 = llvm.ptrtoint %166 : !llvm.ptr to i64
    llvm.br ^bb21(%26 : i64)
  ^bb21(%168: i64):  // 2 preds: ^bb20, ^bb39
    %169 = llvm.icmp "slt" %168, %37 : i64
    llvm.cond_br %169, ^bb22(%26 : i64), ^bb40
  ^bb22(%170: i64):  // 2 preds: ^bb21, ^bb38
    %171 = llvm.icmp "slt" %170, %25 : i64
    llvm.cond_br %171, ^bb23, ^bb39
  ^bb23:  // pred: ^bb22
    %172 = llvm.mul %170, %34 : i64
    %173 = llvm.mul %168, %35 : i64
    %174 = llvm.mul %170, %32 : i64
    %175 = llvm.mul %168, %33 : i64
    %176 = llvm.sub %28, %174 : i64
    %177 = llvm.intr.umin(%176, %32) : (i64, i64) -> i64
    %178 = llvm.sub %30, %175 : i64
    %179 = llvm.intr.umin(%178, %33) : (i64, i64) -> i64
    %180 = llvm.icmp "eq" %177, %32 : i64
    %181 = llvm.icmp "eq" %179, %33 : i64
    %182 = llvm.and %180, %181 : i1
    llvm.cond_br %182, ^bb24, ^bb25
  ^bb24:  // pred: ^bb23
    %183 = llvm.mul %170, %24 : i64
    %184 = llvm.add %183, %175 : i64
    llvm.call @buddy_blis_sgemm_6x16(%41, %165, %172, %103, %173, %167, %184, %30, %27) : (i64, i64, i64, i64, i64, i64, i64, i64, i64) -> ()
    llvm.br ^bb38
  ^bb25:  // pred: ^bb23
    %185 = llvm.mlir.constant(6 : index) : i64
    %186 = llvm.mlir.constant(16 : index) : i64
    %187 = llvm.mlir.constant(1 : index) : i64
    %188 = llvm.mlir.constant(96 : index) : i64
    %189 = llvm.mlir.zero : !llvm.ptr
    %190 = llvm.getelementptr %189[%188] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %191 = llvm.ptrtoint %190 : !llvm.ptr to i64
    %192 = llvm.mlir.constant(64 : index) : i64
    %193 = llvm.add %191, %192 : i64
    %194 = llvm.call @malloc(%193) : (i64) -> !llvm.ptr
    %195 = llvm.ptrtoint %194 : !llvm.ptr to i64
    %196 = llvm.mlir.constant(1 : index) : i64
    %197 = llvm.sub %192, %196 : i64
    %198 = llvm.add %195, %197 : i64
    %199 = llvm.urem %198, %192 : i64
    %200 = llvm.sub %198, %199 : i64
    %201 = llvm.inttoptr %200 : i64 to !llvm.ptr
    %202 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %203 = llvm.insertvalue %194, %202[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %204 = llvm.insertvalue %201, %203[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %205 = llvm.mlir.constant(0 : index) : i64
    %206 = llvm.insertvalue %205, %204[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %207 = llvm.insertvalue %185, %206[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %208 = llvm.insertvalue %186, %207[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %209 = llvm.insertvalue %186, %208[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %210 = llvm.insertvalue %187, %209[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.br ^bb26(%26 : i64)
  ^bb26(%211: i64):  // 2 preds: ^bb25, ^bb31
    %212 = llvm.icmp "slt" %211, %32 : i64
    llvm.cond_br %212, ^bb27(%26 : i64), ^bb32
  ^bb27(%213: i64):  // 2 preds: ^bb26, ^bb30
    %214 = llvm.icmp "slt" %213, %33 : i64
    llvm.cond_br %214, ^bb28, ^bb31
  ^bb28:  // pred: ^bb27
    %215 = llvm.icmp "ult" %211, %177 : i64
    %216 = llvm.icmp "ult" %213, %179 : i64
    %217 = llvm.add %174, %211 : i64
    %218 = llvm.add %175, %213 : i64
    %219 = llvm.and %215, %216 : i1
    llvm.cond_br %219, ^bb29, ^bb30(%36 : f32)
  ^bb29:  // pred: ^bb28
    %220 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %221 = llvm.mlir.constant(17 : index) : i64
    %222 = llvm.mul %217, %221 : i64
    %223 = llvm.add %222, %218 : i64
    %224 = llvm.getelementptr %220[%223] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %225 = llvm.load %224 : !llvm.ptr -> f32
    llvm.br ^bb30(%225 : f32)
  ^bb30(%226: f32):  // 2 preds: ^bb28, ^bb29
    %227 = llvm.extractvalue %210[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %228 = llvm.mlir.constant(16 : index) : i64
    %229 = llvm.mul %211, %228 : i64
    %230 = llvm.add %229, %213 : i64
    %231 = llvm.getelementptr %227[%230] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %226, %231 : f32, !llvm.ptr
    %232 = llvm.add %213, %27 : i64
    llvm.br ^bb27(%232 : i64)
  ^bb31:  // pred: ^bb27
    %233 = llvm.add %211, %27 : i64
    llvm.br ^bb26(%233 : i64)
  ^bb32:  // pred: ^bb26
    %234 = llvm.extractvalue %210[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %235 = llvm.ptrtoint %234 : !llvm.ptr to i64
    llvm.call @buddy_blis_sgemm_6x16_fringe(%41, %165, %172, %103, %173, %235, %26, %33, %27) : (i64, i64, i64, i64, i64, i64, i64, i64, i64) -> ()
    llvm.br ^bb33(%26 : i64)
  ^bb33(%236: i64):  // 2 preds: ^bb32, ^bb36
    %237 = llvm.icmp "slt" %236, %177 : i64
    llvm.cond_br %237, ^bb34(%26 : i64), ^bb37
  ^bb34(%238: i64):  // 2 preds: ^bb33, ^bb35
    %239 = llvm.icmp "slt" %238, %179 : i64
    llvm.cond_br %239, ^bb35, ^bb36
  ^bb35:  // pred: ^bb34
    %240 = llvm.extractvalue %210[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %241 = llvm.mlir.constant(16 : index) : i64
    %242 = llvm.mul %236, %241 : i64
    %243 = llvm.add %242, %238 : i64
    %244 = llvm.getelementptr %240[%243] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %245 = llvm.load %244 : !llvm.ptr -> f32
    %246 = llvm.add %174, %236 : i64
    %247 = llvm.add %175, %238 : i64
    %248 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %249 = llvm.mlir.constant(17 : index) : i64
    %250 = llvm.mul %246, %249 : i64
    %251 = llvm.add %250, %247 : i64
    %252 = llvm.getelementptr %248[%251] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %245, %252 : f32, !llvm.ptr
    %253 = llvm.add %238, %27 : i64
    llvm.br ^bb34(%253 : i64)
  ^bb36:  // pred: ^bb34
    %254 = llvm.add %236, %27 : i64
    llvm.br ^bb33(%254 : i64)
  ^bb37:  // pred: ^bb33
    %255 = llvm.extractvalue %210[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.call @free(%255) : (!llvm.ptr) -> ()
    llvm.br ^bb38
  ^bb38:  // 2 preds: ^bb24, ^bb37
    %256 = llvm.add %170, %27 : i64
    llvm.br ^bb22(%256 : i64)
  ^bb39:  // pred: ^bb22
    %257 = llvm.add %168, %27 : i64
    llvm.br ^bb21(%257 : i64)
  ^bb40:  // pred: ^bb21
    %258 = llvm.extractvalue %133[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.call @free(%258) : (!llvm.ptr) -> ()
    %259 = llvm.extractvalue %71[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.call @free(%259) : (!llvm.ptr) -> ()
    %260 = llvm.add %38, %31 : i64
    llvm.br ^bb1(%260 : i64)
  ^bb41:  // pred: ^bb1
    llvm.return %23 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
  }
  llvm.func @_mlir_ciface_chapter5_fringe_dev(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: !llvm.ptr, %arg3: !llvm.ptr) attributes {llvm.emit_c_interface} {
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
    %24 = llvm.call @chapter5_fringe_dev(%1, %2, %3, %4, %5, %6, %7, %9, %10, %11, %12, %13, %14, %15, %17, %18, %19, %20, %21, %22, %23) : (!llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    llvm.store %24, %arg0 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>, !llvm.ptr
    llvm.return
  }
}

