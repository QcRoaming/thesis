func.func @matmul_m256_k11008_n4096_f32(%A: tensor<256x11008xf32>,
                                        %B: tensor<11008x4096xf32>,
                                        %C: tensor<256x4096xf32>) -> tensor<256x4096xf32> attributes { llvm.emit_c_interface } {
  %0 = linalg.matmul
    ins(%A, %B : tensor<256x11008xf32>, tensor<11008x4096xf32>)
    outs(%C : tensor<256x4096xf32>) -> tensor<256x4096xf32>
  return %0 : tensor<256x4096xf32>
}

module attributes {transform.with_named_sequence} {
  transform.named_sequence @__transform_main(%module_op: !transform.any_op {transform.consumed}) {
    %matmul = transform.structured.match ops{["linalg.matmul"]} in %module_op
      : (!transform.any_op) -> !transform.any_op
    %tiled, %loops:3 = transform.structured.tile_using_for %matmul tile_sizes [32, 32, 32]
      : (!transform.any_op) -> (!transform.any_op, !transform.any_op, !transform.any_op, !transform.any_op)
    %func = transform.get_parent_op %tiled {isolated_from_above}
      : (!transform.any_op) -> !transform.any_op
    transform.structured.vectorize_children_and_apply_patterns %func
      : (!transform.any_op) -> !transform.any_op
    %bufferized = transform.bufferization.one_shot_bufferize layout{IdentityLayoutMap}
      %module_op {bufferize_function_boundaries = true}
      : (!transform.any_op) -> !transform.any_op
    transform.yield
  }
}
