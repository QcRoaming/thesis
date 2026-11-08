module {
  llvm.func @chapter4_adapt_mnk_tail(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: i64, %arg3: i64, %arg4: i64, %arg5: i64, %arg6: i64, %arg7: !llvm.ptr, %arg8: !llvm.ptr, %arg9: i64, %arg10: i64, %arg11: i64, %arg12: i64, %arg13: i64, %arg14: !llvm.ptr, %arg15: !llvm.ptr, %arg16: i64, %arg17: i64, %arg18: i64, %arg19: i64, %arg20: i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> attributes {llvm.emit_c_interface} {
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
    %24 = llvm.mlir.constant(1 : index) : i64
    %25 = llvm.mlir.constant(0 : index) : i64
    %26 = llvm.mlir.constant(190 : index) : i64
    %27 = llvm.mlir.constant(250 : index) : i64
    %28 = llvm.mlir.constant(24 : index) : i64
    %29 = llvm.mlir.constant(32 : index) : i64
    %30 = llvm.mlir.constant(64 : index) : i64
    llvm.br ^bb1(%25 : i64)
  ^bb1(%31: i64):  // 2 preds: ^bb0, ^bb13
    %32 = llvm.icmp "slt" %31, %26 : i64
    llvm.cond_br %32, ^bb2(%25 : i64), ^bb14
  ^bb2(%33: i64):  // 2 preds: ^bb1, ^bb12
    %34 = llvm.icmp "slt" %33, %27 : i64
    llvm.cond_br %34, ^bb3(%25 : i64), ^bb13
  ^bb3(%35: i64):  // 2 preds: ^bb2, ^bb11
    %36 = llvm.icmp "slt" %35, %27 : i64
    llvm.cond_br %36, ^bb4, ^bb12
  ^bb4:  // pred: ^bb3
    %37 = llvm.sub %26, %31 : i64
    %38 = llvm.intr.smin(%37, %28) : (i64, i64) -> i64
    %39 = llvm.sub %27, %33 : i64
    %40 = llvm.intr.smin(%39, %29) : (i64, i64) -> i64
    %41 = llvm.sub %27, %35 : i64
    %42 = llvm.intr.smin(%41, %30) : (i64, i64) -> i64
    %43 = llvm.extractvalue %15[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %44 = llvm.extractvalue %15[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %45 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64)>
    %46 = llvm.insertvalue %43, %45[0] : !llvm.struct<(ptr, ptr, i64)> 
    %47 = llvm.insertvalue %44, %46[1] : !llvm.struct<(ptr, ptr, i64)> 
    %48 = llvm.mlir.constant(0 : index) : i64
    %49 = llvm.insertvalue %48, %47[2] : !llvm.struct<(ptr, ptr, i64)> 
    %50 = llvm.extractvalue %15[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %51 = llvm.extractvalue %15[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %52 = llvm.extractvalue %15[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %53 = llvm.extractvalue %15[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %54 = llvm.extractvalue %15[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %55 = llvm.mlir.constant(250 : index) : i64
    %56 = llvm.mul %31, %55 overflow<nsw> : i64
    %57 = llvm.add %56, %35 : i64
    %58 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %59 = llvm.extractvalue %49[0] : !llvm.struct<(ptr, ptr, i64)> 
    %60 = llvm.extractvalue %49[1] : !llvm.struct<(ptr, ptr, i64)> 
    %61 = llvm.insertvalue %59, %58[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %62 = llvm.insertvalue %60, %61[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %63 = llvm.insertvalue %57, %62[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %64 = llvm.insertvalue %38, %63[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %65 = llvm.mlir.constant(250 : index) : i64
    %66 = llvm.insertvalue %65, %64[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %67 = llvm.insertvalue %42, %66[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %68 = llvm.mlir.constant(1 : index) : i64
    %69 = llvm.insertvalue %68, %67[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %70 = llvm.extractvalue %7[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %71 = llvm.extractvalue %7[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %72 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64)>
    %73 = llvm.insertvalue %70, %72[0] : !llvm.struct<(ptr, ptr, i64)> 
    %74 = llvm.insertvalue %71, %73[1] : !llvm.struct<(ptr, ptr, i64)> 
    %75 = llvm.mlir.constant(0 : index) : i64
    %76 = llvm.insertvalue %75, %74[2] : !llvm.struct<(ptr, ptr, i64)> 
    %77 = llvm.extractvalue %7[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %78 = llvm.extractvalue %7[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %79 = llvm.extractvalue %7[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %80 = llvm.extractvalue %7[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %81 = llvm.extractvalue %7[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %82 = llvm.mlir.constant(250 : index) : i64
    %83 = llvm.mul %35, %82 overflow<nsw> : i64
    %84 = llvm.add %83, %33 : i64
    %85 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %86 = llvm.extractvalue %76[0] : !llvm.struct<(ptr, ptr, i64)> 
    %87 = llvm.extractvalue %76[1] : !llvm.struct<(ptr, ptr, i64)> 
    %88 = llvm.insertvalue %86, %85[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %89 = llvm.insertvalue %87, %88[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %90 = llvm.insertvalue %84, %89[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %91 = llvm.insertvalue %42, %90[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %92 = llvm.mlir.constant(250 : index) : i64
    %93 = llvm.insertvalue %92, %91[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %94 = llvm.insertvalue %40, %93[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %95 = llvm.mlir.constant(1 : index) : i64
    %96 = llvm.insertvalue %95, %94[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %97 = llvm.extractvalue %23[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %98 = llvm.extractvalue %23[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %99 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64)>
    %100 = llvm.insertvalue %97, %99[0] : !llvm.struct<(ptr, ptr, i64)> 
    %101 = llvm.insertvalue %98, %100[1] : !llvm.struct<(ptr, ptr, i64)> 
    %102 = llvm.mlir.constant(0 : index) : i64
    %103 = llvm.insertvalue %102, %101[2] : !llvm.struct<(ptr, ptr, i64)> 
    %104 = llvm.extractvalue %23[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %105 = llvm.extractvalue %23[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %106 = llvm.extractvalue %23[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %107 = llvm.extractvalue %23[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %108 = llvm.extractvalue %23[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %109 = llvm.mlir.constant(250 : index) : i64
    %110 = llvm.mul %31, %109 overflow<nsw> : i64
    %111 = llvm.add %110, %33 : i64
    %112 = llvm.mlir.undef : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    %113 = llvm.extractvalue %103[0] : !llvm.struct<(ptr, ptr, i64)> 
    %114 = llvm.extractvalue %103[1] : !llvm.struct<(ptr, ptr, i64)> 
    %115 = llvm.insertvalue %113, %112[0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %116 = llvm.insertvalue %114, %115[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %117 = llvm.insertvalue %111, %116[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %118 = llvm.insertvalue %38, %117[3, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %119 = llvm.mlir.constant(250 : index) : i64
    %120 = llvm.insertvalue %119, %118[4, 0] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %121 = llvm.insertvalue %40, %120[3, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %122 = llvm.mlir.constant(1 : index) : i64
    %123 = llvm.insertvalue %122, %121[4, 1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    llvm.br ^bb5(%25 : i64)
  ^bb5(%124: i64):  // 2 preds: ^bb4, ^bb10
    %125 = llvm.icmp "slt" %124, %38 : i64
    llvm.cond_br %125, ^bb6(%25 : i64), ^bb11
  ^bb6(%126: i64):  // 2 preds: ^bb5, ^bb9
    %127 = llvm.icmp "slt" %126, %40 : i64
    llvm.cond_br %127, ^bb7(%25 : i64), ^bb10
  ^bb7(%128: i64):  // 2 preds: ^bb6, ^bb8
    %129 = llvm.icmp "slt" %128, %42 : i64
    llvm.cond_br %129, ^bb8, ^bb9
  ^bb8:  // pred: ^bb7
    %130 = llvm.extractvalue %69[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %131 = llvm.extractvalue %69[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %132 = llvm.getelementptr %130[%131] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %133 = llvm.mlir.constant(250 : index) : i64
    %134 = llvm.mul %124, %133 : i64
    %135 = llvm.add %134, %128 : i64
    %136 = llvm.getelementptr %132[%135] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %137 = llvm.load %136 : !llvm.ptr -> f32
    %138 = llvm.extractvalue %96[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %139 = llvm.extractvalue %96[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %140 = llvm.getelementptr %138[%139] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %141 = llvm.mlir.constant(250 : index) : i64
    %142 = llvm.mul %128, %141 : i64
    %143 = llvm.add %142, %126 : i64
    %144 = llvm.getelementptr %140[%143] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %145 = llvm.load %144 : !llvm.ptr -> f32
    %146 = llvm.extractvalue %123[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %147 = llvm.extractvalue %123[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %148 = llvm.getelementptr %146[%147] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %149 = llvm.mlir.constant(250 : index) : i64
    %150 = llvm.mul %124, %149 : i64
    %151 = llvm.add %150, %126 : i64
    %152 = llvm.getelementptr %148[%151] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %153 = llvm.load %152 : !llvm.ptr -> f32
    %154 = llvm.fmul %137, %145 : f32
    %155 = llvm.fadd %153, %154 : f32
    %156 = llvm.extractvalue %123[1] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %157 = llvm.extractvalue %123[2] : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)> 
    %158 = llvm.getelementptr %156[%157] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    %159 = llvm.mlir.constant(250 : index) : i64
    %160 = llvm.mul %124, %159 : i64
    %161 = llvm.add %160, %126 : i64
    %162 = llvm.getelementptr %158[%161] : (!llvm.ptr, i64) -> !llvm.ptr, f32
    llvm.store %155, %162 : f32, !llvm.ptr
    %163 = llvm.add %128, %24 : i64
    llvm.br ^bb7(%163 : i64)
  ^bb9:  // pred: ^bb7
    %164 = llvm.add %126, %24 : i64
    llvm.br ^bb6(%164 : i64)
  ^bb10:  // pred: ^bb6
    %165 = llvm.add %124, %24 : i64
    llvm.br ^bb5(%165 : i64)
  ^bb11:  // pred: ^bb5
    %166 = llvm.add %35, %30 : i64
    llvm.br ^bb3(%166 : i64)
  ^bb12:  // pred: ^bb3
    %167 = llvm.add %33, %29 : i64
    llvm.br ^bb2(%167 : i64)
  ^bb13:  // pred: ^bb2
    %168 = llvm.add %31, %28 : i64
    llvm.br ^bb1(%168 : i64)
  ^bb14:  // pred: ^bb1
    llvm.return %23 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
  }
  llvm.func @_mlir_ciface_chapter4_adapt_mnk_tail(%arg0: !llvm.ptr, %arg1: !llvm.ptr, %arg2: !llvm.ptr, %arg3: !llvm.ptr) attributes {llvm.emit_c_interface} {
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
    %24 = llvm.call @chapter4_adapt_mnk_tail(%1, %2, %3, %4, %5, %6, %7, %9, %10, %11, %12, %13, %14, %15, %17, %18, %19, %20, %21, %22, %23) : (!llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64, !llvm.ptr, !llvm.ptr, i64, i64, i64, i64, i64) -> !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>
    llvm.store %24, %arg0 : !llvm.struct<(ptr, ptr, i64, array<2 x i64>, array<2 x i64>)>, !llvm.ptr
    llvm.return
  }
  module attributes {chapter4.template_path = "finite_tail_adapt_schedule", transform.with_named_sequence} {
  }
}

