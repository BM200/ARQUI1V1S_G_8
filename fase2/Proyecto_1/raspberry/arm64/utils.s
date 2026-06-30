        .equ BUFFER_SIZE, 1048576
        .equ BUFFER_READ_MAX, 1048575

        .equ UTILS_OK, 0
        .equ UTILS_INVALID_ARGUMENTS, -1
        .equ UTILS_INVALID_RANGE, -2
        .equ UTILS_INVALID_COLUMN, -3
        .equ UTILS_FILE_NOT_FOUND, -4
        .equ UTILS_FILE_READ_ERROR, -5
        .equ UTILS_FILE_TOO_LARGE, -6
        .equ UTILS_MISSING_HEADER, -7
        .equ UTILS_COLUMN_NOT_PRESENT, -8
        .equ UTILS_NON_NUMERIC_VALUE, -9
        .equ UTILS_INSUFFICIENT_DATA, -10
        .equ UTILS_OUTPUT_LIMIT_REACHED, -11

        .data
col_temp:
        .asciz "TEMP"
header_temp:
        .asciz "TEMP"
        .equ HEADER_TEMP_LEN, 4
col_hum_aire:
        .asciz "HUM_AIRE"
header_hum_aire:
        .asciz "HUM_AIRE"
        .equ HEADER_HUM_AIRE_LEN, 8
col_soil1:
        .asciz "SOIL1"
header_soil1:
        .asciz "SOIL1"
        .equ HEADER_SOIL1_LEN, 5
col_soil2:
        .asciz "SOIL2"
header_soil2:
        .asciz "SOIL2"
        .equ HEADER_SOIL2_LEN, 5
col_luz:
        .asciz "LUZ"
header_luz:
        .asciz "LUZ"
        .equ HEADER_LUZ_LEN, 3
col_gas:
        .asciz "GAS"
header_gas:
        .asciz "GAS"
        .equ HEADER_GAS_LEN, 3

msg_status_error:
        .ascii "STATUS=ERROR\n"
        .equ MSG_STATUS_ERROR_LEN, . - msg_status_error
msg_error_prefix:
        .ascii "ERROR="
        .equ MSG_ERROR_PREFIX_LEN, . - msg_error_prefix
msg_detail_prefix:
        .ascii "DETAIL="
        .equ MSG_DETAIL_PREFIX_LEN, . - msg_detail_prefix
msg_newline:
        .ascii "\n"

        .bss
        .balign 8
csv_buffer:
        .skip BUFFER_SIZE
number_buffer:
        .skip 64
csv_window_dest:
        .skip 8
csv_window_max:
        .skip 8

        .text

        .global read_csv_column
        .type read_csv_column, %function
read_csv_column:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!
        stp x23, x24, [sp, #-16]!
        stp x25, x26, [sp, #-16]!
        stp x27, x28, [sp, #-16]!

        mov x19, x0                  // esto guarda la ruta del archivo
        mov x20, x1                  // esto guarda la columna numerica
        mov x21, x2                  // esto guarda el arreglo destino
        mov x22, x3                  // esto guarda el maximo de valores

        mov x0, x19
        ldr x1, =csv_buffer
        ldr x2, =BUFFER_READ_MAX
        bl read_file_to_buffer
        cmp x0, #0
        bne read_csv_file_error
        mov x24, x1                  // esto guarda los bytes leidos

        ldr x25, =csv_buffer
        add x26, x25, x24

skip_header_utils:
        cmp x25, x26
        bge read_csv_done_empty
        ldrb w9, [x25], #1
        cmp w9, #10
        beq start_csv_lines
        b skip_header_utils

start_csv_lines:
        mov x27, #0                  // esto cuenta los valores leidos

csv_line_start:
        cmp x27, x22
        bge read_csv_done
        cmp x25, x26
        bge read_csv_done
        mov x28, #1                  // esto cuenta la columna actual

csv_skip_columns:
        cmp x28, x20
        beq csv_read_selected_column
        cmp x25, x26
        bge read_csv_done
        ldrb w9, [x25], #1
        cmp w9, #10
        beq csv_line_start
        cmp w9, #44
        bne csv_skip_columns
        add x28, x28, #1
        b csv_skip_columns

csv_read_selected_column:
        mov x9, #0                   // esto acumula el numero
        mov x10, #0                  // esto marca si hubo digitos

csv_parse_number:
        cmp x25, x26
        bge csv_store_number
        ldrb w11, [x25], #1
        cmp w11, #44
        beq csv_store_number
        cmp w11, #10
        beq csv_store_number_newline
        cmp w11, #13
        beq csv_parse_number
        cmp w11, #48
        blt csv_parse_number
        cmp w11, #57
        bgt csv_parse_number

        mov x12, #10
        mul x9, x9, x12
        sub w11, w11, #48
        add x9, x9, x11
        mov x10, #1
        b csv_parse_number

csv_store_number:
        cbz x10, csv_skip_rest_line
        str x9, [x21, x27, lsl #3]   // esto guarda el valor en el arreglo
        add x27, x27, #1

csv_skip_rest_line:
        cmp x25, x26
        bge read_csv_done
        ldrb w11, [x25], #1
        cmp w11, #10
        beq csv_line_start
        b csv_skip_rest_line

csv_store_number_newline:
        cbz x10, csv_line_start
        str x9, [x21, x27, lsl #3]   // esto guarda el valor en el arreglo
        add x27, x27, #1
        b csv_line_start

read_csv_done_empty:
        mov x0, #0
        b read_csv_return

read_csv_done:
        mov x0, x27
        b read_csv_return

read_csv_file_error:
        cmp x0, #UTILS_FILE_NOT_FOUND
        beq read_csv_open_error
        mov x0, #-2
        b read_csv_return

read_csv_open_error:
        mov x0, #-1

read_csv_return:
        ldp x27, x28, [sp], #16
        ldp x25, x26, [sp], #16
        ldp x23, x24, [sp], #16
        ldp x21, x22, [sp], #16
        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret

        .global write_file
        .type write_file, %function
write_file:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!
        str x23, [sp, #-16]!

        mov x19, x0                  // esto guarda la ruta destino
        mov x20, x1                  // esto guarda el buffer
        mov x21, x2                  // esto guarda la cantidad de bytes

        mov x0, #-100
        mov x1, x19
        mov x2, #577
        mov x3, #420
        mov x8, #56
        svc #0
        cmp x0, #0
        blt write_file_open_error
        mov x22, x0

        mov x0, x22
        mov x1, x20
        mov x2, x21
        mov x8, #64
        svc #0
        mov x23, x0

        mov x0, x22
        mov x8, #57
        svc #0

        mov x0, x23
        b write_file_return

write_file_open_error:
        mov x0, #-1

write_file_return:
        ldr x23, [sp], #16
        ldp x21, x22, [sp], #16
        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret

        .global uint_to_ascii
        .type uint_to_ascii, %function
uint_to_ascii:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!

        mov x19, x0                  // esto guarda el numero
        mov x20, x1                  // esto guarda el buffer temporal
        add x21, x20, #31
        mov w22, #0
        strb w22, [x21]

        cmp x19, #0
        bne uint_convert_loop
        sub x21, x21, #1
        mov w22, #48
        strb w22, [x21]
        mov x0, x21
        mov x1, #1
        b uint_return

uint_convert_loop:
        cmp x19, #0
        beq uint_done
        mov x22, #10
        udiv x23, x19, x22
        msub x24, x23, x22, x19
        add x24, x24, #48
        sub x21, x21, #1
        strb w24, [x21]
        mov x19, x23
        b uint_convert_loop

uint_done:
        add x22, x20, #31
        sub x1, x22, x21
        mov x0, x21

uint_return:
        ldp x21, x22, [sp], #16
        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret

        .global read_file_to_buffer
        .type read_file_to_buffer, %function
read_file_to_buffer:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!
        str x23, [sp, #-16]!

        mov x19, x0                  // esto guarda la ruta del archivo
        mov x20, x1                  // esto guarda el buffer destino
        mov x21, x2                  // esto guarda el maximo a leer

        cbz x19, read_file_invalid
        cbz x20, read_file_invalid
        cbz x21, read_file_invalid

        mov x0, #-100
        mov x1, x19
        mov x2, #0
        mov x3, #0
        mov x8, #56
        svc #0
        cmp x0, #0
        blt read_file_not_found
        mov x22, x0

        mov x0, x22
        mov x1, x20
        mov x2, x21
        mov x8, #63
        svc #0
        mov x23, x0

        mov x0, x22
        mov x8, #57
        svc #0

        cmp x23, #0
        blt read_file_error
        cmp x23, x21
        bge read_file_too_large

        add x9, x20, x23
        strb wzr, [x9]               // esto agrega fin de texto al buffer
        mov x0, #UTILS_OK
        mov x1, x23
        b read_file_return

read_file_invalid:
        mov x0, #UTILS_INVALID_ARGUMENTS
        mov x1, #0
        b read_file_return

read_file_not_found:
        mov x0, #UTILS_FILE_NOT_FOUND
        mov x1, #0
        b read_file_return

read_file_error:
        mov x0, #UTILS_FILE_READ_ERROR
        mov x1, #0
        b read_file_return

read_file_too_large:
        mov x0, #UTILS_FILE_TOO_LARGE
        mov x1, #0

read_file_return:
        ldr x23, [sp], #16
        ldp x21, x22, [sp], #16
        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret

        .global parse_uint
        .type parse_uint, %function
parse_uint:
        mov x2, #0                   // esto acumula el numero
        mov x3, #0                   // esto cuenta digitos
parse_uint_loop:
        ldrb w4, [x0], #1
        cbz w4, parse_uint_done
        cmp w4, #48
        blt parse_uint_invalid
        cmp w4, #57
        bgt parse_uint_invalid
        mov x5, #10
        mul x2, x2, x5
        sub w4, w4, #48
        add x2, x2, x4
        add x3, x3, #1
        b parse_uint_loop
parse_uint_done:
        cbz x3, parse_uint_invalid
        mov x0, x2
        mov x1, #1
        ret
parse_uint_invalid:
        mov x0, #0
        mov x1, #0
        ret

        .global parse_int_cstr
        .type parse_int_cstr, %function
parse_int_cstr:
        mov x2, #0                   // esto acumula el numero
        mov x3, #0                   // esto cuenta digitos
        mov x4, #0                   // esto marca signo negativo
        ldrb w5, [x0]
        cmp w5, #45
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
        mul x2, x2, x6
        sub w5, w5, #48
        add x2, x2, x5
        add x3, x3, #1
        b parse_int_cstr_loop
parse_int_cstr_done:
        cbz x3, parse_int_cstr_invalid
        cbz x4, parse_int_cstr_positive
        neg x2, x2
parse_int_cstr_positive:
        mov x0, x2
        mov x1, #1
        ret
parse_int_cstr_invalid:
        mov x0, #0
        mov x1, #0
        ret

        .global parse_int_span
        .type parse_int_span, %function
parse_int_span:
        cmp x0, x1
        bge parse_int_invalid
        mov x2, #0                   // esto acumula el numero
        mov x3, #0                   // esto cuenta digitos
        mov x4, #0                   // esto marca signo negativo
        ldrb w5, [x0]
        cmp w5, #45
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
        mul x2, x2, x6
        sub w5, w5, #48
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

        .global int_to_ascii
        .type int_to_ascii, %function
int_to_ascii:
        ldr x2, =number_buffer
        add x2, x2, #63
        strb wzr, [x2]
        mov x3, x0
        mov x4, #0
        cmp x3, #0
        bge int_abs_ready
        mov x4, #1
        neg x3, x3
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
        udiv x6, x3, x5
        msub x7, x6, x5, x3
        add x7, x7, #48
        sub x2, x2, #1
        strb w7, [x2]
        mov x3, x6
        b int_convert
int_sign:
        cbz x4, int_done
        sub x2, x2, #1
        mov w5, #45
        strb w5, [x2]
int_done:
        ldr x1, =number_buffer
        add x1, x1, #63
        sub x1, x1, x2
        mov x0, x2
        ret

        .global cstrlen
        .type cstrlen, %function
cstrlen:
        mov x1, x0
cstrlen_loop:
        ldrb w2, [x1], #1
        cbnz w2, cstrlen_loop
        sub x0, x1, x0
        sub x0, x0, #1
        ret

        .global match_cstr
        .type match_cstr, %function
match_cstr:
        ldrb w2, [x0], #1
        ldrb w3, [x1], #1
        cmp w2, w3
        bne match_false
        cbnz w2, match_cstr
        mov x0, #1
        ret
match_false:
        mov x0, #0
        ret

        .global bytes_equal
        .type bytes_equal, %function
bytes_equal:
        cmp x1, x3
        bne bytes_false
        mov x4, #0
bytes_loop:
        cmp x4, x1
        bge bytes_true
        ldrb w5, [x0, x4]
        ldrb w6, [x2, x4]
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

        .global write_stdout
        .type write_stdout, %function
write_stdout:
        mov x2, x1
        mov x1, x0
        mov x0, #1
        mov x8, #64
        svc #0
        ret

        .global write_number_field
        .type write_number_field, %function
write_number_field:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        mov x13, x2                  // esto guarda el numero
        bl write_stdout              // esto escribe la etiqueta
        mov x0, x13
        bl int_to_ascii              // esto convierte entero a texto
        bl write_stdout              // esto escribe el numero
        ldp x29, x30, [sp], #16
        ret

        .global abs_int
        .type abs_int, %function
abs_int:
        cmp x0, #0
        bge abs_done
        neg x0, x0
abs_done:
        ret

        .global select_requested_column
        .type select_requested_column, %function
select_requested_column:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        str x0, [sp, #-16]!          // esto guarda la columna pedida
        ldr x1, =col_temp
        bl match_cstr
        cbnz x0, select_temp
        ldr x0, [sp]
        ldr x1, =col_hum_aire
        bl match_cstr
        cbnz x0, select_hum
        ldr x0, [sp]
        ldr x1, =col_soil1
        bl match_cstr
        cbnz x0, select_soil1
        ldr x0, [sp]
        ldr x1, =col_soil2
        bl match_cstr
        cbnz x0, select_soil2
        ldr x0, [sp]
        ldr x1, =col_luz
        bl match_cstr
        cbnz x0, select_luz
        ldr x0, [sp]
        ldr x1, =col_gas
        bl match_cstr
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

        .global find_header_column
        .type find_header_column, %function
find_header_column:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!
        stp x23, x24, [sp, #-16]!
        stp x25, x26, [sp, #-16]!

        mov x21, x0                  // esto recorre el encabezado
        mov x25, x1                  // esto marca el fin del buffer
        mov x19, x2                  // esto guarda el header esperado
        mov x20, x3                  // esto guarda el largo del header
        mov x22, x21                 // esto marca el inicio del campo
        mov x23, #1                  // esto cuenta columnas desde uno
        mov x24, #0                  // esto guarda la columna encontrada

header_scan:
        cmp x21, x25
        bge header_end
        ldrb w9, [x21]
        cmp w9, #44
        beq header_comma
        cmp w9, #10
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
        bl bytes_equal               // esto compara el campo con el header
        cbz x0, header_next
        mov x24, x23
header_next:
        add x23, x23, #1
        add x21, x21, #1
        mov x22, x21
        b header_scan
header_end:
        cmp x21, x22
        beq header_not_found
        mov x0, x22
        sub x1, x21, x22
        mov x2, x19
        mov x3, x20
        bl bytes_equal               // esto compara el ultimo campo
        cbz x0, header_validate
        mov x24, x23
header_validate:
        cbz x24, header_not_found
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
        mov x1, x21                  // esto devuelve la primera fila de datos
        mov x2, x24                  // esto devuelve la columna real
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

        .global validate_range
        .type validate_range, %function
validate_range:
        cmp x0, #1
        blt validate_range_error
        cmp x1, x0
        blt validate_range_error
        mov x0, #1
        ret
validate_range_error:
        mov x0, #0
        ret

        .global read_csv_window_column
        .type read_csv_window_column, %function
read_csv_window_column:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!
        stp x23, x24, [sp, #-16]!
        stp x25, x26, [sp, #-16]!
        stp x27, x28, [sp, #-16]!

        mov x19, x0                  // esto guarda la ruta del archivo
        mov x20, x1                  // esto guarda la linea inicial
        mov x21, x2                  // esto guarda la linea final
        mov x22, x3                  // esto guarda la columna logica
        mov x23, x4                  // esto guarda el arreglo destino
        mov x24, x5                  // esto guarda el maximo de valores

        cbz x19, csv_window_invalid_arguments
        cbz x22, csv_window_invalid_arguments
        cbz x23, csv_window_invalid_arguments
        cbz x24, csv_window_invalid_arguments

        ldr x9, =csv_window_dest
        str x23, [x9]                // esto guarda el arreglo destino
        ldr x9, =csv_window_max
        str x24, [x9]                // esto guarda el maximo de valores

        mov x0, x20
        mov x1, x21
        bl validate_range            // esto valida el rango
        cbz x0, csv_window_invalid_range

        mov x0, x22
        bl select_requested_column   // esto valida la columna logica
        cbz x0, csv_window_invalid_column
        mov x25, x1                  // esto guarda el header real
        mov x26, x2                  // esto guarda el largo del header

        mov x0, x19
        ldr x1, =csv_buffer
        ldr x2, =BUFFER_READ_MAX
        bl read_file_to_buffer       // esto lee el archivo
        cmp x0, #UTILS_OK
        bne csv_window_file_status
        cbz x1, csv_window_missing_header

        ldr x27, =csv_buffer
        add x28, x27, x1

        mov x0, x27
        mov x1, x28
        mov x2, x25
        mov x3, x26
        bl find_header_column        // esto busca la columna en el encabezado
        cbz x0, csv_window_column_not_present

        mov x19, x1                  // esto apunta a la primera fila
        mov x24, x2                  // esto guarda la columna real
        mov x25, x20                 // esto guarda la linea inicial
        mov x26, x21                 // esto guarda la linea final
        mov x27, #1                  // esto cuenta la linea actual
        mov x20, #0                  // esto cuenta valores procesados

csv_window_row_loop:
        cmp x19, x28
        bge csv_window_end_of_file
        cmp x27, x26
        bgt csv_window_finish
        cmp x27, x25
        blt csv_window_skip_row

        mov x21, #1                  // esto cuenta la columna actual
        mov x22, x19                 // esto marca el inicio del campo
        mov x23, x19                 // esto recorre la fila

csv_window_find_field:
        cmp x23, x28
        bge csv_window_field_found
        ldrb w9, [x23]
        cmp w9, #44
        beq csv_window_field_found
        cmp w9, #10
        beq csv_window_field_found
        cmp w9, #13
        beq csv_window_field_found
        add x23, x23, #1
        b csv_window_find_field

csv_window_field_found:
        cmp x21, x24
        beq csv_window_parse_field
        cmp x23, x28
        bge csv_window_non_numeric
        ldrb w9, [x23]
        cmp w9, #44
        bne csv_window_non_numeric
        add x21, x21, #1
        add x23, x23, #1
        mov x22, x23
        b csv_window_find_field

csv_window_parse_field:
        mov x0, x22
        mov x1, x23
        bl parse_int_span            // esto convierte ascii a entero
        cbz x1, csv_window_non_numeric
        ldr x9, =csv_window_max
        ldr x9, [x9]
        cmp x20, x9
        bge csv_window_output_limit
        ldr x9, =csv_window_dest
        ldr x9, [x9]
        str x0, [x9, x20, lsl #3]    // esto guarda el valor en el arreglo
        add x20, x20, #1
        mov x19, x23
        b csv_window_skip_row

csv_window_skip_row:
        cmp x19, x28
        bge csv_window_row_finished
        ldrb w9, [x19], #1
        cmp w9, #10
        bne csv_window_skip_row
csv_window_row_finished:
        add x27, x27, #1
        b csv_window_row_loop

csv_window_end_of_file:
        sub x9, x27, #1
        cmp x26, x9
        bgt csv_window_invalid_range
        b csv_window_finish

csv_window_finish:
        cbz x20, csv_window_insufficient
        mov x0, #UTILS_OK
        mov x1, x20
        b csv_window_return

csv_window_invalid_arguments:
        mov x0, #UTILS_INVALID_ARGUMENTS
        mov x1, #0
        b csv_window_return

csv_window_invalid_range:
        mov x0, #UTILS_INVALID_RANGE
        mov x1, #0
        b csv_window_return

csv_window_invalid_column:
        mov x0, #UTILS_INVALID_COLUMN
        mov x1, #0
        b csv_window_return

csv_window_file_status:
        mov x1, #0
        b csv_window_return

csv_window_missing_header:
        mov x0, #UTILS_MISSING_HEADER
        mov x1, #0
        b csv_window_return

csv_window_column_not_present:
        mov x0, #UTILS_COLUMN_NOT_PRESENT
        mov x1, #0
        b csv_window_return

csv_window_non_numeric:
        mov x0, #UTILS_NON_NUMERIC_VALUE
        mov x1, #0
        b csv_window_return

csv_window_insufficient:
        mov x0, #UTILS_INSUFFICIENT_DATA
        mov x1, #0
        b csv_window_return

csv_window_output_limit:
        mov x0, #UTILS_OUTPUT_LIMIT_REACHED
        mov x1, x20

csv_window_return:
        ldp x27, x28, [sp], #16
        ldp x25, x26, [sp], #16
        ldp x23, x24, [sp], #16
        ldp x21, x22, [sp], #16
        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret

        .global emit_error
        .type emit_error, %function
emit_error:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!

        mov x19, x0                  // esto guarda el error
        mov x20, x1                  // esto guarda el largo del error
        mov x21, x2                  // esto guarda el detalle
        mov x22, x3                  // esto guarda el largo del detalle

        ldr x0, =msg_status_error
        mov x1, #MSG_STATUS_ERROR_LEN
        bl write_stdout
        ldr x0, =msg_error_prefix
        mov x1, #MSG_ERROR_PREFIX_LEN
        bl write_stdout
        mov x0, x19
        mov x1, x20
        bl write_stdout
        ldr x0, =msg_newline
        mov x1, #1
        bl write_stdout
        ldr x0, =msg_detail_prefix
        mov x1, #MSG_DETAIL_PREFIX_LEN
        bl write_stdout
        mov x0, x21
        mov x1, x22
        bl write_stdout
        ldr x0, =msg_newline
        mov x1, #1
        bl write_stdout

        ldp x21, x22, [sp], #16
        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret

        .global leer_archivo_buffer
        .type leer_archivo_buffer, %function
leer_archivo_buffer:
        // esto llama la funcion compatible existente
        b read_file_to_buffer

        .global escribir_archivo
        .type escribir_archivo, %function
escribir_archivo:
        // esto llama la funcion compatible existente
        b write_file

        .global convertir_entero_sin_signo_ascii
        .type convertir_entero_sin_signo_ascii, %function
convertir_entero_sin_signo_ascii:
        // esto llama la funcion compatible existente
        b uint_to_ascii

        .global convertir_entero_ascii_sin_signo
        .type convertir_entero_ascii_sin_signo, %function
convertir_entero_ascii_sin_signo:
        // esto llama la funcion compatible existente
        b uint_to_ascii

        .global convertir_texto_entero_sin_signo
        .type convertir_texto_entero_sin_signo, %function
convertir_texto_entero_sin_signo:
        // esto llama la funcion compatible existente
        b parse_uint

        .global convertir_cadena_entero
        .type convertir_cadena_entero, %function
convertir_cadena_entero:
        // esto llama la funcion compatible existente
        b parse_int_cstr

        .global convertir_ascii_entero
        .type convertir_ascii_entero, %function
convertir_ascii_entero:
        // esto llama la funcion compatible existente
        b parse_int_cstr

        .global convertir_span_entero
        .type convertir_span_entero, %function
convertir_span_entero:
        // esto llama la funcion compatible existente
        b parse_int_span

        .global convertir_entero_ascii
        .type convertir_entero_ascii, %function
convertir_entero_ascii:
        // esto llama la funcion compatible existente
        b int_to_ascii

        .global contar_cadena
        .type contar_cadena, %function
contar_cadena:
        // esto llama la funcion compatible existente
        b cstrlen

        .global comparar_cadenas
        .type comparar_cadenas, %function
comparar_cadenas:
        // esto llama la funcion compatible existente
        b match_cstr

        .global comparar_cadena
        .type comparar_cadena, %function
comparar_cadena:
        // esto llama la funcion compatible existente
        b match_cstr

        .global comparar_bytes
        .type comparar_bytes, %function
comparar_bytes:
        // esto llama la funcion compatible existente
        b bytes_equal

        .global escribir_salida
        .type escribir_salida, %function
escribir_salida:
        // esto llama la funcion compatible existente
        b write_stdout

        .global escribir_campo_numero
        .type escribir_campo_numero, %function
escribir_campo_numero:
        // esto llama la funcion compatible existente
        b write_number_field

        .global valor_absoluto
        .type valor_absoluto, %function
valor_absoluto:
        // esto llama la funcion compatible existente
        b abs_int

        .global seleccionar_columna
        .type seleccionar_columna, %function
seleccionar_columna:
        // esto llama la funcion compatible existente
        b select_requested_column

        .global buscar_columna
        .type buscar_columna, %function
buscar_columna:
        // esto llama la funcion compatible existente
        b find_header_column

        .global validar_rango
        .type validar_rango, %function
validar_rango:
        // esto llama la funcion compatible existente
        b validate_range

        .global leer_csv_rango_columna
        .type leer_csv_rango_columna, %function
leer_csv_rango_columna:
        // esto llama la funcion compatible existente
        b read_csv_window_column

        .global emitir_error
        .type emitir_error, %function
emitir_error:
        // esto llama la funcion compatible existente
        b emit_error

        .global emitir_error_es
        .type emitir_error_es, %function
emitir_error_es:
        // esto llama la funcion compatible existente
        b emit_error
