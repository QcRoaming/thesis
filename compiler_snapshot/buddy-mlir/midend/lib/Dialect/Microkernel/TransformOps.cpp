//===- TransformOps.cpp - Microkernel transform extension ------*- C++ -*-===//

#include "Microkernel/TransformOps.h"

#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/DialectRegistry.h"
#include "mlir/Interfaces/SideEffectInterfaces.h"

using namespace mlir;

namespace mlir::buddy::microkernel {

TransformExtensions::TransformExtensions() {
  declareGeneratedDialect<func::FuncDialect>();
  registerTransformOps<
#define GET_OP_LIST
#include "Microkernel/TransformOps.cpp.inc"
      >();
}

DiagnosedSilenceableFailure
CallMicrokernelOp::apply(transform::TransformRewriter &rewriter,
                         transform::TransformResults &results,
                         transform::TransformState &state) {
  SmallVector<func::CallOp> calls;
  for (Operation *payload : state.getPayloadOps(getCall())) {
    auto call = dyn_cast<func::CallOp>(payload);
    bool isPrepared =
        call && (call.getCallee() == "buddy_microkernel_placeholder" ||
                 call.getCallee() == "buddy_microkernel_fringe_placeholder");
    if (!isPrepared) {
      DiagnosedSilenceableFailure diag =
          emitSilenceableError()
          << "expects prepared direct or fringe microkernel placeholder calls";
      diag.attachNote(payload->getLoc()) << "offending payload";
      return diag;
    }
    calls.push_back(call);
  }

  for (func::CallOp call : calls) {
    ModuleOp module = call->getParentOfType<ModuleOp>();
    if (!module.lookupSymbol<func::FuncOp>(getCallee())) {
      OpBuilder::InsertionGuard guard(rewriter);
      rewriter.setInsertionPointToStart(module.getBody());
      auto type = FunctionType::get(
          rewriter.getContext(), call.getOperandTypes(), call.getResultTypes());
      auto declaration =
          rewriter.create<func::FuncOp>(call.getLoc(), getCallee(), type);
      declaration.setPrivate();
    }
    call.setCallee(getCallee());
  }
  return DiagnosedSilenceableFailure::success();
}

void CallMicrokernelOp::getEffects(
    SmallVectorImpl<MemoryEffects::EffectInstance> &effects) {
  transform::onlyReadsHandle(getCallMutable(), effects);
  transform::modifiesPayload(effects);
}

} // namespace mlir::buddy::microkernel

void mlir::buddy::registerBuddyMicrokernelTransformOps(
    DialectRegistry &registry) {
  registry.addExtensions<microkernel::TransformExtensions>();
}

#define GET_OP_CLASSES
#include "Microkernel/TransformOps.cpp.inc"
