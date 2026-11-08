add_mlir_library(BuddyMicrokernelTransformOps
  TransformOps.cpp

  DEPENDS
  MicrokernelTransformOpsIncGen

  LINK_LIBS PUBLIC
  MLIRFuncDialect
  MLIRIR
  MLIRSideEffectInterfaces
  MLIRTransformDialect
  MLIRTransformDialectUtils
  )
