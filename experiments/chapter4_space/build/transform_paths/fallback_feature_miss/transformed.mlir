module {
  func.func @chapter4_fallback_feature_miss(%arg0: memref<192x256xf32>, %arg1: memref<256x256xf32>, %arg2: memref<192x256xf32>) -> memref<192x256xf32> attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c192 = arith.constant 192 : index
    %c256 = arith.constant 256 : index
    %c24 = arith.constant 24 : index
    %c32 = arith.constant 32 : index
    %c64 = arith.constant 64 : index
    scf.for %arg3 = %c0 to %c192 step %c24 {
      scf.for %arg4 = %c0 to %c256 step %c32 {
        scf.for %arg5 = %c0 to %c256 step %c64 {
          %subview = memref.subview %arg0[%arg3, %arg5] [24, 64] [1, 1] : memref<192x256xf32> to memref<24x64xf32, strided<[256, 1], offset: ?>>
          %subview_0 = memref.subview %arg1[%arg5, %arg4] [64, 32] [1, 1] : memref<256x256xf32> to memref<64x32xf32, strided<[256, 1], offset: ?>>
          %subview_1 = memref.subview %arg2[%arg3, %arg4] [24, 32] [1, 1] : memref<192x256xf32> to memref<24x32xf32, strided<[256, 1], offset: ?>>
          linalg.matmul ins(%subview, %subview_0 : memref<24x64xf32, strided<[256, 1], offset: ?>>, memref<64x32xf32, strided<[256, 1], offset: ?>>) outs(%subview_1 : memref<24x32xf32, strided<[256, 1], offset: ?>>)
          memref.copy %subview_1, %subview_1 : memref<24x32xf32, strided<[256, 1], offset: ?>> to memref<24x32xf32, strided<[256, 1], offset: ?>>
        }
      }
    }
    return %arg2 : memref<192x256xf32>
  }
  module attributes {chapter4.template_path = "generic_fallback_schedule", transform.with_named_sequence} {
  }
}

