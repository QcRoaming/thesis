func.func @matmul_m256_k256_n256_f32(
    %A: tensor<256x256xf32>,
    %B: tensor<256x256xf32>,
    %C: tensor<256x256xf32>) -> tensor<256x256xf32>
    attributes {llvm.emit_c_interface} {
  %0 = linalg.matmul
    ins(%A, %B : tensor<256x256xf32>, tensor<256x256xf32>)
    outs(%C : tensor<256x256xf32>) -> tensor<256x256xf32>
  return %0 : tensor<256x256xf32>
}
