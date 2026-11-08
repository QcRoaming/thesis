module @k230_payload attributes {buddy.payload} {
  func.func @k230_mlir_adapt_qkv_fringe_m17(
      %A: memref<?x?xf32>,
      %B: memref<?x?xf32>,
      %C: memref<?x?xf32>) attributes {llvm.emit_c_interface} {
    linalg.generic {
        indexing_maps = [
          affine_map<(m, n, k) -> (m, k)>,
          affine_map<(m, n, k) -> (k, n)>,
          affine_map<(m, n, k) -> (m, n)>],
        iterator_types = ["parallel", "parallel", "reduction"]}
        ins(%A, %B : memref<?x?xf32>, memref<?x?xf32>)
        outs(%C : memref<?x?xf32>) {
      ^bb0(%a: f32, %b: f32, %c: f32):
        %product = arith.mulf %a, %b : f32
        %sum = arith.addf %c, %product : f32
        linalg.yield %sum : f32
      }
    return
  }
}

module attributes {transform.with_named_sequence} {
  transform.named_sequence @__transform_main(%root: !transform.any_op) {
    %matmul = transform.structured.match ops{["linalg.generic"]} in %root
      : (!transform.any_op) -> !transform.any_op
    %callee = transform.param.constant "k230_contract_adapter_adapt_qkv_fringe_m17"
      -> !transform.any_param
    transform.annotate %matmul "library_call" = %callee
      : !transform.any_op, !transform.any_param
    %payload = transform.structured.match ops{["builtin.module"]}
      attributes{buddy.payload} in %root
      : (!transform.any_op) -> !transform.any_op
    %library = transform.apply_registered_pass "convert-linalg-to-std"
      to %payload : (!transform.any_op) -> !transform.any_op
    transform.yield
  }
}
