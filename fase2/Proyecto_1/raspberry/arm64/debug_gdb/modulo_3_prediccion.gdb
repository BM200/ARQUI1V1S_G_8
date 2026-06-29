set pagination off
set confirm off
target remote :1238
break _start
continue
info registers
x/8i $pc
si
si
si
si
si
info registers x0 x1 x2 x3 x4 x8 sp pc
x/12gx $sp
quit
