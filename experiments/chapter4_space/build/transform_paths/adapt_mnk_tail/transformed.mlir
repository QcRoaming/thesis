#map = affine_map<(d0) -> (-d0 + 190, 24)>
#map1 = affine_map<(d0) -> (-d0 + 250, 32)>
#map2 = affine_map<(d0) -> (-d0 + 250, 64)>
module {
  func.func @chapter4_adapt_mnk_tail(%arg0: memref<190x250xf32>, %arg1: memref<250x250xf32>, %arg2: memref<190x250xf32>) -> memref<190x250xf32> attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c190 = arith.constant 190 : index
    %c250 = arith.constant 250 : index
    %c24 = arith.constant 24 : index
    %c32 = arith.constant 32 : index
    %c64 = arith.constant 64 : index
    scf.for %arg3 = %c0 to %c190 step %c24 {
      scf.for %arg4 = %c0 to %c250 step %c32 {
        scf.for %arg5 = %c0 to %c250 step %c64 {
          %0 = affine.min #map(%arg3)
          %1 = affine.min #map1(%arg4)
          %2 = affine.min #map2(%arg5)
          %subview = memref.subview %arg0[%arg3, %arg5] [%0, %2] [1, 1] : memref<190x250xf32> to memref<?x?xf32, strided<[250, 1], offset: ?>>
          %subview_0 = memref.subview %arg1[%arg5, %arg4] [%2, %1] [1, 1] : memref<250x250xf32> to memref<?x?xf32, strided<[250, 1], offset: ?>>
          %subview_1 = memref.subview %arg2[%arg3, %arg4] [%0, %1] [1, 1] : memref<190x250xf32> to memref<?x?xf32, strided<[250, 1], offset: ?>>
          linalg.matmul ins(%subview, %subview_0 : memref<?x?xf32, strided<[250, 1], offset: ?>>, memref<?x?xf32, strided<[250, 1], offset: ?>>) outs(%subview_1 : memref<?x?xf32, strided<[250, 1], offset: ?>>)
          memref.copy %subview_1, %subview_1 : memref<?x?xf32, strided<[250, 1], offset: ?>> to memref<?x?xf32, strided<[250, 1], offset: ?>>
        }
      }
    }
    return %arg2 : memref<190x250xf32>
  }
  module attributes {chapter4.template_path = "finite_tail_adapt_schedule", transform.with_named_sequence} {
  }
}

