#map = affine_map<(d0, d1, d2) -> (d0, d2)>
#map1 = affine_map<(d0, d1, d2) -> (d2, d1)>
#map2 = affine_map<(d0, d1, d2) -> (d0, d1)>
module {
  func.func @chapter5_fallback_vectorized(%arg0: memref<192x256xf32>, %arg1: memref<256x256xf32>, %arg2: memref<192x256xf32>) -> memref<192x256xf32> attributes {llvm.emit_c_interface} {
    %cst = arith.constant 0.000000e+00 : f32
    %c0 = arith.constant 0 : index
    %c192 = arith.constant 192 : index
    %c256 = arith.constant 256 : index
    %c24 = arith.constant 24 : index
    %c32 = arith.constant 32 : index
    %c64 = arith.constant 64 : index
    scf.for %arg3 = %c0 to %c192 step %c24 {
      scf.for %arg4 = %c0 to %c256 step %c32 {
        scf.for %arg5 = %c0 to %c256 step %c64 {
          %0 = vector.transfer_read %arg0[%arg3, %arg5], %cst {in_bounds = [true, true]} : memref<192x256xf32>, vector<24x64xf32>
          %1 = vector.transfer_read %arg1[%arg5, %arg4], %cst {in_bounds = [true, true]} : memref<256x256xf32>, vector<64x32xf32>
          %2 = vector.transfer_read %arg2[%arg3, %arg4], %cst {in_bounds = [true, true]} : memref<192x256xf32>, vector<24x32xf32>
          %3 = vector.contract {indexing_maps = [#map, #map1, #map2], iterator_types = ["parallel", "parallel", "reduction"], kind = #vector.kind<add>} %0, %1, %2 : vector<24x64xf32>, vector<64x32xf32> into vector<24x32xf32>
          vector.transfer_write %3, %arg2[%arg3, %arg4] {in_bounds = [true, true]} : vector<24x32xf32>, memref<192x256xf32>
        }
      }
    }
    return %arg2 : memref<192x256xf32>
  }
  module attributes {transform.with_named_sequence} {
  }
}

