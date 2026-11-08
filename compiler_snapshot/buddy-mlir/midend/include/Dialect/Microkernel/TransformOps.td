//===- TransformOps.td - Microkernel transform extension -------*- tablegen -*-===//

#ifndef BUDDY_MICROKERNEL_TRANSFORM_OPS_TD
#define BUDDY_MICROKERNEL_TRANSFORM_OPS_TD

include "mlir/Dialect/Transform/IR/TransformDialect.td"
include "mlir/Dialect/Transform/IR/TransformTypes.td"
include "mlir/Dialect/Transform/Interfaces/TransformInterfaces.td"
include "mlir/Interfaces/SideEffectInterfaces.td"

def CallMicrokernelOp : Op<Transform_Dialect, "buddy.call_microkernel",
    [DeclareOpInterfaceMethods<TransformOpInterface>,
     DeclareOpInterfaceMethods<MemoryEffectsOpInterface>]> {
  let summary = "Retargets prepared microkernel placeholder calls";
  let description = [{
    Retargets each prepared direct or fringe microkernel placeholder call
    associated with the input handle to the requested runtime wrapper. Packing,
    tiling, path selection, and ABI argument construction must already be
    complete.

    Produces a silenceable failure without changing the payload when a target
    is not a prepared placeholder call.
  }];

  let arguments = (ins TransformHandleTypeInterface:$call, StrAttr:$callee);
  let results = (outs);
  let assemblyFormat = "$call `,` $callee attr-dict `:` type($call)";
  let cppNamespace = "mlir::buddy::microkernel";
}

#endif // BUDDY_MICROKERNEL_TRANSFORM_OPS_TD
