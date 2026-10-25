// ────────────────────────────────────────────────────────────────────────────────
// H.U.S.A.R.Z. — Holomorficzny Uziemiony Splotowy Aktywator Rezonatora Zibi (v1.04)
// Licencja: CC BY-NC-ND 4.0 | Łukasz Włodarski | System Labs (Koszalin, 2026)
// ────────────────────────────────────────────────────────────────────────────────

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <cstdint>
#include <omp.h>
#include <windows.h>
#include <intrin.h>

namespace py = pybind11;

constexpr int64_t BAZA_A0      = 585;
constexpr int64_t GTS_KROK     = 91;
constexpr int64_t BARRIER_S22  = 22;
constexpr int64_t DELTA_ML     = 17;

#if defined(_MSC_VER)
    #define FAST_INLINE __forceinline
#else
    #define FAST_INLINE inline
#endif

struct WlodarskiTensor {
    int64_t pion_44;       
    int64_t fala_pilot;    
    int64_t status_mod9;   
    int64_t status_mod10;  
    int64_t x;             
    int64_t y;             
    int64_t z;             
    int64_t popcount_val;  
};

static FAST_INLINE uint64_t fast_hex_digit_sum_tree(uint64_t u) {
    u = (u & 0x0F0F0F0F0F0F0F0FULL) + ((u >> 4) & 0x0F0F0F0F0F0F0F0FULL);
    u = (u & 0x00FF00FF00FF00FFULL) + ((u >> 8) & 0x00FF00FF00FF00FFULL);
    u = (u & 0x0000FFFF0000FFFFULL) + ((u >> 16) & 0x0000FFFF0000FFFFULL);
    return (u & 0x00000000FFFFFFFFULL) + (u >> 32);
}

static FAST_INLINE uint64_t fast_sys20_digit_sum_tree(uint64_t u) {
    u = (u & 0x0F07C1F07C1F07C1ULL) + ((u >> 5) & 0x0F07C1F07C1F07C1ULL);
    u = (u & 0x001F001F001F001FULL) + ((u >> 10) & 0x001F001F001F001FULL);
    u = (u & 0x000003FF000003FFULL) + ((u >> 20) & 0x000003FF000003FFULL);
    return (u & 0x00000000000FFFFFULL) + (u >> 40);
}

static FAST_INLINE uint64_t fast_sys60_digit_sum_tree(uint64_t u) {
    u = (u & 0x3F03F03F03F03F03ULL) + ((u >> 6) & 0x3F03F03F03F03F03ULL);
    u = (u & 0x000FFF000FFF000FULL) + ((u >> 12) & 0x000FFF000FFF000FULL);
    u = (u & 0x00000000FFFFFF00ULL) + ((u >> 24) & 0x00000000FFFFFF00ULL);
    return (u & 0x000000000000FFFFULL) + (u >> 48);
}

static FAST_INLINE uint64_t fast_hardware_popcount_s2(uint64_t u) {
    return __popcnt64(static_cast<unsigned __int64>(u));
}

static FAST_INLINE uint64_t fast_gray_code_sum_tree(uint64_t u) {
    u = (u & 0x5555555555555555ULL) + ((u >> 1) & 0x5555555555555555ULL);
    u = (u & 0x3333333333333333ULL) + ((u >> 2) & 0x3333333333333333ULL);
    u = (u & 0x0F0F0F0F0F0F0F0FULL) + ((u >> 4) & 0x0F0F0F0F0F0F0F0FULL);
    u = (u & 0x00FF00FF00FF00FFULL) + ((u >> 8) & 0x00FF00FF00FF00FFULL);
    u = (u & 0x0000FFFF0000FFFFULL) + ((u >> 16) & 0x0000FFFF0000FFFFULL);
    return (u & 0x00000000FFFFFFFFULL) + (u >> 32);
}

static FAST_INLINE uint64_t fast_base12_sum_tree(uint64_t u) {
    u = (u & 0x0F0F0F0F0F0F0F0FULL) + ((u >> 4) & 0x0F0F0F0F0F0F0F0FULL);
    u = (u & 0x00FF00FF00FF00FFULL) + ((u >> 8) & 0x00FF00FF00FF00FFULL);
    u = (u & 0x0000FFFF0000FFFFULL) + ((u >> 16) & 0x0000FFFF0000FFFFULL);
    uint64_t sum = (u & 0x00000000FFFFFFFFULL) + (u >> 32);
    uint64_t q = __umulh(sum, 0x2E8BA2E8BA2E8BA3ULL) >> 3;
    return (sum - q * 11);
}

static FAST_INLINE uint64_t fast_base10_sum_tree(uint64_t u) {
    uint64_t sum = 0;
    while (u > 0) {
        uint64_t q = __umulh(u, 0xCCCCCCCCCCCCCCCDULL) >> 3;
        sum += (u - q * 10);
        u = q;
    }
    uint64_t q_mod9 = __umulh(sum, 0x1C71C71C71C71C72ULL) >> 3;
    return (sum - q_mod9 * 9);
}

static FAST_INLINE int64_t fast_modulo_11(uint64_t val) {
    uint64_t q = __umulh(val, 0x2E8BA2E8BA2E8BA3ULL) >> 3;
    return static_cast<int64_t>(val - q * 11);
}

static FAST_INLINE int64_t fast_modulo_20(uint64_t val) {
    uint64_t q = __umulh(val, 0xCCCDCCCCCCCCCCCDULL) >> 4;
    return static_cast<int64_t>(val - q * 20);
}

static FAST_INLINE int64_t fast_modulo_60(uint64_t val) {
    uint64_t q = __umulh(val, 0x4444444444444445ULL) >> 4;
    return static_cast<int64_t>(val - q * 60);
}

template <int64_t SYS_BASE>
FAST_INLINE void execute_pipeline(int64_t start_global_idx, int64_t* __restrict output_data, int64_t size) {
    #pragma omp parallel for schedule(static)
    for (int64_t i = 0; i < size; ++i) {
        int64_t current_global_idx = start_global_idx + i;
        int64_t val = BAZA_A0 + GTS_KROK * current_global_idx;
        uint64_t uval = static_cast<uint64_t>(val);
        
        uint64_t s = 0;
        if constexpr (SYS_BASE == 16)      s = fast_hex_digit_sum_tree(uval);
        else if constexpr (SYS_BASE == 20) s = fast_sys20_digit_sum_tree(uval);
        else if constexpr (SYS_BASE == 60) s = fast_sys60_digit_sum_tree(uval);
        else if constexpr (SYS_BASE == 2)  s = fast_hardware_popcount_s2(uval);
        else if constexpr (SYS_BASE == 4)  s = fast_gray_code_sum_tree(uval);
        else if constexpr (SYS_BASE == 12) s = fast_base12_sum_tree(uval);
        else if constexpr (SYS_BASE == 10) s = fast_base10_sum_tree(uval);
        
        int64_t mask_pendulum = (static_cast<int64_t>(s) > 18) ? 1LL : 0LL;
        int64_t new_val = val - GTS_KROK * mask_pendulum; 
        uint64_t u_new_val = static_cast<uint64_t>(new_val);
        
        uint64_t new_s = 0;
        if constexpr (SYS_BASE == 16)      new_s = fast_hex_digit_sum_tree(u_new_val);
        else if constexpr (SYS_BASE == 20) new_s = fast_sys20_digit_sum_tree(u_new_val);
        else if constexpr (SYS_BASE == 60) new_s = fast_sys60_digit_sum_tree(u_new_val);
        else if constexpr (SYS_BASE == 2)  new_s = fast_hardware_popcount_s2(u_new_val);
        else if constexpr (SYS_BASE == 4)  new_s = fast_gray_code_sum_tree(u_new_val);
        else if constexpr (SYS_BASE == 12) new_s = fast_base12_sum_tree(u_new_val);
        else if constexpr (SYS_BASE == 10) new_s = fast_base10_sum_tree(u_new_val);
        
        int64_t mask_barrier = (static_cast<int64_t>(new_s) >= BARRIER_S22) ? 1LL : 0LL;
        new_val = new_val - DELTA_ML * mask_barrier; 
        uint64_t u_final = static_cast<uint64_t>(new_val);
        
        if constexpr (SYS_BASE == 16)      output_data[i] = fast_modulo_11(u_final);
        else if constexpr (SYS_BASE == 20) output_data[i] = fast_modulo_20(u_final);
        else if constexpr (SYS_BASE == 60) output_data[i] = fast_modulo_60(u_final);
        else if constexpr (SYS_BASE == 2) {
            output_data[i] = static_cast<int64_t>(u_final & 0x1LL);
        }
        else if constexpr (SYS_BASE == 4) {
            output_data[i] = static_cast<int64_t>(u_final & 0x3LL);
        }
        else if constexpr (SYS_BASE == 12) {
            output_data[i] = fast_modulo_11(u_final);
        }
        else if constexpr (SYS_BASE == 10) {
            uint64_t q = __umulh(u_final, 0x4EC4EC4EC4EC4EC5ULL) >> 2;
            output_data[i] = static_cast<int64_t>(u_final - q * 13);
        }
    }
}

void process_batch(int64_t start_global_idx, py::array_t<int64_t, py::array::c_style | py::array::forcecast> output, int64_t system_base) {
    py::gil_scoped_release release;

    int64_t* __restrict output_data = output.mutable_data();
    int64_t size = static_cast<int64_t>(output.size());

    if (system_base == 20) {
        execute_pipeline<20>(start_global_idx, output_data, size);
    } else if (system_base == 60) {
        execute_pipeline<60>(start_global_idx, output_data, size);
    } else if (system_base == 2) {
        execute_pipeline<2>(start_global_idx, output_data, size);
    } else if (system_base == 4) {
        execute_pipeline<4>(start_global_idx, output_data, size);
    } else if (system_base == 12) {
        execute_pipeline<12>(start_global_idx, output_data, size);
    } else if (system_base == 10) {
        execute_pipeline<10>(start_global_idx, output_data, size);
    } else {
        execute_pipeline<16>(start_global_idx, output_data, size);
    }
}

WlodarskiTensor compute_tensor(int64_t val) {
    WlodarskiTensor t;
    t.pion_44    = val % 13; 
    t.fala_pilot = 4;        
    t.status_mod9  = static_cast<int64_t>(fast_hex_digit_sum_tree(static_cast<uint64_t>(val)) % 9);
    t.status_mod10 = val % 10;
    t.x = val % 11;
    t.y = val % 8;   
    t.z = val % 5;
    t.popcount_val = __popcnt64(static_cast<unsigned __int64>(val)); 
    return t;
}

void set_thread_affinity() {
#if defined(_WIN32) || defined(_WIN64)
    DWORD_PTR affinity_mask = 0xFFFFFFFFFFFFFFFF;
    SetThreadAffinityMask(GetCurrentThread(), affinity_mask);
#endif
}

PYBIND11_MODULE(husarz, m) {
    m.doc() = "Echokosmos - Husarz v1.04";

    py::class_<WlodarskiTensor>(m, "WlodarskiTensor")
        .def(py::init<>())
        .def_readwrite("pion_44",       &WlodarskiTensor::pion_44)
        .def_readwrite("fala_pilot",    &WlodarskiTensor::fala_pilot)
        .def_readwrite("status_mod9",   &WlodarskiTensor::status_mod9)
        .def_readwrite("status_mod10",  &WlodarskiTensor::status_mod10)
        .def_readwrite("x",             &WlodarskiTensor::x)
        .def_readwrite("y",             &WlodarskiTensor::y)
        .def_readwrite("z",             &WlodarskiTensor::z)
        .def_readwrite("popcount_val",  &WlodarskiTensor::popcount_val);

    m.def("process_batch",        &process_batch,        "process_batch", py::arg("start_global_idx"), py::arg("output"), py::arg("system_base") = 16);
    m.def("compute_tensor",       &compute_tensor,       "compute_tensor", py::arg("val"));
    m.def("set_thread_affinity",  &set_thread_affinity,  "set_thread_affinity");
}
