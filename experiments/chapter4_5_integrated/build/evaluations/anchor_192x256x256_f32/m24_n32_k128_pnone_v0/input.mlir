func.func @integrated_anchor_192x256x256_f32_m24_n32_k128_pnone_v0(
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
    %matmul = transform.structured.match ops{["linalg.matmul"]} in %root
      : (!transform.any_op) -> !transform.any_op
    %tiled, %loops:3 = transform.structured.tile_using_for %matmul
      tile_sizes [24, 32, 128]
      : (!transform.any_op) -> (!transform.any_op, !transform.any_op,
          !transform.any_op, !transform.any_op)
    %bufferized = transform.bufferization.one_shot_bufferize
      layout{IdentityLayoutMap} %root
      {bufferize_function_boundaries = true}
      : (!transform.any_op) -> !transform.any_op
    transform.yield
  }
}
