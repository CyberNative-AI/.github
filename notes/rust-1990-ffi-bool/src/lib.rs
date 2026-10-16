// Exported C-ABI functions that return bool. Each is a plausible real-world shape.
#[repr(C)]
pub struct Opts { pub verbose: bool, pub flags: u32 }

#[unsafe(no_mangle)] pub extern "C" fn is_flag_set(flags: u8) -> bool { (flags & 0x1) == 0x1 }
#[unsafe(no_mangle)] pub extern "C" fn low_bit_ne0_u8(x: u8) -> bool { x & 1 != 0 }
#[unsafe(no_mangle)] pub extern "C" fn low_bit_ne0_u32(x: u32) -> bool { x & 1 != 0 }
#[unsafe(no_mangle)] pub extern "C" fn low_bit_eq1_u64(x: u64) -> bool { x & 1 == 1 }
#[unsafe(no_mangle)] pub extern "C" fn is_odd(n: u32) -> bool { n % 2 == 1 }
#[unsafe(no_mangle)] pub extern "C" fn is_odd_i32(n: i32) -> bool { n % 2 != 0 }
#[unsafe(no_mangle)] pub extern "C" fn bit3_shift(x: u32) -> bool { (x >> 3) & 1 == 1 }
#[unsafe(no_mangle)] pub extern "C" fn bit3_mask(x: u32) -> bool { x & 8 != 0 }
#[unsafe(no_mangle)] pub extern "C" fn is_even(n: u32) -> bool { n % 2 == 0 }
#[unsafe(no_mangle)] pub extern "C" fn passthrough(b: bool) -> bool { b }
#[unsafe(no_mangle)] pub extern "C" fn not_b(b: bool) -> bool { !b }
#[unsafe(no_mangle)] pub extern "C" fn and_b(a: bool, b: bool) -> bool { a && b }
#[unsafe(no_mangle)] pub extern "C" fn opts_verbose(o: *const Opts) -> bool { unsafe { (*o).verbose } }
#[unsafe(no_mangle)] pub extern "C" fn opts_flag0(o: *const Opts) -> bool { unsafe { (*o).flags & 1 != 0 } }
#[unsafe(no_mangle)] pub extern "C" fn is_zero(x: u32) -> bool { x == 0 }
#[unsafe(no_mangle)] pub extern "C" fn gt(a: i64, b: i64) -> bool { a > b }
#[unsafe(no_mangle)] pub extern "C" fn get_bit_u8(x: u8, n: u32) -> bool { (x >> n) & 1 == 1 }
#[unsafe(no_mangle)] pub extern "system" fn sys_low_bit(x: u32) -> bool { x & 1 != 0 }
pub type Cb = extern "C" fn(u32) -> bool;
#[unsafe(no_mangle)] pub extern "C" fn get_callback() -> Cb { cb_impl }
extern "C" fn cb_impl(x: u32) -> bool { x & 1 != 0 }
