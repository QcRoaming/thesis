#map = affine_map<(d0) -> (-d0 + 192, 168)>
#map1 = affine_map<(d0) -> (-d0 + 256, 192)>
module {
  func.func @chapter4_0050_m168_n192_k128_pab_v1(%arg0: memref<192x256xf32>, %arg1: memref<256x256xf32>, %arg2: memref<192x256xf32>) -> memref<192x256xf32> attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c192 = arith.constant 192 : index
    %c256 = arith.constant 256 : index
    %c168 = arith.constant 168 : index
    %c128 = arith.constant 128 : index
    scf.for %arg3 = %c0 to %c192 step %c168 {
      scf.for %arg4 = %c0 to %c256 step %c192 {
        scf.for %arg5 = %c0 to %c256 step %c128 {
          %0 = affine.min #map(%arg3)
          %1 = affine.min #map1(%arg4)
          %subview = memref.subview %arg0[%arg3, %arg5] [%0, 128] [1, 1] : memref<192x256xf32> to memref<?x128xf32, strided<[256, 1], offset: ?>>
          %subview_0 = memref.subview %arg1[%arg5, %arg4] [128, %1] [1, 1] : memref<256x256xf32> to memref<128x?xf32, strided<[256, 1], offset: ?>>
          %subview_1 = memref.subview %arg2[%arg3, %arg4] [%0, %1] [1, 1] : memref<192x256xf32> to memref<?x?xf32, strided<[256, 1], offset: ?>>
          linalg.matmul ins(%subview, %subview_0 : memref<?x128xf32, strided<[256, 1], offset: ?>>, memref<128x?xf32, strided<[256, 1], offset: ?>>) outs(%subview_1 : memref<?x?xf32, strided<[256, 1], offset: ?>>)
          memref.copy %subview_1, %subview_1 : memref<?x?xf32, strided<[256, 1], offset: ?>> to memref<?x?xf32, strided<[256, 1], offset: ?>>
        }
      }
    }
    return %arg2 : memref<192x256xf32>
  }
  module attributes {chapter4.template_path = "contract_direct_schedule", transform.with_named_sequence} {
  }
}

