
.text
.global sqrt_int

sqrt_int:
    mov x1, x0
    mov x2, #0

sqrt_loop:
    add x3, x2, #1
    mul x4, x3, x3

    cmp x4, x1
    bgt sqrt_done

    mov x2, x3
    b sqrt_loop

sqrt_done:
    mov x0, x2
    ret
