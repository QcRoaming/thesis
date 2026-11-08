//===- TransformOps.h - Microkernel transform extension --------*- C++ -*-===//

#ifndef BUDDY_MICROKERNEL_TRANSFORM_OPS_H
#define BUDDY_MICROKERNEL_TRANSFORM_OPS_H

#include "mlir/Dialect/Transform/IR/TransformDialect.h"
#include "mlir/Dialect/Transform/Interfaces/TransformInterfaces.h"

namespace mlir {
class DialectRegistry;

namespace buddy {
void registerBuddyMicrokernelTransformOps(DialectRegistry &registry);

namespace microkernel {
class TransformExtensions
    : public transform::TransformDialectExtension<TransformExtensions> {
public:
  TransformExtensions();
};
} // namespace microkernel
} // namespace buddy
} // namespace mlir

#define GET_OP_CLASSES
#include "Microkernel/TransformOps.h.inc"

#endif // BUDDY_MICROKERNEL_TRANSFORM_OPS_H
