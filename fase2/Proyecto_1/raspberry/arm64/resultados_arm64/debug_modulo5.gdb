set confirm off
set pagination off
set architecture aarch64

target remote :1235

break imprimir_y_guardar
continue

info registers x19 x20 x21 x22 x23 x24 x25 x26 x27 x28

p/d *(long*)&increments_mem
p/d *(long*)&decrements_mem
p/d *(long*)&max_up_mem
p/d *(long*)&max_down_mem
p/d *(long*)&accum_diff_mem

x/30gx &values

detach
quit