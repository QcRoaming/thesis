module {
  func.func private @buddy_blis_sgemm_6x16_fringe(index, index, index, index, index, index, index, index, index)
  func.func private @buddy_blis_sgemm_6x16(index, index, index, index, index, index, index, index, index)
  func.func private @buddy_microkernel_fringe_placeholder(index, index, index, index, index, index, index, index, index)
  func.func private @buddy_microkernel_placeholder(index, index, index, index, index, index, index, index, index)
  func.func @cgo_f32_m24_n256_k256_pab_v0(%arg0: memref<?x?xf32>, %arg1: memref<?x?xf32>, %arg2: memref<?x?xf32>) -> memref<?x?xf32> attributes {llvm.emit_c_interface} {
    %cst = arith.constant 0.000000e+00 : f32
    %c4096 = arith.constant 4096 : index
    %c1536 = arith.constant 1536 : index
    %c16 = arith.constant 16 : index
    %c6 = arith.constant 6 : index
    %c256 = arith.constant 256 : index
    %c24 = arith.constant 24 : index
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %dim = memref.dim %arg0, %c0 : memref<?x?xf32>
    %dim_0 = memref.dim %arg0, %c1 : memref<?x?xf32>
    %dim_1 = memref.dim %arg1, %c1 : memref<?x?xf32>
    scf.for %arg3 = %c0 to %dim_1 step %c256 {
      %0 = arith.subi %dim_1, %arg3 : index
      %1 = arith.minui %0, %c256 : index
      %2 = arith.ceildivui %1, %c16 : index
      scf.for %arg4 = %c0 to %dim_0 step %c256 {
        %3 = arith.subi %dim_0, %arg4 : index
        %4 = arith.minui %3, %c256 : index
        %alloc = memref.alloc() {alignment = 64 : i64} : memref<16x256x16xf32>
        scf.for %arg5 = %c0 to %2 step %c1 {
          scf.for %arg6 = %c0 to %c256 step %c1 {
            scf.for %arg7 = %c0 to %c16 step %c1 {
              %5 = arith.addi %arg4, %arg6 : index
              %6 = arith.muli %arg5, %c16 : index
              %7 = arith.addi %6, %arg7 : index
              %8 = arith.addi %arg3, %7 : index
              %9 = arith.cmpi ult, %5, %dim_0 : index
              %10 = arith.cmpi ult, %8, %dim_1 : index
              %11 = arith.andi %9, %10 : i1
              %12 = scf.if %11 -> (f32) {
                %13 = memref.load %arg1[%5, %8] : memref<?x?xf32>
                scf.yield %13 : f32
              } else {
                scf.yield %cst : f32
              }
              memref.store %12, %alloc[%arg5, %arg6, %arg7] : memref<16x256x16xf32>
            }
          }
        }
        %intptr = memref.extract_aligned_pointer_as_index %alloc : memref<16x256x16xf32> -> index
        scf.for %arg5 = %c0 to %dim step %c24 {
          %5 = arith.subi %dim, %arg5 : index
          %6 = arith.minui %5, %c24 : index
          %7 = arith.ceildivui %6, %c6 : index
          %alloc_2 = memref.alloc() {alignment = 64 : i64} : memref<4x256x6xf32>
          scf.for %arg6 = %c0 to %7 step %c1 {
            scf.for %arg7 = %c0 to %c256 step %c1 {
              scf.for %arg8 = %c0 to %c6 step %c1 {
                %8 = arith.muli %arg6, %c6 : index
                %9 = arith.addi %8, %arg8 : index
                %10 = arith.addi %arg5, %9 : index
                %11 = arith.addi %arg4, %arg7 : index
                %12 = arith.cmpi ult, %10, %dim : index
                %13 = arith.cmpi ult, %11, %dim_0 : index
                %14 = arith.andi %12, %13 : i1
                %15 = scf.if %14 -> (f32) {
                  %16 = memref.load %arg0[%10, %11] : memref<?x?xf32>
                  scf.yield %16 : f32
                } else {
                  scf.yield %cst : f32
                }
                memref.store %15, %alloc_2[%arg6, %arg7, %arg8] : memref<4x256x6xf32>
              }
            }
          }
          %intptr_3 = memref.extract_aligned_pointer_as_index %alloc_2 : memref<4x256x6xf32> -> index
          %intptr_4 = memref.extract_aligned_pointer_as_index %arg2 : memref<?x?xf32> -> index
          scf.for %arg6 = %c0 to %2 step %c1 {
            scf.for %arg7 = %c0 to %7 step %c1 {
              %8 = arith.muli %arg7, %c1536 : index
              %9 = arith.muli %arg6, %c4096 : index
              %10 = arith.muli %arg7, %c6 : index
              %11 = arith.addi %arg5, %10 : index
              %12 = arith.muli %arg6, %c16 : index
              %13 = arith.addi %arg3, %12 : index
              %14 = arith.subi %dim, %11 : index
              %15 = arith.minui %14, %c6 : index
              %16 = arith.subi %dim_1, %13 : index
              %17 = arith.minui %16, %c16 : index
              %18 = arith.cmpi eq, %15, %c6 : index
              %19 = arith.cmpi eq, %17, %c16 : index
              %20 = arith.andi %18, %19 : i1
              scf.if %20 {
                %21 = arith.muli %11, %dim_1 : index
                %22 = arith.addi %21, %13 : index
                func.call @buddy_blis_sgemm_6x16(%4, %intptr_3, %8, %intptr, %9, %intptr_4, %22, %dim_1, %c1) : (index, index, index, index, index, index, index, index, index) -> ()
              } else {
                %alloc_5 = memref.alloc() {alignment = 64 : i64} : memref<6x16xf32>
                scf.for %arg8 = %c0 to %c6 step %c1 {
                  scf.for %arg9 = %c0 to %c16 step %c1 {
                    %21 = arith.cmpi ult, %arg8, %15 : index
                    %22 = arith.cmpi ult, %arg9, %17 : index
                    %23 = arith.addi %11, %arg8 : index
                    %24 = arith.addi %13, %arg9 : index
                    %25 = arith.andi %21, %22 : i1
                    %26 = scf.if %25 -> (f32) {
                      %27 = memref.load %arg2[%23, %24] : memref<?x?xf32>
                      scf.yield %27 : f32
                    } else {
                      scf.yield %cst : f32
                    }
                    memref.store %26, %alloc_5[%arg8, %arg9] : memref<6x16xf32>
                  }
                }
                %intptr_6 = memref.extract_aligned_pointer_as_index %alloc_5 : memref<6x16xf32> -> index
                func.call @buddy_blis_sgemm_6x16_fringe(%4, %intptr_3, %8, %intptr, %9, %intptr_6, %c0, %c16, %c1) : (index, index, index, index, index, index, index, index, index) -> ()
                scf.for %arg8 = %c0 to %15 step %c1 {
                  scf.for %arg9 = %c0 to %17 step %c1 {
                    %21 = memref.load %alloc_5[%arg8, %arg9] : memref<6x16xf32>
                    %22 = arith.addi %11, %arg8 : index
                    %23 = arith.addi %13, %arg9 : index
                    memref.store %21, %arg2[%22, %23] : memref<?x?xf32>
                  }
                }
                memref.dealloc %alloc_5 : memref<6x16xf32>
              }
            }
          }
          memref.dealloc %alloc_2 : memref<4x256x6xf32>
        }
        memref.dealloc %alloc : memref<16x256x16xf32>
      }
    }
    return %arg2 : memref<?x?xf32>
  }
}

