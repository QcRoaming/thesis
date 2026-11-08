module {
  func.func private @k230_contract_adapter_direct_qkv_prefill_m32(memref<?x?xf32, strided<[?, ?], offset: ?>>, memref<?x?xf32, strided<[?, ?], offset: ?>>, memref<?x?xf32, strided<[?, ?], offset: ?>>) attributes {llvm.emit_c_interface}
  func.func @k230_mlir_direct_qkv_prefill_m32(%arg0: memref<?x?xf32>, %arg1: memref<?x?xf32>, %arg2: memref<?x?xf32>) attributes {llvm.emit_c_interface} {
    %cast = memref.cast %arg0 : memref<?x?xf32> to memref<?x?xf32, strided<[?, ?], offset: ?>>
    %cast_0 = memref.cast %arg1 : memref<?x?xf32> to memref<?x?xf32, strided<[?, ?], offset: ?>>
    %cast_1 = memref.cast %arg2 : memref<?x?xf32> to memref<?x?xf32, strided<[?, ?], offset: ?>>
    call @k230_contract_adapter_direct_qkv_prefill_m32(%cast, %cast_0, %cast_1) : (memref<?x?xf32, strided<[?, ?], offset: ?>>, memref<?x?xf32, strided<[?, ?], offset: ?>>, memref<?x?xf32, strided<[?, ?], offset: ?>>) -> ()
    return
  }
}

