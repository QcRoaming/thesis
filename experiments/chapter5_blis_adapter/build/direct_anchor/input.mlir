module @chapter5_payload attributes {buddy.payload} {
  func.func @chapter5_direct_anchor(
      %A: tensor<192x256xf32>,
      %B: tensor<256x256xf32>,
      %C: tensor<192x256xf32>) -> tensor<192x256xf32>
      attributes {llvm.emit_c_interface} {
    %0 = linalg.matmul
      ins(%A, %B : tensor<192x256xf32>, tensor<256x256xf32>)
      outs(%C : tensor<192x256xf32>) -> tensor<192x256xf32>
    return %0 : tensor<192x256xf32>
  }
}

module attributes {transform.with_named_sequence} {
  transform.named_sequence @__transform_main(
      %module_op: !transform.any_op) {
    %payload = transform.structured.match ops{["builtin.module"]}
      attributes{buddy.payload} in %module_op
      : (!transform.any_op) -> !transform.any_op
    %bufferized = transform.bufferization.one_shot_bufferize
      layout{IdentityLayoutMap} %payload
      {bufferize_function_boundaries = true}
      : (!transform.any_op) -> !transform.any_op
    %prepared = transform.apply_registered_pass
      "buddy-materialize-blis-packed-matmul" to %bufferized
      {options = "tile-m=24 tile-n=32 tile-k=64 mr=6 nr=16"}
      : (!transform.any_op) -> !transform.any_op
    %calls = transform.structured.match ops{["func.call"]} in %prepared
      : (!transform.any_op) -> !transform.any_op
    transform.buddy.call_microkernel
      %calls, "buddy_blis_sgemm_6x16" : !transform.any_op
    transform.yield
  }
}
