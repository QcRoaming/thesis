module {
  func.func private @buddy_blis_sgemm_6x16_fringe(index, index, index, index, index, index, index, index, index)
  func.func private @buddy_blis_sgemm_6x16(index, index, index, index, index, index, index, index, index)
  func.func private @buddy_microkernel_fringe_placeholder(index, index, index, index, index, index, index, index, index)
  func.func private @buddy_microkernel_placeholder(index, index, index, index, index, index, index, index, index)
  func.func @chapter5_fringe_dev(%arg0: memref<19x65xf32>, %arg1: memref<65x17xf32>, %arg2: memref<19x17xf32>) -> memref<19x17xf32> attributes {llvm.emit_c_interface} {
    %c102 = arith.constant 102 : index
    %c4 = arith.constant 4 : index
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c19 = arith.constant 19 : index
    %c65 = arith.constant 65 : index
    %c17 = arith.constant 17 : index
    %c64 = arith.constant 64 : index
    %c6 = arith.constant 6 : index
    %c16 = arith.constant 16 : index
    %c384 = arith.constant 384 : index
    %c1024 = arith.constant 1024 : index
    %cst = arith.constant 0.000000e+00 : f32
    %c2 = arith.constant 2 : index
    scf.for %arg3 = %c0 to %c65 step %c64 {
      %0 = arith.subi %c65, %arg3 : index
      %1 = arith.minui %0, %c64 : index
      %alloc = memref.alloc() {alignment = 64 : i64} : memref<2x64x16xf32>
      scf.for %arg4 = %c0 to %c2 step %c1 {
        scf.for %arg5 = %c0 to %c64 step %c1 {
          scf.for %arg6 = %c0 to %c16 step %c1 {
            %2 = arith.addi %arg3, %arg5 : index
            %3 = arith.muli %arg4, %c16 : index
            %4 = arith.addi %3, %arg6 : index
            %5 = arith.cmpi ult, %2, %c65 : index
            %6 = arith.cmpi ult, %4, %c17 : index
            %7 = arith.andi %5, %6 : i1
            %8 = scf.if %7 -> (f32) {
              %9 = memref.load %arg1[%2, %4] : memref<65x17xf32>
              scf.yield %9 : f32
            } else {
              scf.yield %cst : f32
            }
            memref.store %8, %alloc[%arg4, %arg5, %arg6] : memref<2x64x16xf32>
          }
        }
      }
      %intptr = memref.extract_aligned_pointer_as_index %alloc : memref<2x64x16xf32> -> index
      %alloc_0 = memref.alloc() {alignment = 64 : i64} : memref<4x64x6xf32>
      scf.for %arg4 = %c0 to %c4 step %c1 {
        scf.for %arg5 = %c0 to %c64 step %c1 {
          scf.for %arg6 = %c0 to %c6 step %c1 {
            %2 = arith.muli %arg4, %c6 : index
            %3 = arith.addi %2, %arg6 : index
            %4 = arith.addi %arg3, %arg5 : index
            %5 = arith.cmpi ult, %3, %c19 : index
            %6 = arith.cmpi ult, %4, %c65 : index
            %7 = arith.andi %5, %6 : i1
            %8 = scf.if %7 -> (f32) {
              %9 = memref.load %arg0[%3, %4] : memref<19x65xf32>
              scf.yield %9 : f32
            } else {
              scf.yield %cst : f32
            }
            memref.store %8, %alloc_0[%arg4, %arg5, %arg6] : memref<4x64x6xf32>
          }
        }
      }
      %intptr_1 = memref.extract_aligned_pointer_as_index %alloc_0 : memref<4x64x6xf32> -> index
      %intptr_2 = memref.extract_aligned_pointer_as_index %arg2 : memref<19x17xf32> -> index
      scf.for %arg4 = %c0 to %c2 step %c1 {
        scf.for %arg5 = %c0 to %c4 step %c1 {
          %2 = arith.muli %arg5, %c384 : index
          %3 = arith.muli %arg4, %c1024 : index
          %4 = arith.muli %arg5, %c6 : index
          %5 = arith.muli %arg4, %c16 : index
          %6 = arith.subi %c19, %4 : index
          %7 = arith.minui %6, %c6 : index
          %8 = arith.subi %c17, %5 : index
          %9 = arith.minui %8, %c16 : index
          %10 = arith.cmpi eq, %7, %c6 : index
          %11 = arith.cmpi eq, %9, %c16 : index
          %12 = arith.andi %10, %11 : i1
          scf.if %12 {
            %13 = arith.muli %arg5, %c102 : index
            %14 = arith.addi %13, %5 : index
            func.call @buddy_blis_sgemm_6x16(%1, %intptr_1, %2, %intptr, %3, %intptr_2, %14, %c17, %c1) : (index, index, index, index, index, index, index, index, index) -> ()
          } else {
            %alloc_3 = memref.alloc() {alignment = 64 : i64} : memref<6x16xf32>
            scf.for %arg6 = %c0 to %c6 step %c1 {
              scf.for %arg7 = %c0 to %c16 step %c1 {
                %13 = arith.cmpi ult, %arg6, %7 : index
                %14 = arith.cmpi ult, %arg7, %9 : index
                %15 = arith.addi %4, %arg6 : index
                %16 = arith.addi %5, %arg7 : index
                %17 = arith.andi %13, %14 : i1
                %18 = scf.if %17 -> (f32) {
                  %19 = memref.load %arg2[%15, %16] : memref<19x17xf32>
                  scf.yield %19 : f32
                } else {
                  scf.yield %cst : f32
                }
                memref.store %18, %alloc_3[%arg6, %arg7] : memref<6x16xf32>
              }
            }
            %intptr_4 = memref.extract_aligned_pointer_as_index %alloc_3 : memref<6x16xf32> -> index
            func.call @buddy_blis_sgemm_6x16_fringe(%1, %intptr_1, %2, %intptr, %3, %intptr_4, %c0, %c16, %c1) : (index, index, index, index, index, index, index, index, index) -> ()
            scf.for %arg6 = %c0 to %7 step %c1 {
              scf.for %arg7 = %c0 to %9 step %c1 {
                %13 = memref.load %alloc_3[%arg6, %arg7] : memref<6x16xf32>
                %14 = arith.addi %4, %arg6 : index
                %15 = arith.addi %5, %arg7 : index
                memref.store %13, %arg2[%14, %15] : memref<19x17xf32>
              }
            }
            memref.dealloc %alloc_3 : memref<6x16xf32>
          }
        }
      }
      memref.dealloc %alloc_0 : memref<4x64x6xf32>
      memref.dealloc %alloc : memref<2x64x16xf32>
    }
    return %arg2 : memref<19x17xf32>
  }
}

