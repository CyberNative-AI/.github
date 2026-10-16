// Fixture for scripts/find-bool-exports.sh: the first five functions should match, the rest should not.
#[no_mangle]
pub unsafe extern "C" fn multi_line(
    a: *const u8,
    len: usize,
) -> bool { true }
#[no_mangle] pub extern "C" fn with_fnptr(cb: extern "C" fn(u32) -> u32, x: u32) -> bool { cb(x) == 0 }
#[no_mangle] pub extern fn old_style(x: u32) -> bool { x & 1 != 0 }
#[no_mangle] pub extern "C-unwind" fn unwind(x: u32) -> bool { x & 1 != 0 }
#[no_mangle] pub extern "C" fn generic_ok<'a>(x: &'a u8) -> bool { *x == 0 }
extern "C" { fn imported(x: u32) -> bool; }
pub fn plain(x: u32) -> bool { x & 1 != 0 }
#[no_mangle] pub extern "C" fn returns_u8(x: u32) -> u8 { (x & 1) as u8 }
#[no_mangle] pub extern "C" fn returns_opt(x: u32) -> Option<bool> { None }
#[no_mangle] pub extern "C" fn boolish(x: u32) -> bool_t { 0 }
