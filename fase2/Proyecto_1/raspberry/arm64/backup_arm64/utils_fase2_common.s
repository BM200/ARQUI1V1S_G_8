
        .data
col_temp:          .asciz "TEMP"
header_temp:       .asciz "TEMP"
        .equ HEADER_TEMP_LEN, 4
col_hum_aire:      .asciz "HUM_AIRE"
header_hum_aire:   .asciz "HUM_AIRE"
        .equ HEADER_HUM_AIRE_LEN, 8
col_soil1:         .asciz "SOIL1"
header_soil1:      .asciz "HUM_SUELO_1"
        .equ HEADER_SOIL1_LEN, 11
col_soil2:         .asciz "SOIL2"
header_soil2:      .asciz "HUM_SUELO_2"
        .equ HEADER_SOIL2_LEN, 11
col_luz:           .asciz "LUZ"
header_luz:        .asciz "LUZ"
        .equ HEADER_LUZ_LEN, 3
col_gas:           .asciz "GAS"
header_gas:        .asciz "GAS"
        .equ HEADER_GAS_LEN, 3

        .bss
        .balign 8
common_number_buffer:
        .skip 64

        .text
        .global parse_uint
        .global parse_int_cstr
        .global parse_int_span
        .global cstrlen
        .global match_cstr
        .global bytes_equal
        .global write_stdout
        .global write_number_field
        .global int_to_ascii
        .global abs_int
        .global select_requested_column
        .global find_header_column

parse_uint:
        mov x2, #0                 // acumulador del numero
        mov x3, #0                 // cuenta digitos leidos
parse_uint_loop:
        ldrb w4, [x0], #1          // leo un caracter y avanzo
        cbz w4, parse_uint_done    // cero marca fin de string
        cmp w4, #48
        blt parse_uint_invalid
        cmp w4, #57
        bgt parse_uint_invalid
        mov x5, #10
        mul x2, x2, x5             // desplazo decimal: valor * 10
        sub w4, w4, #48            // paso ASCII a digito
        add x2, x2, x4             // agrego digito al acumulador
        add x3, x3, #1
        b parse_uint_loop
parse_uint_done:
        cbz x3, parse_uint_invalid // si no hubo digitos, es invalido
        mov x0, x2
        mov x1, #1
        ret
parse_uint_invalid:
        mov x0, #0
        mov x1, #0
        ret

parse_int_cstr:
        mov x2, #0                 // acumulador del numero
        mov x3, #0                 // cuenta digitos validos
        mov x4, #0                 // bandera de signo negativo
        ldrb w5, [x0]
        cmp w5, #45                // reviso si empieza con '-'
        bne parse_int_cstr_loop
        mov x4, #1
        add x0, x0, #1
parse_int_cstr_loop:
        ldrb w5, [x0], #1
        cbz w5, parse_int_cstr_done
        cmp w5, #48
        blt parse_int_cstr_invalid
        cmp w5, #57
        bgt parse_int_cstr_invalid
        mov x6, #10
        mul x2, x2, x6             // valor = valor * 10
        sub w5, w5, #48            // ASCII a digito
        add x2, x2, x5
        add x3, x3, #1
        b parse_int_cstr_loop
parse_int_cstr_done:
        cbz x3, parse_int_cstr_invalid // no acepta string vacio o solo '-'
        cbz x4, parse_int_cstr_positive
        neg x2, x2                 // aplico signo negativo
parse_int_cstr_positive:
        mov x0, x2
        mov x1, #1
        ret
parse_int_cstr_invalid:
        mov x0, #0
        mov x1, #0
        ret


parse_int_span:
        cmp x0, x1                 // campo vacio no es valido
        bge parse_int_invalid
        mov x2, #0                 // acumulador
        mov x3, #0                 // cantidad de digitos
        mov x4, #0                 // bandera de signo negativo
        ldrb w5, [x0]
        cmp w5, #45                // signo '-' opcional
        bne parse_int_loop
        mov x4, #1
        add x0, x0, #1
        cmp x0, x1
        bge parse_int_invalid
parse_int_loop:
        cmp x0, x1
        bge parse_int_done
        ldrb w5, [x0], #1
        cmp w5, #48
        blt parse_int_invalid
        cmp w5, #57
        bgt parse_int_invalid
        mov x6, #10
        mul x2, x2, x6             // desplazo decimal
        sub w5, w5, #48            // convierto ASCII a digito
        add x2, x2, x5
        add x3, x3, #1
        b parse_int_loop
parse_int_done:
        cbz x3, parse_int_invalid
        cbz x4, parse_int_positive
        neg x2, x2
parse_int_positive:
        mov x0, x2
        mov x1, #1
        ret
parse_int_invalid:
        mov x0, #0
        mov x1, #0
        ret


// Calcula longitud de un string terminado en cero
// Entrada: x0 = puntero al string
// Salida:  x0 = longitud sin contar el cero final
cstrlen:
        mov x1, x0
cstrlen_loop:
        ldrb w2, [x1], #1          // avanzo hasta encontrar cero
        cbnz w2, cstrlen_loop
        sub x0, x1, x0
        sub x0, x0, #1
        ret


// Compara dos strings terminados en cero
// Entrada: x0 = string A, x1 = string B
// Salida:  x0 = 1 si son iguales, 0 si no
match_cstr:
        ldrb w2, [x0], #1
        ldrb w3, [x1], #1
        cmp w2, w3                 // comparo caracter por caracter
        bne match_false
        cbnz w2, match_cstr
        mov x0, #1
        ret
match_false:
        mov x0, #0
        ret

// bytes_equal
// Compara dos bloques de bytes con longitudes conocidas
// Entrada: x0 = bloque A, x1 = len A, x2 = bloque B, x3 = len B
// Salida:  x0 = 1 si son iguales, 0 si no
bytes_equal:
        cmp x1, x3                 // si las longitudes cambian, no son iguales
        bne bytes_false
        mov x4, #0
bytes_loop:
        cmp x4, x1
        bge bytes_true
        ldrb w5, [x0, x4]          // byte del primer texto
        ldrb w6, [x2, x4]          // byte del segundo texto
        cmp w5, w6
        bne bytes_false
        add x4, x4, #1
        b bytes_loop
bytes_true:
        mov x0, #1
        ret
bytes_false:
        mov x0, #0
        ret


// Escribe un bloque de texto en stdout usando syscall write
// Entrada: x0 = puntero, x1 = longitud
// Salida:  devuelve lo que retorne el syscall en x0
write_stdout:
        mov x2, x1                 // x2 lleva cantidad de bytes
        mov x1, x0                 // x1 lleva direccion del texto
        mov x0, #1                 // fd 1 = stdout
        mov x8, #64                // syscall write
        svc #0
        ret

// write_number_field
// Imprime una etiqueta y despues un numero entero
// Entrada: x0 = texto, x1 = len texto, x2 = numero
write_number_field:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        mov x13, x2                // guardo numero mientras imprimo etiqueta
        bl write_stdout            // escribo el nombre del campo
        mov x0, x13
        bl int_to_ascii            // convierto numero a texto
        bl write_stdout            // imprimo el numero convertido
        ldp x29, x30, [sp], #16
        ret

// int_to_ascii
// Convierte entero con signo a texto decimal 
// Entrada: x0 = numero.
// Salida:  x0 = puntero al texto, x1 = longitud
int_to_ascii:
        ldr x2, =common_number_buffer
        add x2, x2, #63            // escribo desde el final del buffer
        mov x3, #0
        strb w3, [x2]
        mov x3, x0
        mov x4, #0
        cmp x3, #0
        bge int_abs_ready
        mov x4, #1                 // marco que hay signo negativo
        neg x3, x3                 // uso valor absoluto para convertir
int_abs_ready:
        cmp x3, #0
        bne int_convert
        sub x2, x2, #1
        mov w5, #48
        strb w5, [x2]
        b int_sign
int_convert:
        cmp x3, #0
        beq int_sign
        mov x5, #10
        udiv x6, x3, x5            // division entera entre 10
        msub x7, x6, x5, x3        // residuo = digito actual
        add x7, x7, #48
        sub x2, x2, #1
        strb w7, [x2]
        mov x3, x6
        b int_convert
int_sign:
        cbz x4, int_done
        sub x2, x2, #1
        mov w5, #45                // agrego '-'
        strb w5, [x2]
int_done:
        ldr x1, =common_number_buffer
        add x1, x1, #63
        sub x1, x1, x2
        mov x0, x2
        ret

// abs_int
// Devuelve el valor absoluto de un entero
// Entrada: x0 = numero
// Salida:  x0 = numero positivo
abs_int:
        cmp x0, #0
        bge abs_done
        neg x0, x0
abs_done:
        ret

// select_requested_column
// Recibe el nombre que pidio el usuario y busca el header real del CSV
// Entrada: x0 = columna logica
// Salida:  x0 = 1/0, x1 = header real, x2 = longitud header
select_requested_column:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        str x0, [sp, #-16]!        // guardo nombre original para compararlo varias veces
        ldr x1, =col_temp
        bl match_cstr              // reviso si pidieron TEMP
        cbnz x0, select_temp
        ldr x0, [sp]
        ldr x1, =col_hum_aire
        bl match_cstr              // reviso HUM_AIRE
        cbnz x0, select_hum
        ldr x0, [sp]
        ldr x1, =col_soil1
        bl match_cstr              // reviso SOIL1
        cbnz x0, select_soil1
        ldr x0, [sp]
        ldr x1, =col_soil2
        bl match_cstr              // reviso SOIL2
        cbnz x0, select_soil2
        ldr x0, [sp]
        ldr x1, =col_luz
        bl match_cstr              // reviso LUZ
        cbnz x0, select_luz
        ldr x0, [sp]
        ldr x1, =col_gas
        bl match_cstr              // reviso GAS
        cbnz x0, select_gas
        mov x0, #0
        mov x1, #0
        mov x2, #0
        b select_return
select_temp:
        mov x0, #1
        ldr x1, =header_temp
        mov x2, #HEADER_TEMP_LEN
        b select_return
select_hum:
        mov x0, #1
        ldr x1, =header_hum_aire
        mov x2, #HEADER_HUM_AIRE_LEN
        b select_return
select_soil1:
        mov x0, #1
        ldr x1, =header_soil1
        mov x2, #HEADER_SOIL1_LEN
        b select_return
select_soil2:
        mov x0, #1
        ldr x1, =header_soil2
        mov x2, #HEADER_SOIL2_LEN
        b select_return
select_luz:
        mov x0, #1
        ldr x1, =header_luz
        mov x2, #HEADER_LUZ_LEN
        b select_return
select_gas:
        mov x0, #1
        ldr x1, =header_gas
        mov x2, #HEADER_GAS_LEN
select_return:
        add sp, sp, #16
        ldp x29, x30, [sp], #16
        ret

// find_header_column
// Busca la columna esperada dentro de la primera linea del CSV
// Entrada: x0 = inicio CSV, x1 = fin CSV, x2 = header, x3 = header_len
// Salida:  x0 = 1/0, x1 = primera fila de datos, x2 = indice columna
find_header_column:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!
        stp x23, x24, [sp, #-16]!
        stp x25, x26, [sp, #-16]!
        mov x21, x0                // cursor dentro del buffer
        mov x25, x1                // fin del buffer
        mov x19, x2                // header que necesito encontrar
        mov x20, x3                // longitud del header buscado
        mov x22, x21               // inicio del campo actual
        mov x23, #1                // columnas empiezan en 1
        mov x24, #0                // aqui guardo columna encontrada
header_scan:
        cmp x21, x25
        bge header_not_found
        ldrb w9, [x21]
        cmp w9, #44                // coma separa columnas
        beq header_comma
        cmp w9, #10                // salto de linea termina header
        beq header_end
        cmp w9, #13
        beq header_end
        add x21, x21, #1
        b header_scan
header_comma:
        mov x0, x22
        sub x1, x21, x22
        mov x2, x19
        mov x3, x20
        bl bytes_equal             // comparo campo actual con header esperado
        cbz x0, header_next
        mov x24, x23
header_next:
        add x23, x23, #1           // paso a la siguiente columna
        add x21, x21, #1
        mov x22, x21
        b header_scan
header_end:
        mov x0, x22
        sub x1, x21, x22
        mov x2, x19
        mov x3, x20
        bl bytes_equal             // comparo ultimo campo del header
        cbz x0, header_validate
        mov x24, x23
header_validate:
        cbz x24, header_not_found  // si nunca coincidio, la columna no existe
        cmp x21, x25
        bge header_success
        ldrb w9, [x21]
        cmp w9, #13
        bne header_lf
        add x21, x21, #1
header_lf:
        cmp x21, x25
        bge header_success
        ldrb w9, [x21]
        cmp w9, #10
        bne header_success
        add x21, x21, #1
header_success:
        mov x0, #1
        mov x1, x21                // x1 queda apuntando a primera fila de datos
        mov x2, x24                // x2 devuelve indice de columna
        b header_return
header_not_found:
        mov x0, #0
        mov x1, #0
        mov x2, #0
header_return:
        ldp x25, x26, [sp], #16
        ldp x23, x24, [sp], #16
        ldp x21, x22, [sp], #16
        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret
