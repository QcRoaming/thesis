module @cgo_payload attributes {buddy.payload} {
  func.func @cgo_f32_m24_n192_k32_pab_v0(
      %A: tensor<?x?xf32>,
      %B: tensor<?x?xf32>,
      %C: tensor<?x?xf32>) -> tensor<?x?xf32>
      attributes {llvm.emit_c_interface} {
    %0 = linalg.matmul
      ins(%A, %B : tensor<?x?xf32>, tensor<?x?xf32>)
      outs(%C : tensor<?x?xf32>) -> tensor<?x?xf32>
    return %0 : tensor<?x?xf32>
  }
}

module attributes {transform.with_named_sequence} {
  transform.named_sequence @__transform_main(%root: !transform.any_op) {
    %payload = transform.structured.match ops{["builtin.module"]}
      attributes{buddy.payload} in %root
      : (!transform.any_op) -> !transform.any_op
    %bufferized = transform.bufferization.one_shot_bufferize
      layout{IdentityLayoutMap} %payload
      {bufferize_function_boundaries = true}
      : (!transform.any_op) -> !transform.any_op
    %prepared = transform.apply_registered_pass
      "buddy-materialize-blis-packed-matmul" to %bufferized
      {options = "tile-m=24 tile-n=192 tile-k=32 mr=6 nr=16"}
      : (!transform.any_op) -> !transform.any_op
    %direct = transform.structured.match ops{["func.call"]}
      attributes{callee = @buddy_microkernel_placeholder} in %prepared
      : (!transform.any_op) -> !transform.any_op
    transform.buddy.call_microkernel
      %direct, "buddy_blis_sgemm_6x16" : !transform.any_op
    %fringe = transform.structured.match ops{["func.call"]}
      attributes{callee = @buddy_microkernel_fringe_placeholder} in %prepared
      : (!transform.any_op) -> !transform.any_op
    transform.buddy.call_microkernel
      %fringe, "buddy_blis_sgemm_6x16_fringe" : !transform.any_op
    transform.yield
  }
}
