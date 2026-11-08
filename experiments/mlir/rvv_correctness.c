static float a[64];
static float b[64];
static float c[64];

__attribute__((noinline))
void saxpy_check_kernel(int n, const float *x, const float *y, float *z) {
  for (int i = 0; i < n; ++i) {
    z[i] = x[i] + y[i];
  }
}

static void sys_exit(int code) {
  register long a0 asm("a0") = code;
  register long a7 asm("a7") = 93;
  asm volatile("ecall" : : "r"(a0), "r"(a7) : "memory");
  __builtin_unreachable();
}

void _start(void) {
  for (int i = 0; i < 64; ++i) {
    a[i] = (float)i;
    b[i] = (float)(2 * i + 1);
    c[i] = 0.0f;
  }

  saxpy_check_kernel(64, a, b, c);

  int errors = 0;
  for (int i = 0; i < 64; ++i) {
    float expected = (float)(3 * i + 1);
    if (c[i] != expected) {
      ++errors;
    }
  }

  sys_exit(errors == 0 ? 0 : 1);
}
