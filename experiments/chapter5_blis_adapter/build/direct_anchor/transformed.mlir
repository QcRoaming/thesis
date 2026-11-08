module {
  func.func private @buddy_blis_sgemm_6x16(index, index, index, index, index, index, index, index, index)
  func.func private @buddy_microkernel_placeholder(index, index, index, index, index, index, index, index, index)
  func.func @chapter5_direct_anchor(%arg0: memref<192x256xf32>, %arg1: memref<256x256xf32>, %arg2: memref<192x256xf32>) -> memref<192x256xf32> attributes {llvm.emit_c_interface} {
    %c0 = arith.constant 0 : index
    %c1 = arith.constant 1 : index
    %c192 = arith.constant 192 : index
    %c256 = arith.constant 256 : index
    %c24 = arith.constant 24 : index
    %c32 = arith.constant 32 : index
    %c64 = arith.constant 64 : index
    %c6 = arith.constant 6 : index
    %c16 = arith.constant 16 : index
    %c4 = arith.constant 4 : index
    %c2 = arith.constant 2 : index
    %c384 = arith.constant 384 : index
    %c1024 = arith.constant 1024 : index
    scf.for %arg3 = %c0 to %c256 step %c32 {
      scf.for %arg4 = %c0 to %c256 step %c64 {
        %alloc = memref.alloc() {alignment = 64 : i64} : memref<2x64x16xf32>
        scf.for %arg5 = %c0 to %c2 step %c1 {
          scf.for %arg6 = %c0 to %c64 step %c1 {
            scf.for %arg7 = %c0 to %c16 step %c1 {
              %0 = arith.addi %arg4, %arg6 : index
              %1 = arith.muli %arg5, %c16 : index
              %2 = arith.addi %1, %arg7 : index
              %3 = arith.addi %arg3, %2 : index
              %4 = memref.load %arg1[%0, %3] : memref<256x256xf32>
              memref.store %4, %alloc[%arg5, %arg6, %arg7] : memref<2x64x16xf32>
            }
          }
        }
        %intptr = memref.extract_aligned_pointer_as_index %alloc : memref<2x64x16xf32> -> index
        scf.for %arg5 = %c0 to %c192 step %c24 {
          %alloc_0 = memref.alloc() {alignment = 64 : i64} : memref<4x64x6xf32>
          scf.for %arg6 = %c0 to %c4 step %c1 {
            scf.for %arg7 = %c0 to %c64 step %c1 {
              scf.for %arg8 = %c0 to %c6 step %c1 {
                %0 = arith.muli %arg6, %c6 : index
                %1 = arith.addi %0, %arg8 : index
                %2 = arith.addi %arg5, %1 : index
                %3 = arith.addi %arg4, %arg7 : index
                %4 = memref.load %arg0[%2, %3] : memref<192x256xf32>
                memref.store %4, %alloc_0[%arg6, %arg7, %arg8] : memref<4x64x6xf32>
              }
            }
          }
          %intptr_1 = memref.extract_aligned_pointer_as_index %alloc_0 : memref<4x64x6xf32> -> index
          %intptr_2 = memref.extract_aligned_pointer_as_index %arg2 : memref<192x256xf32> -> index
          scf.for %arg6 = %c0 to %c2 step %c1 {
            scf.for %arg7 = %c0 to %c4 step %c1 {
              %0 = arith.muli %arg7, %c384 : index
              %1 = arith.muli %arg6, %c1024 : index
              %2 = arith.muli %arg7, %c6 : index
              %3 = arith.addi %arg5, %2 : index
              %4 = arith.muli %arg6, %c16 : index
              %5 = arith.addi %arg3, %4 : index
              %6 = arith.muli %3, %c256 : index
              %7 = arith.addi %6, %5 : index
              func.call @buddy_blis_sgemm_6x16(%c64, %intptr_1, %0, %intptr, %1, %intptr_2, %7, %c256, %c1) : (index, index, index, index, index, index, index, index, index) -> ()
            }
          }
          memref.dealloc %alloc_0 : memref<4x64x6xf32>
        }
        memref.dealloc %alloc : memref<2x64x16xf32>
      }
    }
    return %arg2 : memref<192x256xf32>
  }
}

