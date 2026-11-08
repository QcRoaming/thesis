func.func @chapter5_dynamic_fallback(
    %A: tensor<?x?xf32>,
    %B: tensor<?x?xf32>,
    %C: tensor<?x?xf32>) -> tensor<?x?xf32>
    attributes {llvm.emit_c_interface} {
  %0 = linalg.matmul
    ins(%A, %B : tensor<?x?xf32>, tensor<?x?xf32>)
    outs(%C : tensor<?x?xf32>) -> tensor<?x?xf32>
  return %0 : tensor<?x?xf32>
}

module attributes {transform.with_named_sequence} {
  transform.named_sequence @__transform_main(
      %root: !transform.any_op {transform.consumed}) {
    %bufferized = transform.bufferization.one_shot_bufferize
      layout{IdentityLayoutMap} %root
      {bufferize_function_boundaries = true}
      : (!transform.any_op) -> !transform.any_op
    transform.yield
  }
}
