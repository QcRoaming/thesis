#include "mlir/IR/BuiltinOps.h"
#include "mlir/Pass/Pass.h"

using namespace mlir;

namespace {

struct FinalizeTransformPayloadPass
    : public PassWrapper<FinalizeTransformPayloadPass,
                         OperationPass<ModuleOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(FinalizeTransformPayloadPass)

  StringRef getArgument() const final {
    return "buddy-finalize-transform-payload";
  }

  StringRef getDescription() const final {
    return "Drop the interpreted Transform schedule and unwrap buddy.payload";
  }

  void runOnOperation() final {
    ModuleOp outer = getOperation();
    ModuleOp payload;
    SmallVector<ModuleOp> schedules;

    for (ModuleOp nested : outer.getOps<ModuleOp>()) {
      if (nested->hasAttr("buddy.payload")) {
        if (payload) {
          nested.emitError("only one buddy.payload module is supported");
          signalPassFailure();
          return;
        }
        payload = nested;
      }
      if (nested->hasAttr("transform.with_named_sequence"))
        schedules.push_back(nested);
    }

    if (!payload) {
      outer.emitError("expected a nested module with buddy.payload");
      signalPassFailure();
      return;
    }

    for (ModuleOp schedule : schedules)
      schedule.erase();

    Block &source = payload.getBodyRegion().front();
    outer.getBodyRegion().front().getOperations().splice(
        Block::iterator(payload), source.getOperations(), source.begin(),
        source.end());
    payload.erase();
  }
};

} // namespace

namespace mlir::buddy {

void registerFinalizeTransformPayloadPass() {
  PassRegistration<FinalizeTransformPayloadPass>();
}

} // namespace mlir::buddy
