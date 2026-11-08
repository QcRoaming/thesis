#include "blis.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <memory>
#include <numeric>
#include <sstream>
#include <string>
#include <vector>

extern "C" void bli_sgemm_haswell_asm_6x16(dim_t m, dim_t n, dim_t k,
                                           const void *alpha, const void *a,
                                           const void *b, const void *beta,
                                           void *c, inc_t rs_c, inc_t cs_c,
                                           const auxinfo_t *data,
                                           const cntx_t *cntx);

namespace {

using Clock = std::chrono::steady_clock;
constexpr int64_t MR = 6;
constexpr int64_t NR = 16;
constexpr int64_t KC = 256;

template <typename T, std::size_t Alignment> class AlignedAllocator {
public:
  using value_type = T;

  AlignedAllocator() noexcept = default;
  template <typename U>
  AlignedAllocator(const AlignedAllocator<U, Alignment> &) noexcept {}

  T *allocate(std::size_t count) {
    void *pointer = nullptr;
    if (posix_memalign(&pointer, Alignment, count * sizeof(T)) != 0)
      throw std::bad_alloc();
    return static_cast<T *>(pointer);
  }

  void deallocate(T *pointer, std::size_t) noexcept { std::free(pointer); }

  template <typename U> struct rebind {
    using other = AlignedAllocator<U, Alignment>;
  };
};

template <typename T, typename U, std::size_t Alignment>
bool operator==(const AlignedAllocator<T, Alignment> &,
                const AlignedAllocator<U, Alignment> &) {
  return true;
}

template <typename T, typename U, std::size_t Alignment>
bool operator!=(const AlignedAllocator<T, Alignment> &,
                const AlignedAllocator<U, Alignment> &) {
  return false;
}

using AlignedFloats = std::vector<float, AlignedAllocator<float, 64>>;

enum class Variant {
  IndependentBlis,
  ConcatenatedBlis,
  RepackedAMicrokernel,
  SharedAMicrokernel,
};

struct Timing {
  double totalMs = 0.0;
  double packMs = -1.0;
  double computeMs = 0.0;
};

struct Problem {
  std::string region;
  std::string phase;
  int64_t m = 0;
  int64_t k = 0;
  std::vector<int64_t> ns;
  std::vector<float> a;
  std::vector<std::vector<float>> weights;
  std::vector<std::vector<float>> outputs;
  std::vector<std::vector<float>> expected;
  std::vector<AlignedFloats> packedWeights;
  std::vector<float> concatenatedWeights;
  std::vector<float> concatenatedOutput;
  AlignedFloats packedA;
  double persistentWeightPackMs = 0.0;
  double weightConcatenationMs = 0.0;
};

int64_t positive(const char *value, const char *name) {
  const long long parsed = std::strtoll(value, nullptr, 10);
  if (parsed <= 0) {
    std::cerr << name << " must be positive\n";
    std::exit(2);
  }
  return static_cast<int64_t>(parsed);
}

std::vector<int64_t> parseNs(const std::string &value) {
  std::vector<int64_t> result;
  std::stringstream stream(value);
  std::string item;
  while (std::getline(stream, item, ',')) {
    const auto parsed = std::strtoll(item.c_str(), nullptr, 10);
    if (parsed <= 0) {
      std::cerr << "all branch N values must be positive\n";
      std::exit(2);
    }
    result.push_back(parsed);
  }
  if (result.size() < 2) {
    std::cerr << "fan-out experiment requires at least two branches\n";
    std::exit(2);
  }
  return result;
}

const char *variantName(Variant variant) {
  switch (variant) {
  case Variant::IndependentBlis:
    return "independent_blis";
  case Variant::ConcatenatedBlis:
    return "concatenated_blis";
  case Variant::RepackedAMicrokernel:
    return "repacked_a_microkernel";
  case Variant::SharedAMicrokernel:
    return "shared_a_microkernel";
  }
  return "unknown";
}

double elapsedMs(Clock::time_point begin, Clock::time_point end) {
  return std::chrono::duration<double, std::milli>(end - begin).count();
}

double median(std::vector<double> values) {
  std::sort(values.begin(), values.end());
  const size_t middle = values.size() / 2;
  if (values.size() % 2 == 1)
    return values[middle];
  return 0.5 * (values[middle - 1] + values[middle]);
}

void fillProblem(Problem &problem) {
  problem.a.resize(static_cast<size_t>(problem.m) * problem.k);
  for (int64_t i = 0; i < problem.m; ++i)
    for (int64_t p = 0; p < problem.k; ++p)
      problem.a[i * problem.k + p] =
          static_cast<float>(((i * 17 + p * 13) % 101) - 50) / 101.0f;

  problem.weights.resize(problem.ns.size());
  problem.outputs.resize(problem.ns.size());
  problem.expected.resize(problem.ns.size());
  for (size_t branch = 0; branch < problem.ns.size(); ++branch) {
    const int64_t n = problem.ns[branch];
    auto &weight = problem.weights[branch];
    weight.resize(static_cast<size_t>(problem.k) * n);
    problem.outputs[branch].resize(static_cast<size_t>(problem.m) * n);
    problem.expected[branch].resize(static_cast<size_t>(problem.m) * n);
    for (int64_t p = 0; p < problem.k; ++p)
      for (int64_t j = 0; j < n; ++j)
        weight[p * n + j] =
            static_cast<float>(
                ((p * 19 + j * 7 + static_cast<int64_t>(branch) * 23) % 97) -
                48) /
            97.0f;
  }
}

AlignedFloats packWeight(const std::vector<float> &weight, int64_t k,
                         int64_t n) {
  const int64_t panels = (n + NR - 1) / NR;
  AlignedFloats packed(static_cast<size_t>(panels) * k * NR, 0.0f);
  for (int64_t pc = 0; pc < k; pc += KC) {
    const int64_t blockK = std::min<int64_t>(KC, k - pc);
    for (int64_t panel = 0; panel < panels; ++panel)
      for (int64_t p = 0; p < blockK; ++p)
        for (int64_t j = 0; j < NR; ++j) {
          const int64_t column = panel * NR + j;
          if (column < n)
            packed[((pc * panels + panel * blockK + p) * NR) + j] =
                weight[(pc + p) * n + column];
        }
  }
  return packed;
}

void preparePersistentRepresentations(Problem &problem) {
  auto begin = Clock::now();
  problem.packedWeights.clear();
  for (size_t branch = 0; branch < problem.ns.size(); ++branch)
    problem.packedWeights.push_back(
        packWeight(problem.weights[branch], problem.k, problem.ns[branch]));
  auto end = Clock::now();
  problem.persistentWeightPackMs = elapsedMs(begin, end);

  begin = Clock::now();
  const int64_t totalN =
      std::accumulate(problem.ns.begin(), problem.ns.end(), int64_t{0});
  problem.concatenatedWeights.assign(static_cast<size_t>(problem.k) * totalN,
                                     0.0f);
  int64_t offset = 0;
  for (size_t branch = 0; branch < problem.ns.size(); ++branch) {
    const int64_t n = problem.ns[branch];
    for (int64_t p = 0; p < problem.k; ++p)
      std::copy_n(problem.weights[branch].data() + p * n, n,
                  problem.concatenatedWeights.data() + p * totalN + offset);
    offset += n;
  }
  problem.concatenatedOutput.resize(static_cast<size_t>(problem.m) * totalN);
  end = Clock::now();
  problem.weightConcatenationMs = elapsedMs(begin, end);

  const int64_t mPanels = (problem.m + MR - 1) / MR;
  problem.packedA.resize(static_cast<size_t>(mPanels) * problem.k * MR);
}

void packActivation(const Problem &problem, AlignedFloats &packed) {
  const int64_t panels = (problem.m + MR - 1) / MR;
  std::fill(packed.begin(), packed.end(), 0.0f);
  for (int64_t pc = 0; pc < problem.k; pc += KC) {
    const int64_t blockK = std::min<int64_t>(KC, problem.k - pc);
    for (int64_t panel = 0; panel < panels; ++panel)
      for (int64_t p = 0; p < blockK; ++p)
        for (int64_t i = 0; i < MR; ++i) {
          const int64_t row = panel * MR + i;
          if (row < problem.m)
            packed[((pc * panels + panel * blockK + p) * MR) + i] =
                problem.a[row * problem.k + pc + p];
        }
  }
}

void callMicrokernel(int64_t k, const float *packedA, const float *packedB,
                     float *c, int64_t rowStride, float beta) {
  const float alpha = 1.0f;
  auxinfo_t aux{};
  bli_auxinfo_set_next_a(const_cast<float *>(packedA), &aux);
  bli_auxinfo_set_next_b(const_cast<float *>(packedB), &aux);
  bli_sgemm_haswell_asm_6x16(MR, NR, static_cast<dim_t>(k), &alpha, packedA,
                             packedB, &beta, c, static_cast<inc_t>(rowStride),
                             1, &aux, bli_gks_query_cntx());
}

void computeMicrokernelBranch(const Problem &problem,
                              const AlignedFloats &packedA,
                              const AlignedFloats &packedB,
                              std::vector<float> &output, int64_t n) {
  const int64_t mPanels = (problem.m + MR - 1) / MR;
  const int64_t nPanels = (n + NR - 1) / NR;
  for (int64_t mPanel = 0; mPanel < mPanels; ++mPanel) {
    const int64_t validM = std::min<int64_t>(MR, problem.m - mPanel * MR);
    for (int64_t nPanel = 0; nPanel < nPanels; ++nPanel) {
      const int64_t validN = std::min<int64_t>(NR, n - nPanel * NR);
      if (validM == MR && validN == NR) {
        float beta = 0.0f;
        for (int64_t pc = 0; pc < problem.k; pc += KC) {
          const int64_t blockK = std::min<int64_t>(KC, problem.k - pc);
          const float *aBlock =
              packedA.data() + (pc * mPanels + mPanel * blockK) * MR;
          const float *bBlock =
              packedB.data() + (pc * nPanels + nPanel * blockK) * NR;
          callMicrokernel(blockK, aBlock, bBlock,
                          output.data() + mPanel * MR * n + nPanel * NR, n,
                          beta);
          beta = 1.0f;
        }
        continue;
      }
      alignas(64) float temporary[MR * NR]{};
      float beta = 0.0f;
      for (int64_t pc = 0; pc < problem.k; pc += KC) {
        const int64_t blockK = std::min<int64_t>(KC, problem.k - pc);
        const float *aBlock =
            packedA.data() + (pc * mPanels + mPanel * blockK) * MR;
        const float *bBlock =
            packedB.data() + (pc * nPanels + nPanel * blockK) * NR;
        callMicrokernel(blockK, aBlock, bBlock, temporary, NR, beta);
        beta = 1.0f;
      }
      for (int64_t i = 0; i < validM; ++i)
        std::copy_n(temporary + i * NR, validN,
                    output.data() + (mPanel * MR + i) * n + nPanel * NR);
    }
  }
}

Timing execute(Problem &problem, Variant variant) {
  const float alpha = 1.0f;
  const float beta = 0.0f;
  const int64_t totalN =
      std::accumulate(problem.ns.begin(), problem.ns.end(), int64_t{0});
  Timing timing;
  const auto totalBegin = Clock::now();

  if (variant == Variant::IndependentBlis) {
    const auto computeBegin = Clock::now();
    for (size_t branch = 0; branch < problem.ns.size(); ++branch) {
      const int64_t n = problem.ns[branch];
      bli_sgemm(BLIS_NO_TRANSPOSE, BLIS_NO_TRANSPOSE, problem.m, n, problem.k,
                &alpha, problem.a.data(), problem.k, 1,
                problem.weights[branch].data(), n, 1, &beta,
                problem.outputs[branch].data(), n, 1);
    }
    timing.computeMs = elapsedMs(computeBegin, Clock::now());
  } else if (variant == Variant::ConcatenatedBlis) {
    const auto computeBegin = Clock::now();
    bli_sgemm(BLIS_NO_TRANSPOSE, BLIS_NO_TRANSPOSE, problem.m, totalN,
              problem.k, &alpha, problem.a.data(), problem.k, 1,
              problem.concatenatedWeights.data(), totalN, 1, &beta,
              problem.concatenatedOutput.data(), totalN, 1);
    timing.computeMs = elapsedMs(computeBegin, Clock::now());
  } else if (variant == Variant::RepackedAMicrokernel) {
    timing.packMs = 0.0;
    timing.computeMs = 0.0;
    for (size_t branch = 0; branch < problem.ns.size(); ++branch) {
      auto begin = Clock::now();
      packActivation(problem, problem.packedA);
      timing.packMs += elapsedMs(begin, Clock::now());
      begin = Clock::now();
      computeMicrokernelBranch(problem, problem.packedA,
                               problem.packedWeights[branch],
                               problem.outputs[branch], problem.ns[branch]);
      timing.computeMs += elapsedMs(begin, Clock::now());
    }
  } else {
    auto begin = Clock::now();
    packActivation(problem, problem.packedA);
    timing.packMs = elapsedMs(begin, Clock::now());
    begin = Clock::now();
    for (size_t branch = 0; branch < problem.ns.size(); ++branch)
      computeMicrokernelBranch(problem, problem.packedA,
                               problem.packedWeights[branch],
                               problem.outputs[branch], problem.ns[branch]);
    timing.computeMs = elapsedMs(begin, Clock::now());
  }

  timing.totalMs = elapsedMs(totalBegin, Clock::now());
  return timing;
}

void buildReference(Problem &problem) {
  execute(problem, Variant::IndependentBlis);
  problem.expected = problem.outputs;
}

struct CheckResult {
  float maxAbsDiff = 0.0f;
  float maxRelDiff = 0.0f;
  bool correct = true;
};

CheckResult checkVariant(Problem &problem, Variant variant) {
  execute(problem, variant);
  CheckResult result;
  const int64_t totalN =
      std::accumulate(problem.ns.begin(), problem.ns.end(), int64_t{0});
  int64_t offset = 0;
  for (size_t branch = 0; branch < problem.ns.size(); ++branch) {
    const int64_t n = problem.ns[branch];
    for (int64_t i = 0; i < problem.m; ++i)
      for (int64_t j = 0; j < n; ++j) {
        const float actual =
            variant == Variant::ConcatenatedBlis
                ? problem.concatenatedOutput[i * totalN + offset + j]
                : problem.outputs[branch][i * n + j];
        const float expected = problem.expected[branch][i * n + j];
        const float absDiff = std::fabs(actual - expected);
        const float relDiff = absDiff / std::max(std::fabs(expected), 1.0e-6f);
        result.maxAbsDiff = std::max(result.maxAbsDiff, absDiff);
        result.maxRelDiff = std::max(result.maxRelDiff, relDiff);
        if (absDiff > 1.0e-3f + 2.0e-4f * std::fabs(expected))
          result.correct = false;
      }
    offset += n;
  }
  return result;
}

struct Summary {
  double totalMedianMs = 0.0;
  double packMedianMs = -1.0;
  double computeMedianMs = 0.0;
};

Timing measureSample(Problem &problem, Variant variant, int innerIters) {
  Timing accumulated;
  accumulated.packMs = variant == Variant::IndependentBlis ||
                               variant == Variant::ConcatenatedBlis
                           ? -1.0
                           : 0.0;
  for (int inner = 0; inner < innerIters; ++inner) {
    const Timing value = execute(problem, variant);
    accumulated.totalMs += value.totalMs;
    accumulated.computeMs += value.computeMs;
    if (accumulated.packMs >= 0.0)
      accumulated.packMs += value.packMs;
  }
  accumulated.totalMs /= innerIters;
  accumulated.computeMs /= innerIters;
  if (accumulated.packMs >= 0.0)
    accumulated.packMs /= innerIters;
  return accumulated;
}

std::vector<Summary> benchmarkTrial(Problem &problem,
                                    const std::vector<Variant> &variants,
                                    int trial, int warmups, int repeats,
                                    int innerIters) {
  for (int warmup = 0; warmup < warmups; ++warmup)
    for (size_t order = 0; order < variants.size(); ++order) {
      const size_t index =
          (order + static_cast<size_t>(trial + warmup)) % variants.size();
      measureSample(problem, variants[index], innerIters);
    }

  std::vector<std::vector<double>> totals(variants.size());
  std::vector<std::vector<double>> packs(variants.size());
  std::vector<std::vector<double>> computes(variants.size());
  for (int repeat = 0; repeat < repeats; ++repeat)
    for (size_t order = 0; order < variants.size(); ++order) {
      const size_t index =
          (order + static_cast<size_t>(trial + repeat)) % variants.size();
      const Timing sample = measureSample(problem, variants[index], innerIters);
      totals[index].push_back(sample.totalMs);
      computes[index].push_back(sample.computeMs);
      if (sample.packMs >= 0.0)
        packs[index].push_back(sample.packMs);
    }

  std::vector<Summary> summaries;
  summaries.reserve(variants.size());
  for (size_t index = 0; index < variants.size(); ++index)
    summaries.push_back({median(totals[index]),
                         packs[index].empty() ? -1.0 : median(packs[index]),
                         median(computes[index])});
  return summaries;
}

int activationPackCount(Variant variant, int branches) {
  if (variant == Variant::RepackedAMicrokernel)
    return branches;
  if (variant == Variant::SharedAMicrokernel)
    return 1;
  return -1;
}

int blisCallCount(Variant variant, int branches) {
  if (variant == Variant::IndependentBlis)
    return branches;
  if (variant == Variant::ConcatenatedBlis)
    return 1;
  return 0;
}

} // namespace

int main(int argc, char **argv) {
  if (argc != 10) {
    std::cerr << "usage: region_fanout_bench REGION PHASE M K N1,N2,... "
                 "WARMUPS REPEATS INNER_ITERS TRIALS\n";
    return 2;
  }

  Problem problem;
  problem.region = argv[1];
  problem.phase = argv[2];
  problem.m = positive(argv[3], "M");
  problem.k = positive(argv[4], "K");
  problem.ns = parseNs(argv[5]);
  const int warmups = static_cast<int>(positive(argv[6], "warmups"));
  const int repeats = static_cast<int>(positive(argv[7], "repeats"));
  const int innerIters = static_cast<int>(positive(argv[8], "inner_iters"));
  const int trials = static_cast<int>(positive(argv[9], "trials"));

  bli_init();
  bli_thread_set_thread_impl(BLIS_SINGLE);
  bli_thread_set_num_threads(1);
  fillProblem(problem);
  preparePersistentRepresentations(problem);
  buildReference(problem);

  const std::vector<Variant> variants = {
      Variant::IndependentBlis, Variant::ConcatenatedBlis,
      Variant::RepackedAMicrokernel, Variant::SharedAMicrokernel};
  std::vector<CheckResult> checks;
  for (Variant variant : variants)
    checks.push_back(checkVariant(problem, variant));

  const int64_t totalN =
      std::accumulate(problem.ns.begin(), problem.ns.end(), int64_t{0});
  const int64_t aPackedBytes =
      ((problem.m + MR - 1) / MR) * problem.k * MR * sizeof(float);
  int64_t persistentWeightBytes = 0;
  int64_t microkernelCalls = 0;
  for (size_t branch = 0; branch < problem.ns.size(); ++branch) {
    persistentWeightBytes += static_cast<int64_t>(
        problem.packedWeights[branch].size() * sizeof(float));
    microkernelCalls += ((problem.m + MR - 1) / MR) *
                        ((problem.ns[branch] + NR - 1) / NR) *
                        ((problem.k + KC - 1) / KC);
  }
  const double flops =
      2.0 * static_cast<double>(problem.m) * problem.k * totalN;
  std::string branchNs = argv[5];
  std::replace(branchNs.begin(), branchNs.end(), ',', 'x');

  std::cout << "region,phase,m,k,branch_n,total_n,branch_count,variant,trial,"
               "inner_iters,total_median_ms,visible_pack_median_ms,"
               "compute_median_ms,region_gflops,activation_pack_count,"
               "blis_frontend_call_count,microkernel_call_count,packed_a_bytes,"
               "persistent_weight_bytes,persistent_weight_pack_ms,"
               "weight_concatenation_ms,max_abs_diff,max_rel_diff,status\n";

  for (int trial = 0; trial < trials; ++trial) {
    const std::vector<Summary> summaries =
        benchmarkTrial(problem, variants, trial, warmups, repeats, innerIters);
    for (size_t order = 0; order < variants.size(); ++order) {
      const size_t index =
          (order + static_cast<size_t>(trial)) % variants.size();
      const Variant variant = variants[index];
      const Summary &summary = summaries[index];
      const CheckResult &check = checks[index];
      std::cout << problem.region << ',' << problem.phase << ',' << problem.m
                << ',' << problem.k << ',' << branchNs << ',' << totalN << ','
                << problem.ns.size() << ',' << variantName(variant) << ','
                << (trial + 1) << ',' << innerIters << ',' << std::fixed
                << std::setprecision(6) << summary.totalMedianMs << ','
                << summary.packMedianMs << ',' << summary.computeMedianMs << ','
                << std::setprecision(3)
                << flops / (summary.totalMedianMs * 1.0e6) << ','
                << activationPackCount(variant, problem.ns.size()) << ','
                << blisCallCount(variant, problem.ns.size()) << ','
                << (variant == Variant::RepackedAMicrokernel ||
                            variant == Variant::SharedAMicrokernel
                        ? microkernelCalls
                        : 0)
                << ',' << aPackedBytes << ',' << persistentWeightBytes << ','
                << std::setprecision(6) << problem.persistentWeightPackMs << ','
                << problem.weightConcatenationMs << ',' << std::setprecision(8)
                << check.maxAbsDiff << ',' << check.maxRelDiff << ','
                << (check.correct ? "PASS" : "FAIL") << '\n';
    }
  }
  bli_finalize();
  return std::all_of(checks.begin(), checks.end(),
                     [](const CheckResult &check) { return check.correct; })
             ? 0
             : 1;
}
