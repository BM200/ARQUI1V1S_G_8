set confirm off
set pagination off
set architecture aarch64

target remote :1232

break imprimir_y_guardar
continue

info registers x19 x20 x21 x22 x23 x24 x25 x26 x27 x28

p/d *(long*)&mean_mem
p/d *(long*)&variance_mem
p/d *(long*)&std_mem

x/30gx &values

detach
quit
