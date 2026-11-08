module {
  func.func @chapter5_dynamic_fallback(%arg0: memref<?x?xf32>, %arg1: memref<?x?xf32>, %arg2: memref<?x?xf32>) -> memref<?x?xf32> attributes {llvm.emit_c_interface} {
    linalg.matmul ins(%arg0, %arg1 : memref<?x?xf32>, memref<?x?xf32>) outs(%arg2 : memref<?x?xf32>)
    return %arg2 : memref<?x?xf32>
  }
  module attributes {transform.with_named_sequence} {
  }
}

