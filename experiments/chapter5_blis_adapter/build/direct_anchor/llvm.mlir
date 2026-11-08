module {
  llvm.func @free(!llvm.ptr)
  llvm.func @malloc(i64) -> !llvm.ptr
  llvm.func @buddy_blis_sgemm_6x16(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @buddy_microkernel_placeholder(i64, i64, i64, i64, i64, i64, i64, i64, i64) attributes {sym_visibility = "private"}
  llvm.func @chapter5_direct_anchor(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: i64, %arg3: i64, %arg4: i64, %arg5: i64, %arg6: i64, %arg7: !llvm.ptr, %arg8: !llvm.ptr, %arg9: i64, %arg10: i64, %arg11: i64, %arg12: i64, %arg13: i64, %arg14: !llvm.ptr, %arg15: !llvm.ptr, %arg16: i64, %arg17: i64, %arg18: i64, %arg19: i64, %arg20: i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> attributes {llvm.emit_c_interface} {
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
    %24 = llvm.mlir.constant(0 : index) : i64
    %25 = llvm.mlir.constant(1 : index) : i64
    %26 = llvm.mlir.constant(192 : index) : i64
    %27 = llvm.mlir.constant(256 : index) : i64
    %28 = llvm.mlir.constant(24 : index) : i64
    %29 = llvm.mlir.constant(32 : index) : i64
    %30 = llvm.mlir.constant(64 : index) : i64
    %31 = llvm.mlir.constant(6 : index) : i64
    %32 = llvm.mlir.constant(16 : index) : i64
    %33 = llvm.mlir.constant(4 : index) : i64
    %34 = llvm.mlir.constant(2 : index) : i64
    %35 = llvm.mlir.constant(384 : index) : i64
    %36 = llvm.mlir.constant(1024 : index) : i64
    llvm.br ^bb1(%24 : i64)
  ^bb1(%37: i64):  // 2 preds: ^bb0, ^bb26
    %38 = llvm.icmp "slt" %37, %27 : i64
    llvm.cond_br %38, ^bb2(%24 : i64), ^bb27
  ^bb2(%39: i64):  // 2 preds: ^bb1, ^bb25
    %40 = llvm.icmp "slt" %39, %27 : i64
    llvm.cond_br %40, ^bb3, ^bb26
  ^bb3:  // pred: ^bb2
    %41 = llvm.mlir.constant(2 : index) : i64
    %42 = llvm.mlir.constant(64 : index) : i64
    %43 = llvm.mlir.constant(16 : index) : i64
    %44 = llvm.mlir.constant(1 : index) : i64
    %45 = llvm.mlir.constant(1024 : index) : i64
    %46 = llvm.mlir.constant(2048 : index) : i64
    %47 = llvm.mlir.zero : !llvm.ptr
    %48 = llvm.getelementptr %47[%46] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %49 = llvm.ptrtoint %48 : !llvm.ptr to i64
    %50 = llvm.mlir.constant(64 : index) : i64
    %51 = llvm.add %49, %50 : i64
    %52 = llvm.call @malloc(%51) : (i64) -> !llvm.ptr
    %53 = llvm.ptrtoint %52 : !llvm.ptr to i64
    %54 = llvm.mlir.constant(1 : index) : i64
    %55 = llvm.sub %50, %54 : i64
    %56 = llvm.add %53, %55 : i64
    %57 = llvm.urem %56, %50 : i64
    %58 = llvm.sub %56, %57 : i64
    %59 = llvm.inttoptr %58 : i64 to !llvm.ptr
    %60 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %61 = llvm.insertvalue %52, %60[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %62 = llvm.insertvalue %59, %61[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %63 = llvm.mlir.constant(0 : index) : i64
    %64 = llvm.insertvalue %63, %62[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %65 = llvm.insertvalue %41, %64[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %66 = llvm.insertvalue %42, %65[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %67 = llvm.insertvalue %43, %66[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %68 = llvm.insertvalue %45, %67[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %69 = llvm.insertvalue %43, %68[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %70 = llvm.insertvalue %44, %69[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.br ^bb4(%24 : i64)
  ^bb4(%71: i64):  // 2 preds: ^bb3, ^bb9
    %72 = llvm.icmp "slt" %71, %34 : i64
    llvm.cond_br %72, ^bb5(%24 : i64), ^bb10
  ^bb5(%73: i64):  // 2 preds: ^bb4, ^bb8
    %74 = llvm.icmp "slt" %73, %30 : i64
    llvm.cond_br %74, ^bb6(%24 : i64), ^bb9
  ^bb6(%75: i64):  // 2 preds: ^bb5, ^bb7
    %76 = llvm.icmp "slt" %75, %32 : i64
    llvm.cond_br %76, ^bb7, ^bb8
  ^bb7:  // pred: ^bb6
    %77 = llvm.add %39, %73 : i64
    %78 = llvm.mul %71, %32 : i64
    %79 = llvm.add %78, %75 : i64
    %80 = llvm.add %37, %79 : i64
    %81 = llvm.extractvalue %7[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %82 = llvm.mlir.constant(256 : index) : i64
    %83 = llvm.mul %77, %82 : i64
    %84 = llvm.add %83, %80 : i64
    %85 = llvm.getelementptr %81[%84] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %86 = llvm.load %85 : !llvm.ptr -> f32
    %87 = llvm.extractvalue %70[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %88 = llvm.mlir.constant(1024 : index) : i64
    %89 = llvm.mul %71, %88 : i64
    %90 = llvm.mlir.constant(16 : index) : i64
    %91 = llvm.mul %73, %90 : i64
    %92 = llvm.add %89, %91 : i64
    %93 = llvm.add %92, %75 : i64
    %94 = llvm.getelementptr %87[%93] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %86, %94 : f32, !llvm.ptr
    %95 = llvm.add %75, %25 : i64
    llvm.br ^bb6(%95 : i64)
  ^bb8:  // pred: ^bb6
    %96 = llvm.add %73, %25 : i64
    llvm.br ^bb5(%96 : i64)
  ^bb9:  // pred: ^bb5
    %97 = llvm.add %71, %25 : i64
    llvm.br ^bb4(%97 : i64)
  ^bb10:  // pred: ^bb4
    %98 = llvm.extractvalue %70[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %99 = llvm.ptrtoint %98 : !llvm.ptr to i64
    llvm.br ^bb11(%24 : i64)
  ^bb11(%100: i64):  // 2 preds: ^bb10, ^bb24
    %101 = llvm.icmp "slt" %100, %26 : i64
    llvm.cond_br %101, ^bb12, ^bb25
  ^bb12:  // pred: ^bb11
    %102 = llvm.mlir.constant(4 : index) : i64
    %103 = llvm.mlir.constant(64 : index) : i64
    %104 = llvm.mlir.constant(6 : index) : i64
    %105 = llvm.mlir.constant(1 : index) : i64
    %106 = llvm.mlir.constant(384 : index) : i64
    %107 = llvm.mlir.constant(1536 : index) : i64
    %108 = llvm.mlir.zero : !llvm.ptr
    %109 = llvm.getelementptr %108[%107] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %110 = llvm.ptrtoint %109 : !llvm.ptr to i64
    %111 = llvm.mlir.constant(64 : index) : i64
    %112 = llvm.add %110, %111 : i64
    %113 = llvm.call @malloc(%112) : (i64) -> !llvm.ptr
    %114 = llvm.ptrtoint %113 : !llvm.ptr to i64
    %115 = llvm.mlir.constant(1 : index) : i64
    %116 = llvm.sub %111, %115 : i64
    %117 = llvm.add %114, %116 : i64
    %118 = llvm.urem %117, %111 : i64
    %119 = llvm.sub %117, %118 : i64
    %120 = llvm.inttoptr %119 : i64 to !llvm.ptr
    %121 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)>
    %122 = llvm.insertvalue %113, %121[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %123 = llvm.insertvalue %120, %122[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %124 = llvm.mlir.constant(0 : index) : i64
    %125 = llvm.insertvalue %124, %123[2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %126 = llvm.insertvalue %102, %125[3, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %127 = llvm.insertvalue %103, %126[3, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %128 = llvm.insertvalue %104, %127[3, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %129 = llvm.insertvalue %106, %128[4, 0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %130 = llvm.insertvalue %104, %129[4, 1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %131 = llvm.insertvalue %105, %130[4, 2] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.br ^bb13(%24 : i64)
  ^bb13(%132: i64):  // 2 preds: ^bb12, ^bb18
    %133 = llvm.icmp "slt" %132, %33 : i64
    llvm.cond_br %133, ^bb14(%24 : i64), ^bb19
  ^bb14(%134: i64):  // 2 preds: ^bb13, ^bb17
    %135 = llvm.icmp "slt" %134, %30 : i64
    llvm.cond_br %135, ^bb15(%24 : i64), ^bb18
  ^bb15(%136: i64):  // 2 preds: ^bb14, ^bb16
    %137 = llvm.icmp "slt" %136, %31 : i64
    llvm.cond_br %137, ^bb16, ^bb17
  ^bb16:  // pred: ^bb15
    %138 = llvm.mul %132, %31 : i64
    %139 = llvm.add %138, %136 : i64
    %140 = llvm.add %100, %139 : i64
    %141 = llvm.add %39, %134 : i64
    %142 = llvm.extractvalue %15[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %143 = llvm.mlir.constant(256 : index) : i64
    %144 = llvm.mul %140, %143 : i64
    %145 = llvm.add %144, %141 : i64
    %146 = llvm.getelementptr %142[%145] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %147 = llvm.load %146 : !llvm.ptr -> f32
    %148 = llvm.extractvalue %131[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %149 = llvm.mlir.constant(384 : index) : i64
    %150 = llvm.mul %132, %149 : i64
    %151 = llvm.mlir.constant(6 : index) : i64
    %152 = llvm.mul %134, %151 : i64
    %153 = llvm.add %150, %152 : i64
    %154 = llvm.add %153, %136 : i64
    %155 = llvm.getelementptr %148[%154] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %147, %155 : f32, !llvm.ptr
    %156 = llvm.add %136, %25 : i64
    llvm.br ^bb15(%156 : i64)
  ^bb17:  // pred: ^bb15
    %157 = llvm.add %134, %25 : i64
    llvm.br ^bb14(%157 : i64)
  ^bb18:  // pred: ^bb14
    %158 = llvm.add %132, %25 : i64
    llvm.br ^bb13(%158 : i64)
  ^bb19:  // pred: ^bb13
    %159 = llvm.extractvalue %131[1] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    %160 = llvm.ptrtoint %159 : !llvm.ptr to i64
    %161 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %162 = llvm.ptrtoint %161 : !llvm.ptr to i64
    llvm.br ^bb20(%24 : i64)
  ^bb20(%163: i64):  // 2 preds: ^bb19, ^bb23
    %164 = llvm.icmp "slt" %163, %34 : i64
    llvm.cond_br %164, ^bb21(%24 : i64), ^bb24
  ^bb21(%165: i64):  // 2 preds: ^bb20, ^bb22
    %166 = llvm.icmp "slt" %165, %33 : i64
    llvm.cond_br %166, ^bb22, ^bb23
  ^bb22:  // pred: ^bb21
    %167 = llvm.mul %165, %35 : i64
    %168 = llvm.mul %163, %36 : i64
    %169 = llvm.mul %165, %31 : i64
    %170 = llvm.add %100, %169 : i64
    %171 = llvm.mul %163, %32 : i64
    %172 = llvm.add %37, %171 : i64
    %173 = llvm.mul %170, %27 : i64
    %174 = llvm.add %173, %172 : i64
    llvm.call @buddy_blis_sgemm_6x16(%30, %160, %167, %99, %168, %162, %174, %27, %25) : (i64, i64, i64, i64, i64, i64, i64, i64, i64) -> ()
    %175 = llvm.add %165, %25 : i64
    llvm.br ^bb21(%175 : i64)
  ^bb23:  // pred: ^bb21
    %176 = llvm.add %163, %25 : i64
    llvm.br ^bb20(%176 : i64)
  ^bb24:  // pred: ^bb20
    %177 = llvm.extractvalue %131[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.call @free(%177) : (!llvm.ptr) -> ()
    %178 = llvm.add %100, %28 : i64
    llvm.br ^bb11(%178 : i64)
  ^bb25:  // pred: ^bb11
    %179 = llvm.extractvalue %70[0] : !llvm.struct<(ptr, ptr, i64, array<3 x i64>, array<3 x i64>)> 
    llvm.call @free(%179) : (!llvm.ptr) -> ()
    %180 = llvm.add %39, %30 : i64
    llvm.br ^bb2(%180 : i64)
  ^bb26:  // pred: ^bb2
    %181 = llvm.add %37, %29 : i64
    llvm.br ^bb1(%181 : i64)
  ^bb27:  // pred: ^bb1
    llvm.return %23 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
  }
  llvm.func @_mlir_ciface_chapter5_direct_anchor(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: !llvm.ptr, %arg3: !llvm.ptr) attributes {llvm.emit_c_interface} {
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
    %24 = llvm.call @chapter5_direct_anchor(%1, %2, %3, %4, %5, %6, %7, %9, %10, %11, %12, %13, %14, %15, %17, %18, %19, %20, %21, %22, %23) : (!llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    llvm.store %24, %arg0 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>, !llvm.ptr
    llvm.return
  }
}

