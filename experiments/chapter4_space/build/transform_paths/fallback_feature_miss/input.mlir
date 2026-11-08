func.func @chapter4_fallback_feature_miss(
    %A: tensor<192x256xf32>,
    %B: tensor<256x256xf32>,
    %C: tensor<192x256xf32>) -> tensor<192x256xf32>
    attributes {llvm.emit_c_interface} {
  %0 = linalg.matmul
    ins(%A, %B : tensor<192x256xf32>, tensor<256x256xf32>)
    outs(%C : tensor<192x256xf32>) -> tensor<192x256xf32>
  return %0 : tensor<192x256xf32>
}

module attributes {transform.with_named_sequence, chapter4.template_path = "generic_fallback_schedule"} {
  transform.named_sequence @__transform_main(
      %module_op: !transform.any_op {transform.consumed}) {
    %matmul = transform.structured.match ops{["linalg.matmul"]} in %module_op
      : (!transform.any_op) -> !transform.any_op
    %tiled, %loops:3 = transform.structured.tile_using_for %matmul
      tile_sizes [24, 32, 64]
      : (!transform.any_op) -> (!transform.any_op, !transform.any_op,
          !transform.any_op, !transform.any_op)
    %bufferized = transform.bufferization.one_shot_bufferize
      layout{IdentityLayoutMap} %module_op
      {bufferize_function_boundaries = true}
      : (!transform.any_op) -> !transform.any_op
    transform.yield
  }
}
