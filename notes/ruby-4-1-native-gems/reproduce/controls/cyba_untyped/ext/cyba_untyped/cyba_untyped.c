#include <ruby.h>
struct box { long v; };
static VALUE alloc(VALUE klass) { struct box *b; return Data_Make_Struct(klass, struct box, 0, -1, b); }
static VALUE get(VALUE self) { struct box *b; Data_Get_Struct(self, struct box, b); return LONG2NUM(b->v + 41); }
void Init_cyba_untyped(void) { VALUE c = rb_define_class("CybaUntyped", rb_cObject); rb_define_alloc_func(c, alloc); rb_define_method(c, "get", get, 0); }
