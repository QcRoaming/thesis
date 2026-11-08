#map = affine_map<(d0) -> (-d0 + 192, 168)>
module {
  func.func @chapter4_0000_m168_n256_k256_pab_v1(%arg0: memref<192x256xf32>, %arg1: memref<256x256xf32>, %arg2: memref<192x256xf32>) -> memref<192x256xf32> attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c192 = arith.constant 192 : index
    %c168 = arith.constant 168 : index
    scf.for %arg3 = %c0 to %c192 step %c168 {
      %0 = affine.min #map(%arg3)
      %subview = memref.subview %arg0[%arg3, 0] [%0, 256] [1, 1] : memref<192x256xf32> to memref<?x256xf32, strided<[256, 1], offset: ?>>
      %subview_0 = memref.subview %arg2[%arg3, 0] [%0, 256] [1, 1] : memref<192x256xf32> to memref<?x256xf32, strided<[256, 1], offset: ?>>
      linalg.matmul ins(%subview, %arg1 : memref<?x256xf32, strided<[256, 1], offset: ?>>, memref<256x256xf32>) outs(%subview_0 : memref<?x256xf32, strided<[256, 1], offset: ?>>)
      memref.copy %subview_0, %subview_0 : memref<?x256xf32, strided<[256, 1], offset: ?>> to memref<?x256xf32, strided<[256, 1], offset: ?>>
    }
    return %arg2 : memref<192x256xf32>
  }
  module attributes {chapter4.template_path = "contract_direct_schedule", transform.with_named_sequence} {
  }
}

