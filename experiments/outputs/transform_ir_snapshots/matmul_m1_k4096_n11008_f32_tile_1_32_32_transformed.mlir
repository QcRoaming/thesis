#map = affine_map<(d0, d1, d2) -> (d0, d2)>
#map1 = affine_map<(d0, d1, d2) -> (d2, d1)>
#map2 = affine_map<(d0, d1, d2) -> (d0, d1)>
module {
  func.func @matmul_m1_k4096_n11008_f32(%arg0: memref<1x4096xf32>, %arg1: memref<4096x11008xf32>, %arg2: memref<1x11008xf32>) -> memref<1x11008xf32> attributes {llvm.emit_c_interface} {
    %cst = arith.constant 0.000000e+00 : f32
    %c0 = arith.constant 0 : index
    %c11008 = arith.constant 11008 : index
    %c4096 = arith.constant 4096 : index
    %c32 = arith.constant 32 : index
    scf.for %arg3 = %c0 to %c11008 step %c32 {
      scf.for %arg4 = %c0 to %c4096 step %c32 {
        %0 = vector.transfer_read %arg0[%c0, %arg4], %cst {in_bounds = [true, true]} : memref<1x4096xf32>, vector<1x32xf32>
        %1 = vector.transfer_read %arg1[%arg4, %arg3], %cst {in_bounds = [true, true]} : memref<4096x11008xf32>, vector<32x32xf32>
        %2 = vector.transfer_read %arg2[%c0, %arg3], %cst {in_bounds = [true, true]} : memref<1x11008xf32>, vector<1x32xf32>
        %3 = vector.contract {indexing_maps = [#map, #map1, #map2], iterator_types = ["parallel", "parallel", "reduction"], kind = #vector.kind<add>} %0, %1, %2 : vector<1x32xf32>, vector<32x32xf32> into vector<1x32xf32>
        vector.transfer_write %3, %arg2[%c0, %arg3] {in_bounds = [true, true]} : vector<1x32xf32>, memref<1x11008xf32>
      }
    }
    return %arg2 : memref<1x11008xf32>
  }
  module attributes {transform.with_named_sequence} {
  }
}

