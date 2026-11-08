# Local BaCO Deployment

- Source: <https://github.com/baco-authors/baco>
- Pinned commit: `167b19699ead224b661da4abad560306f677e215`
- Package version: `3.0.0`
- Local path: `/buddy-mlir/jlq/thesis/third_party/baco`
- Python: system Python 3.10.12

The package metadata declares Python `<=3.10`, which rejects patch release 3.10.12 under modern packaging interpretation. The editable checkout was therefore installed with `--ignore-requires-python --no-deps`, followed by explicit compatible dependencies. `setuptools` is pinned below 81 because this BaCO commit imports the deprecated `pkg_resources` API.

The Chapter 4 driver uses unmodified BaCO. Expert knowledge is supplied through the finite schedule lookup, parameter domain, default point, and external provenance files; BaCO's probabilistic model is not changed.
