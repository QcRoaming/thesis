func.func @matmul_m128_k128_n128_f32(
    %A: tensor<128x128xf32>,
    %B: tensor<128x128xf32>,
    %C: tensor<128x128xf32>) -> tensor<128x128xf32>
    attributes {llvm.emit_c_interface} {
  %0 = linalg.matmul
    ins(%A, %B : tensor<128x128xf32>, tensor<128x128xf32>)
    outs(%C : tensor<128x128xf32>) -> tensor<128x128xf32>
  return %0 : tensor<128x128xf32>
}
