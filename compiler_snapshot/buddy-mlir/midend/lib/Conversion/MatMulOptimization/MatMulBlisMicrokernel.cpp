//===- MatMulBlisMicrokernel.cpp - Materialize BLIS calls -----*- C++ -*-===//

#include "mlir/Dialect/Arith/IR/Arith.h"
#include "mlir/Dialect/Func/IR/FuncOps.h"
#include "mlir/Dialect/Linalg/IR/Linalg.h"
#include "mlir/Dialect/MemRef/IR/MemRef.h"
#include "mlir/Dialect/SCF/IR/SCF.h"
#include "mlir/IR/BuiltinOps.h"
#include "mlir/Pass/Pass.h"
#include "llvm/Support/CommandLine.h"

using namespace mlir;

namespace {

constexpr StringLiteral kDirectPlaceholder = "buddy_microkernel_placeholder";
constexpr StringLiteral kFringePlaceholder =
    "buddy_microkernel_fringe_placeholder";

static Value indexConstant(OpBuilder &builder, Location loc, int64_t value) {
  return builder.create<arith::ConstantIndexOp>(loc, value);
}

static Value add(OpBuilder &builder, Location loc, Value lhs, Value rhs) {
  return builder.create<arith::AddIOp>(loc, lhs, rhs);
}

static Value sub(OpBuilder &builder, Location loc, Value lhs, Value rhs) {
  return builder.create<arith::SubIOp>(loc, lhs, rhs);
}

static Value mul(OpBuilder &builder, Location loc, Value lhs, Value rhs) {
  return builder.create<arith::MulIOp>(loc, lhs, rhs);
}

static Value min(OpBuilder &builder, Location loc, Value lhs, Value rhs) {
  return builder.create<arith::MinUIOp>(loc, lhs, rhs);
}

static Value ceilDiv(OpBuilder &builder, Location loc, Value value,
                     Value divisor) {
  return builder.create<arith::CeilDivUIOp>(loc, value, divisor);
}

static Value both(OpBuilder &builder, Location loc, Value lhs, Value rhs) {
  return builder.create<arith::AndIOp>(loc, lhs, rhs);
}

static Value dimValue(OpBuilder &builder, Location loc, Value memref,
                      MemRefType type, int64_t dimension) {
  if (!type.isDynamicDim(dimension))
    return indexConstant(builder, loc, type.getDimSize(dimension));
  return builder.create<memref::DimOp>(loc, memref, dimension);
}

static Value loadOrZero(OpBuilder &builder, Location loc, Value source,
                        ValueRange indices, Value inBounds, Value zero) {
  auto ifOp = builder.create<scf::IfOp>(
      loc, inBounds,
      [&](OpBuilder &thenBuilder, Location loc) {
        Value value = thenBuilder.create<memref::LoadOp>(loc, source, indices);
        thenBuilder.create<scf::YieldOp>(loc, value);
      },
      [&](OpBuilder &elseBuilder, Location loc) {
        elseBuilder.create<scf::YieldOp>(loc, zero);
      });
  return ifOp.getResult(0);
}

static void buildPackB(OpBuilder &builder, Location loc, Value source,
                       Value packed, Value pc, Value jc, Value panelCount,
                       Value tileK, Value nr, Value kBound, Value nBound,
                       Value zero, Value c0, Value c1) {
  builder.create<scf::ForOp>(
      loc, c0, panelCount, c1, ValueRange{},
      [&](OpBuilder &b0, Location loc, Value panel, ValueRange) {
        b0.create<scf::ForOp>(
            loc, c0, tileK, c1, ValueRange{},
            [&](OpBuilder &b1, Location loc, Value p, ValueRange) {
              b1.create<scf::ForOp>(
                  loc, c0, nr, c1, ValueRange{},
                  [&](OpBuilder &b2, Location loc, Value j, ValueRange) {
                    Value sourceK = add(b2, loc, pc, p);
                    Value sourceN = add(
                        b2, loc, jc, add(b2, loc, mul(b2, loc, panel, nr), j));
                    Value kInBounds = b2.create<arith::CmpIOp>(
                        loc, arith::CmpIPredicate::ult, sourceK, kBound);
                    Value nInBounds = b2.create<arith::CmpIOp>(
                        loc, arith::CmpIPredicate::ult, sourceN, nBound);
                    Value value = loadOrZero(
                        b2, loc, source, ValueRange{sourceK, sourceN},
                        both(b2, loc, kInBounds, nInBounds), zero);
                    b2.create<memref::StoreOp>(loc, value, packed,
                                               ValueRange{panel, p, j});
                    b2.create<scf::YieldOp>(loc);
                  });
              b1.create<scf::YieldOp>(loc);
            });
        b0.create<scf::YieldOp>(loc);
      });
}

static void buildPackA(OpBuilder &builder, Location loc, Value source,
                       Value packed, Value ic, Value pc, Value panelCount,
                       Value tileK, Value mr, Value mBound, Value kBound,
                       Value zero, Value c0, Value c1) {
  builder.create<scf::ForOp>(
      loc, c0, panelCount, c1, ValueRange{},
      [&](OpBuilder &b0, Location loc, Value panel, ValueRange) {
        b0.create<scf::ForOp>(
            loc, c0, tileK, c1, ValueRange{},
            [&](OpBuilder &b1, Location loc, Value p, ValueRange) {
              b1.create<scf::ForOp>(
                  loc, c0, mr, c1, ValueRange{},
                  [&](OpBuilder &b2, Location loc, Value i, ValueRange) {
                    Value sourceM = add(
                        b2, loc, ic, add(b2, loc, mul(b2, loc, panel, mr), i));
                    Value sourceK = add(b2, loc, pc, p);
                    Value mInBounds = b2.create<arith::CmpIOp>(
                        loc, arith::CmpIPredicate::ult, sourceM, mBound);
                    Value kInBounds = b2.create<arith::CmpIOp>(
                        loc, arith::CmpIPredicate::ult, sourceK, kBound);
                    Value value = loadOrZero(
                        b2, loc, source, ValueRange{sourceM, sourceK},
                        both(b2, loc, mInBounds, kInBounds), zero);
                    b2.create<memref::StoreOp>(loc, value, packed,
                                               ValueRange{panel, p, i});
                    b2.create<scf::YieldOp>(loc);
                  });
              b1.create<scf::YieldOp>(loc);
            });
        b0.create<scf::YieldOp>(loc);
      });
}

static void emitMicrokernelCall(OpBuilder &builder, Location loc,
                                StringRef callee, Value actualK, Value aPointer,
                                Value aOffset, Value bPointer, Value bOffset,
                                Value cPointer, Value cOffset, Value cRowStride,
                                Value cColStride) {
  builder.create<func::CallOp>(loc, callee, TypeRange{},
                               ValueRange{actualK, aPointer, aOffset, bPointer,
                                          bOffset, cPointer, cOffset,
                                          cRowStride, cColStride});
}

static void buildFringeCall(OpBuilder &builder, Location loc, Value c,
                            MemRefType temporaryCType, Value actualK,
                            Value aPointer, Value aOffset, Value bPointer,
                            Value bOffset, Value globalI, Value globalJ,
                            Value validM, Value validN, Value mr, Value nr,
                            Value zero, Value c0, Value c1) {
  auto temporaryC = builder.create<memref::AllocOp>(loc, temporaryCType);
  temporaryC->setAttr("alignment", builder.getI64IntegerAttr(64));

  builder.create<scf::ForOp>(
      loc, c0, mr, c1, ValueRange{},
      [&](OpBuilder &iBuilder, Location loc, Value i, ValueRange) {
        iBuilder.create<scf::ForOp>(
            loc, c0, nr, c1, ValueRange{},
            [&](OpBuilder &jBuilder, Location loc, Value j, ValueRange) {
              Value iInBounds = jBuilder.create<arith::CmpIOp>(
                  loc, arith::CmpIPredicate::ult, i, validM);
              Value jInBounds = jBuilder.create<arith::CmpIOp>(
                  loc, arith::CmpIPredicate::ult, j, validN);
              Value sourceI = add(jBuilder, loc, globalI, i);
              Value sourceJ = add(jBuilder, loc, globalJ, j);
              Value value =
                  loadOrZero(jBuilder, loc, c, ValueRange{sourceI, sourceJ},
                             both(jBuilder, loc, iInBounds, jInBounds), zero);
              jBuilder.create<memref::StoreOp>(loc, value, temporaryC,
                                               ValueRange{i, j});
              jBuilder.create<scf::YieldOp>(loc);
            });
        iBuilder.create<scf::YieldOp>(loc);
      });

  Value temporaryPointer =
      builder.create<memref::ExtractAlignedPointerAsIndexOp>(loc, temporaryC);
  emitMicrokernelCall(builder, loc, kFringePlaceholder, actualK, aPointer,
                      aOffset, bPointer, bOffset, temporaryPointer, c0, nr, c1);

  builder.create<scf::ForOp>(
      loc, c0, validM, c1, ValueRange{},
      [&](OpBuilder &iBuilder, Location loc, Value i, ValueRange) {
        iBuilder.create<scf::ForOp>(
            loc, c0, validN, c1, ValueRange{},
            [&](OpBuilder &jBuilder, Location loc, Value j, ValueRange) {
              Value value = jBuilder.create<memref::LoadOp>(loc, temporaryC,
                                                            ValueRange{i, j});
              Value destinationI = add(jBuilder, loc, globalI, i);
              Value destinationJ = add(jBuilder, loc, globalJ, j);
              jBuilder.create<memref::StoreOp>(
                  loc, value, c, ValueRange{destinationI, destinationJ});
              jBuilder.create<scf::YieldOp>(loc);
            });
        iBuilder.create<scf::YieldOp>(loc);
      });
  builder.create<memref::DeallocOp>(loc, temporaryC);
}

static bool compatibleDimensions(int64_t lhs, int64_t rhs) {
  return ShapedType::isDynamic(lhs) || ShapedType::isDynamic(rhs) || lhs == rhs;
}

class MatMulToBlisPackedMicrokernelPass
    : public PassWrapper<MatMulToBlisPackedMicrokernelPass,
                         OperationPass<ModuleOp>> {
public:
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(
      MatMulToBlisPackedMicrokernelPass)

  StringRef getArgument() const final {
    return "buddy-materialize-blis-packed-matmul";
  }
  StringRef getDescription() const final {
    return "Materialize BLIS panel packing and direct/fringe microkernel calls";
  }

  MatMulToBlisPackedMicrokernelPass() = default;
  MatMulToBlisPackedMicrokernelPass(
      const MatMulToBlisPackedMicrokernelPass &pass)
      : PassWrapper(pass) {}

  Option<int64_t> tileM{*this, "tile-m", llvm::cl::init(24)};
  Option<int64_t> tileN{*this, "tile-n", llvm::cl::init(32)};
  Option<int64_t> tileK{*this, "tile-k", llvm::cl::init(64)};
  Option<int64_t> mr{*this, "mr", llvm::cl::init(6)};
  Option<int64_t> nr{*this, "nr", llvm::cl::init(16)};

  void getDependentDialects(DialectRegistry &registry) const override {
    registry
        .insert<arith::ArithDialect, func::FuncDialect, linalg::LinalgDialect,
                memref::MemRefDialect, scf::SCFDialect>();
  }

  void runOnOperation() override {
    ModuleOp module = getOperation();
    SmallVector<linalg::MatmulOp> matmuls;
    module.walk([&](linalg::MatmulOp op) { matmuls.push_back(op); });
    if (matmuls.size() != 1) {
      module.emitError("expected exactly one buffer-semantics linalg.matmul");
      return signalPassFailure();
    }
    if (tileM <= 0 || tileN <= 0 || tileK <= 0 || mr <= 0 || nr <= 0 ||
        tileM % mr != 0 || tileN % nr != 0) {
      module.emitError("requires positive tiles with tile-m % mr == 0 and "
                       "tile-n % nr == 0");
      return signalPassFailure();
    }

    IRRewriter rewriter(&getContext());
    auto index = rewriter.getIndexType();
    auto placeholderType =
        rewriter.getFunctionType(SmallVector<Type>(9, index), TypeRange{});
    for (StringRef name : {kDirectPlaceholder, kFringePlaceholder}) {
      if (!module.lookupSymbol<func::FuncOp>(name)) {
        rewriter.setInsertionPointToStart(module.getBody());
        auto declaration = rewriter.create<func::FuncOp>(module.getLoc(), name,
                                                         placeholderType);
        declaration.setPrivate();
      }
    }

    linalg::MatmulOp matmul = matmuls.front();
    Value a = matmul->getOperand(0);
    Value b = matmul->getOperand(1);
    Value c = matmul->getOperand(2);
    auto aType = dyn_cast<MemRefType>(a.getType());
    auto bType = dyn_cast<MemRefType>(b.getType());
    auto cType = dyn_cast<MemRefType>(c.getType());
    if (!aType || !bType || !cType || aType.getRank() != 2 ||
        bType.getRank() != 2 || cType.getRank() != 2 ||
        !aType.getLayout().isIdentity() || !bType.getLayout().isIdentity() ||
        !cType.getLayout().isIdentity()) {
      matmul.emitError("requires rank-2 row-major f32/f64 memrefs");
      return signalPassFailure();
    }
    Type elementType = aType.getElementType();
    if ((!elementType.isF32() && !elementType.isF64()) ||
        bType.getElementType() != elementType ||
        cType.getElementType() != elementType) {
      matmul.emitError("requires matching f32 or f64 element types");
      return signalPassFailure();
    }
    if (!compatibleDimensions(aType.getDimSize(1), bType.getDimSize(0)) ||
        !compatibleDimensions(aType.getDimSize(0), cType.getDimSize(0)) ||
        !compatibleDimensions(bType.getDimSize(1), cType.getDimSize(1))) {
      matmul.emitError("requires statically compatible M/N/K dimensions");
      return signalPassFailure();
    }

    Location loc = matmul.getLoc();
    rewriter.setInsertionPoint(matmul);
    Value c0 = indexConstant(rewriter, loc, 0);
    Value c1 = indexConstant(rewriter, loc, 1);
    Value mValue = dimValue(rewriter, loc, a, aType, 0);
    Value kValue = dimValue(rewriter, loc, a, aType, 1);
    Value nValue = dimValue(rewriter, loc, b, bType, 1);
    Value tileMValue = indexConstant(rewriter, loc, tileM);
    Value tileNValue = indexConstant(rewriter, loc, tileN);
    Value tileKValue = indexConstant(rewriter, loc, tileK);
    Value mrValue = indexConstant(rewriter, loc, mr);
    Value nrValue = indexConstant(rewriter, loc, nr);
    Value aPanelStride = indexConstant(rewriter, loc, tileK * mr);
    Value bPanelStride = indexConstant(rewriter, loc, tileK * nr);
    Value zero = rewriter.create<arith::ConstantOp>(
        loc, rewriter.getFloatAttr(elementType, 0.0));

    auto packedAType =
        MemRefType::get({tileM / mr, tileK, mr}, elementType);
    auto packedBType =
        MemRefType::get({tileN / nr, tileK, nr}, elementType);
    auto temporaryCType = MemRefType::get({mr, nr}, elementType);

    rewriter.create<scf::ForOp>(
        loc, c0, nValue, tileNValue, ValueRange{},
        [&](OpBuilder &jcBuilder, Location loc, Value jc, ValueRange) {
          Value actualN =
              min(jcBuilder, loc, tileNValue, sub(jcBuilder, loc, nValue, jc));
          Value nPanels = ceilDiv(jcBuilder, loc, actualN, nrValue);
          jcBuilder.create<scf::ForOp>(
              loc, c0, kValue, tileKValue, ValueRange{},
              [&](OpBuilder &pcBuilder, Location loc, Value pc, ValueRange) {
                Value actualK = min(pcBuilder, loc, tileKValue,
                                    sub(pcBuilder, loc, kValue, pc));
                auto packedB =
                    pcBuilder.create<memref::AllocOp>(loc, packedBType);
                packedB->setAttr("alignment", pcBuilder.getI64IntegerAttr(64));
                buildPackB(pcBuilder, loc, b, packedB, pc, jc, nPanels,
                           tileKValue, nrValue, kValue, nValue, zero, c0, c1);
                Value bPointer =
                    pcBuilder.create<memref::ExtractAlignedPointerAsIndexOp>(
                        loc, packedB);

                pcBuilder.create<scf::ForOp>(
                    loc, c0, mValue, tileMValue, ValueRange{},
                    [&](OpBuilder &icBuilder, Location loc, Value ic,
                        ValueRange) {
                      Value actualM = min(icBuilder, loc, tileMValue,
                                          sub(icBuilder, loc, mValue, ic));
                      Value mPanels = ceilDiv(icBuilder, loc, actualM, mrValue);
                      auto packedA =
                          icBuilder.create<memref::AllocOp>(loc, packedAType);
                      packedA->setAttr("alignment",
                                       icBuilder.getI64IntegerAttr(64));
                      buildPackA(icBuilder, loc, a, packedA, ic, pc, mPanels,
                                 tileKValue, mrValue, mValue, kValue, zero, c0,
                                 c1);
                      Value aPointer =
                          icBuilder
                              .create<memref::ExtractAlignedPointerAsIndexOp>(
                                  loc, packedA);
                      Value cPointer =
                          icBuilder
                              .create<memref::ExtractAlignedPointerAsIndexOp>(
                                  loc, c);

                      icBuilder.create<scf::ForOp>(
                          loc, c0, nPanels, c1, ValueRange{},
                          [&](OpBuilder &jBuilder, Location loc, Value jPanel,
                              ValueRange) {
                            jBuilder.create<scf::ForOp>(
                                loc, c0, mPanels, c1, ValueRange{},
                                [&](OpBuilder &iBuilder, Location loc,
                                    Value iPanel, ValueRange) {
                                  Value aOffset =
                                      mul(iBuilder, loc, iPanel, aPanelStride);
                                  Value bOffset =
                                      mul(iBuilder, loc, jPanel, bPanelStride);
                                  Value globalI =
                                      add(iBuilder, loc, ic,
                                          mul(iBuilder, loc, iPanel, mrValue));
                                  Value globalJ =
                                      add(iBuilder, loc, jc,
                                          mul(iBuilder, loc, jPanel, nrValue));
                                  Value validM =
                                      min(iBuilder, loc, mrValue,
                                          sub(iBuilder, loc, mValue, globalI));
                                  Value validN =
                                      min(iBuilder, loc, nrValue,
                                          sub(iBuilder, loc, nValue, globalJ));
                                  Value fullM = iBuilder.create<arith::CmpIOp>(
                                      loc, arith::CmpIPredicate::eq, validM,
                                      mrValue);
                                  Value fullN = iBuilder.create<arith::CmpIOp>(
                                      loc, arith::CmpIPredicate::eq, validN,
                                      nrValue);
                                  Value fullTile =
                                      both(iBuilder, loc, fullM, fullN);
                                  iBuilder.create<scf::IfOp>(
                                      loc, fullTile,
                                      [&](OpBuilder &thenBuilder,
                                          Location loc) {
                                        Value cOffset =
                                            add(thenBuilder, loc,
                                                mul(thenBuilder, loc, globalI,
                                                    nValue),
                                                globalJ);
                                        emitMicrokernelCall(
                                            thenBuilder, loc,
                                            kDirectPlaceholder, actualK,
                                            aPointer, aOffset, bPointer,
                                            bOffset, cPointer, cOffset, nValue,
                                            c1);
                                        thenBuilder.create<scf::YieldOp>(loc);
                                      },
                                      [&](OpBuilder &elseBuilder,
                                          Location loc) {
                                        buildFringeCall(
                                            elseBuilder, loc, c, temporaryCType,
                                            actualK, aPointer, aOffset,
                                            bPointer, bOffset, globalI, globalJ,
                                            validM, validN, mrValue, nrValue,
                                            zero, c0, c1);
                                        elseBuilder.create<scf::YieldOp>(loc);
                                      });
                                  iBuilder.create<scf::YieldOp>(loc);
                                });
                            jBuilder.create<scf::YieldOp>(loc);
                          });
                      icBuilder.create<memref::DeallocOp>(loc, packedA);
                      icBuilder.create<scf::YieldOp>(loc);
                    });
                pcBuilder.create<memref::DeallocOp>(loc, packedB);
                pcBuilder.create<scf::YieldOp>(loc);
              });
          jcBuilder.create<scf::YieldOp>(loc);
        });
    rewriter.eraseOp(matmul);
  }
};

} // namespace

namespace mlir::buddy {
void registerMatMulToBlisPackedMicrokernelPass() {
  PassRegistration<MatMulToBlisPackedMicrokernelPass>();
}
} // namespace mlir::buddy
