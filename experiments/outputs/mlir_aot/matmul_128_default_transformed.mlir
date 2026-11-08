module {
  func.func @matmul_m128_k128_n128_f32(%arg0: memref<128x128xf32, strided<[?, ?], offset: ?>>, %arg1: memref<128x128xf32, strided<[?, ?], offset: ?>>, %arg2: memref<128x128xf32, strided<[?, ?], offset: ?>>) -> memref<128x128xf32, strided<[?, ?], offset: ?>> attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c128 = arith.constant 128 : index
    %c1 = arith.constant 1 : index
    scf.for %arg3 = %c0 to %c128 step %c1 {
      scf.for %arg4 = %c0 to %c128 step %c1 {
        scf.for %arg5 = %c0 to %c128 step %c1 {
          %0 = memref.load %arg0[%arg3, %arg5] : memref<128x128xf32, strided<[?, ?], offset: ?>>
          %1 = memref.load %arg1[%arg5, %arg4] : memref<128x128xf32, strided<[?, ?], offset: ?>>
          %2 = memref.load %arg2[%arg3, %arg4] : memref<128x128xf32, strided<[?, ?], offset: ?>>
          %3 = arith.mulf %0, %1 : f32
          %4 = arith.addf %2, %3 : f32
          memref.store %4, %arg2[%arg3, %arg4] : memref<128x128xf32, strided<[?, ?], offset: ?>>
        }
      }
    }
    return %arg2 : memref<128x128xf32, strided<[?, ?], offset: ?>>
  }
}

