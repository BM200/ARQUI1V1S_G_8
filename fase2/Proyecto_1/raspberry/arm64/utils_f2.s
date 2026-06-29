

.data

filename:
    .asciz "lecturas.csv"

.bss
buffer:
    .skip 64

.text
.global contar_lineas_archivo
.global obtener_indice_columna
.global atoi_csv
.global validar_rango
.global validar_columna
.global sumar_arreglo
.global promedio_arreglo
.global maximo_arreglo
.global minimo_arreglo
.global copiar_rango
.global contar_elementos_rango

// ----------------------------------------------------------------------------
// contar_lineas_archivo
// ----------------------------------------------------------------------------

contar_lineas_archivo:

    mov x24, #0

    mov x0, #-100
    ldr x1, =filename
    mov x2, #0
    mov x3, #0
    mov x8, #56
    svc #0

    cmp x0, #0
    blt error

    mov x19, x0

    loop:
        mov x0, x19
        ldr x1, =buffer
        mov x2, #64
        mov x8, #63
        svc #0

        cmp x0, #0
        beq done
        blt error

        mov x20, x0
        ldr x21, =buffer
        mov x22, #0

    loop2:
        cmp x22, x20
        bge loop

        ldrb w23, [x21], #1
        add x22, x22, #1

        cmp w23, #10
        bne loop2

        add x24, x24, #1
        b loop2

    done:
        mov x0, x19
        mov x8, #57
        svc #0

        mov x0, x24
        ret

    error:
        mov x0, #0
        ret

// ----------------------------------------------------------------------------
// obtener_indice_columna
// ----------------------------------------------------------------------------
obtener_indice_columna:

    ldrb w1,[x0]

    cmp w1,'T'
    beq temp

    cmp w1,'H'
    beq hum

    cmp w1,'S'
    beq soil

    cmp w1,'L'
    beq luz

    cmp w1,'G'
    beq gas

    cmp w1,'R'
    beq riego

    mov x0,#0
    ret

    temp:
        mov x0,#2
        ret

    hum:
        mov x0,#3
        ret

    luz:
        mov x0,#6
        ret

    gas:
        mov x0,#7
        ret

    soil:

        ldrb w2,[x0,#10]

        cmp w2,'1'
        beq soil1

        cmp w2,'2'
        beq soil2

        mov x0,#0
        ret

    soil1:
        mov x0,#4
        ret

    soil2:
        mov x0,#5
        ret

    riego:

        ldrb w2,[x0,#6]

        cmp w2,'1'
        beq riego1

        cmp w2,'2'
        beq riego2

        mov x0,#0
        ret

    riego1:
        mov x0,#8
        ret

    riego2:
        mov x0,#9
        ret

// ----------------------------------------------------------------------------
// atoi_csv
// ----------------------------------------------------------------------------
atoi_csv:

    mov x10,#0
    mov x7,#0

    atoi_loop:

        ldrb w23,[x21],#1

        cmp w23,'0'
        blt atoi_done

        cmp w23,'9'
        bgt atoi_done

        sub w23,w23,'0'

        mov x4,x10
        mov x5,#10
        mul x10,x4,x5

        add x10,x10,x23

        mov x7,#1

        b atoi_loop

    atoi_done:
        ret

// ----------------------------------------------------------------------------
// validar_rango
// ----------------------------------------------------------------------------
validar_rango:

    cmp x0,#1
    blt rango_error

    cmp x1,x0
    blt rango_error

    cmp x1,x2
    bgt rango_error

    mov x0,#1
    ret

rango_error:

    mov x0,#0
    ret

// ----------------------------------------------------------------------------
// validar_columna
// ----------------------------------------------------------------------------

validar_columna:

    cmp x0,#2
    blt col_error

    cmp x0,#9
    bgt col_error

    mov x0,#1
    ret

    col_error:

        mov x0,#0
        ret

// ----------------------------------------------------------------------------
// sumar_arreglo
// ----------------------------------------------------------------------------

sumar_arreglo:

    mov x2,#0
    mov x3,#0

    sum_loop:

        cmp x3,x1
        bge sum_done

        ldr x4,[x0,x3,lsl #3]

        add x2,x2,x4

        add x3,x3,#1

        b sum_loop

    sum_done:

        mov x0,x2
        ret

// ----------------------------------------------------------------------------
// promedio_arreglo
// ----------------------------------------------------------------------------
promedio_arreglo:

    stp x29,x30,[sp,#-16]!
    mov x29,sp

    str x20,[sp,#-16]!

    mov x20,x1

    cbz x20,promedio_cero

    bl sumar_arreglo

    udiv x0,x0,x20

    b promedio_fin

    promedio_cero:
        mov x0,#0

    promedio_fin:

        ldr x20,[sp],#16

        ldp x29,x30,[sp],#16
        ret


// ----------------------------------------------------------------------------
// maximo_arreglo
// ----------------------------------------------------------------------------
maximo_arreglo:

    cbz x1,max_vacio

    ldr x2,[x0]
    mov x3,#1

    max_loop:

        cmp x3,x1
        bge max_done

        ldr x4,[x0,x3,lsl #3]

        cmp x4,x2
        ble max_next

        mov x2,x4

    max_next:

        add x3,x3,#1
        b max_loop

    max_done:

        mov x0,x2
        ret

    max_vacio:

        mov x0,#0
        ret


// ----------------------------------------------------------------------------
// minimo_arreglo
// ----------------------------------------------------------------------------

minimo_arreglo:

    cbz x1,min_vacio

    ldr x2,[x0]
    mov x3,#1

    min_loop:

        cmp x3,x1
        bge min_done

        ldr x4,[x0,x3,lsl #3]

        cmp x4,x2
        bge min_next

        mov x2,x4

    min_next:

        add x3,x3,#1
        b min_loop

    min_done:

        mov x0,x2
        ret

    min_vacio:

        mov x0,#0
        ret

// ----------------------------------------------------------------------------
// copiar_rango
// ----------------------------------------------------------------------------
copiar_rango:

    mov x4,#0

    copy_loop:

        cmp x2,x3
        bgt copy_done

        ldr x5,[x0,x2,lsl #3]

        str x5,[x1,x4,lsl #3]

        add x2,x2,#1
        add x4,x4,#1

        b copy_loop

    copy_done:

        mov x0,x4
        ret


// ----------------------------------------------------------------------------
// contar_elementos_rango
// ----------------------------------------------------------------------------
contar_elementos_rango:

    sub x0,x1,x0
    add x0,x0,#1
    ret
