#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
typedef struct { bool verbose; uint32_t flags; } Opts;
extern bool is_flag_set(uint8_t); extern bool low_bit_ne0_u8(uint8_t); extern bool low_bit_ne0_u32(uint32_t);
extern bool low_bit_eq1_u64(uint64_t); extern bool is_odd(uint32_t); extern bool is_odd_i32(int32_t);
extern bool bit3_shift(uint32_t); extern bool bit3_mask(uint32_t); extern bool is_even(uint32_t);
extern bool passthrough(bool); extern bool not_b(bool); extern bool and_b(bool,bool);
extern bool opts_verbose(const Opts*); extern bool opts_flag0(const Opts*); extern bool is_zero(uint32_t);
extern bool gt(int64_t,int64_t); extern bool get_bit_u8(uint8_t,uint32_t); extern bool sys_low_bit(uint32_t);
typedef bool (*Cb)(uint32_t); extern Cb get_callback(void);
static int bad = 0;
static void show(const char *call, bool r, int expect) {
  unsigned char raw; __builtin_memcpy(&raw, &r, 1);
  int wrong = raw != expect; bad += wrong;
  printf("%-26s expect=%d raw=0x%02x %s\n", call, expect, raw, wrong ? "<-- NOT 0/1 (C reads it as true)" : "ok");
}
int main(void) {
  Opts o = { false, 0x6 };
  show("is_flag_set(0x10)", is_flag_set(0x10), 0);
  show("low_bit_ne0_u8(0x10)", low_bit_ne0_u8(0x10), 0);
  show("low_bit_ne0_u32(0x10)", low_bit_ne0_u32(0x10), 0);
  show("low_bit_eq1_u64(0x10)", low_bit_eq1_u64(0x10), 0);
  show("is_odd(16)", is_odd(16), 0);
  show("is_odd_i32(16)", is_odd_i32(16), 0);
  show("bit3_shift(0x30)", bit3_shift(0x30), 0);
  show("bit3_mask(0x30)", bit3_mask(0x30), 0);
  show("is_even(3)", is_even(3), 0);
  show("passthrough(false)", passthrough(false), 0);
  show("not_b(true)", not_b(true), 0);
  show("and_b(true,false)", and_b(true,false), 0);
  show("opts_verbose(&o)", opts_verbose(&o), 0);
  show("opts_flag0(&o)", opts_flag0(&o), 0);
  show("is_zero(16)", is_zero(16), 0);
  show("gt(1,2)", gt(1,2), 0);
  show("get_bit_u8(0x12,0)", get_bit_u8(0x12,0), 0);
  show("sys_low_bit(0x10)", sys_low_bit(0x10), 0);
  show("get_callback()(0x10)", get_callback()(0x10), 0);
  printf("WRONG=%d\n", bad); return 0;
}
