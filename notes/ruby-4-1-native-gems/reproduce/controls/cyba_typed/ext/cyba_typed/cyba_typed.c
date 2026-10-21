#include <ruby.h>
struct box { long v; };
static const rb_data_type_t box_type = { "box", { 0, RUBY_TYPED_DEFAULT_FREE, 0 }, 0, 0, RUBY_TYPED_FREE_IMMEDIATELY };
static VALUE alloc(VALUE klass) { struct box *b; return TypedData_Make_Struct(klass, struct box, &box_type, b); }
static VALUE get(VALUE self) { struct box *b; TypedData_Get_Struct(self, struct box, &box_type, b); return LONG2NUM(b->v + 41); }
void Init_cyba_typed(void) { VALUE c = rb_define_class("CybaTyped", rb_cObject); rb_define_alloc_func(c, alloc); rb_define_method(c, "get", get, 0); }
