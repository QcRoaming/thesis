#map = affine_map<(d0)[s0] -> (-d0 + s0, 24)>
#map1 = affine_map<(d0)[s0] -> (-d0 + s0, 32)>
#map2 = affine_map<(d0)[s0] -> (-d0 + s0, 64)>
module {
  func.func @integrated_feature_mismatch_192x256x256_f32_m24_n32_k64_pnone_v0(%arg0: memref<?x?xf32>, %arg1: memref<?x?xf32>, %arg2: memref<?x?xf32>) -> memref<?x?xf32> attributes {llvm.emit_c_interface} {
    %c64 = arith.constant 64 : index
    %c32 = arith.constant 32 : index
    %c24 = arith.constant 24 : index
    %c1 = arith.constant 1 : index
    %c0 = arith.constant 0 : index
    %dim = memref.dim %arg0, %c0 : memref<?x?xf32>
    %dim_0 = memref.dim %arg0, %c1 : memref<?x?xf32>
    %dim_1 = memref.dim %arg1, %c1 : memref<?x?xf32>
    scf.for %arg3 = %c0 to %dim step %c24 {
      scf.for %arg4 = %c0 to %dim_1 step %c32 {
        scf.for %arg5 = %c0 to %dim_0 step %c64 {
          %0 = affine.min #map(%arg3)[%dim]
          %1 = affine.min #map1(%arg4)[%dim_1]
          %2 = affine.min #map2(%arg5)[%dim_0]
          %subview = memref.subview %arg0[%arg3, %arg5] [%0, %2] [1, 1] : memref<?x?xf32> to memref<?x?xf32, strided<[?, 1], offset: ?>>
          %subview_2 = memref.subview %arg1[%arg5, %arg4] [%2, %1] [1, 1] : memref<?x?xf32> to memref<?x?xf32, strided<[?, 1], offset: ?>>
          %subview_3 = memref.subview %arg2[%arg3, %arg4] [%0, %1] [1, 1] : memref<?x?xf32> to memref<?x?xf32, strided<[?, 1], offset: ?>>
          linalg.matmul ins(%subview, %subview_2 : memref<?x?xf32, strided<[?, 1], offset: ?>>, memref<?x?xf32, strided<[?, 1], offset: ?>>) outs(%subview_3 : memref<?x?xf32, strided<[?, 1], offset: ?>>)
          memref.copy %subview_3, %subview_3 : memref<?x?xf32, strided<[?, 1], offset: ?>> to memref<?x?xf32, strided<[?, 1], offset: ?>>
        }
      }
    }
    return %arg2 : memref<?x?xf32>
  }
  module attributes {transform.with_named_sequence} {
  }
}

