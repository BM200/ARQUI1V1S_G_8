
        .equ BUFFER_SIZE, 1048576
        .equ BUFFER_READ_MAX, 1048575

        .data
msg_module:            .ascii "MODULE=HISTORICAL_ANALYZER\n"
        .equ MSG_MODULE_LEN, . - msg_module
msg_status_ok:         .ascii "STATUS=OK\n"
        .equ MSG_STATUS_OK_LEN, . - msg_status_ok
msg_status_error:      .ascii "STATUS=ERROR\n"
        .equ MSG_STATUS_ERROR_LEN, . - msg_status_error
msg_column:            .ascii "COLUMN="
        .equ MSG_COLUMN_LEN, . - msg_column
msg_window_start:      .ascii "WINDOW_START="
        .equ MSG_WINDOW_START_LEN, . - msg_window_start
msg_window_end:        .ascii "WINDOW_END="
        .equ MSG_WINDOW_END_LEN, . - msg_window_end
msg_count:             .ascii "COUNT="
        .equ MSG_COUNT_LEN, . - msg_count
msg_min:               .ascii "MIN="
        .equ MSG_MIN_LEN, . - msg_min
msg_max:               .ascii "MAX="
        .equ MSG_MAX_LEN, . - msg_max
msg_sum:               .ascii "SUM="
        .equ MSG_SUM_LEN, . - msg_sum
msg_error_prefix:      .ascii "ERROR="
        .equ MSG_ERROR_PREFIX_LEN, . - msg_error_prefix
msg_detail_prefix:     .ascii "DETAIL="
        .equ MSG_DETAIL_PREFIX_LEN, . - msg_detail_prefix
msg_newline:           .ascii "\n"

err_invalid_arguments: .ascii "INVALID_ARGUMENTS"
        .equ ERR_INVALID_ARGUMENTS_LEN, . - err_invalid_arguments
detail_expected_args:  .ascii "EXPECTED_FILE_START_END_COLUMN"
        .equ DETAIL_EXPECTED_ARGS_LEN, . - detail_expected_args
err_invalid_range:     .ascii "INVALID_RANGE"
        .equ ERR_INVALID_RANGE_LEN, . - err_invalid_range
detail_start_positive: .ascii "START_LINE_MUST_BE_AT_LEAST_1"
        .equ DETAIL_START_POSITIVE_LEN, . - detail_start_positive
detail_end_before:     .ascii "END_LINE_BEFORE_START_LINE"
        .equ DETAIL_END_BEFORE_LEN, . - detail_end_before
detail_start_exceeds:  .ascii "START_LINE_EXCEEDS_FILE_LENGTH"
        .equ DETAIL_START_EXCEEDS_LEN, . - detail_start_exceeds
detail_end_exceeds:    .ascii "END_LINE_EXCEEDS_FILE_LENGTH"
        .equ DETAIL_END_EXCEEDS_LEN, . - detail_end_exceeds
err_invalid_column:    .ascii "INVALID_COLUMN"
        .equ ERR_INVALID_COLUMN_LEN, . - err_invalid_column
detail_unknown_column: .ascii "UNKNOWN_SENSOR_COLUMN"
        .equ DETAIL_UNKNOWN_COLUMN_LEN, . - detail_unknown_column
detail_column_header:  .ascii "COLUMN_NOT_PRESENT_IN_HEADER"
        .equ DETAIL_COLUMN_HEADER_LEN, . - detail_column_header
err_file_not_found:    .ascii "FILE_NOT_FOUND"
        .equ ERR_FILE_NOT_FOUND_LEN, . - err_file_not_found
detail_file_not_found: .ascii "INPUT_FILE_COULD_NOT_BE_OPENED"
        .equ DETAIL_FILE_NOT_FOUND_LEN, . - detail_file_not_found
err_file_read:         .ascii "FILE_READ_ERROR"
        .equ ERR_FILE_READ_LEN, . - err_file_read
detail_file_read:      .ascii "INPUT_FILE_COULD_NOT_BE_READ"
        .equ DETAIL_FILE_READ_LEN, . - detail_file_read
err_file_too_large:    .ascii "FILE_TOO_LARGE"
        .equ ERR_FILE_TOO_LARGE_LEN, . - err_file_too_large
detail_buffer_limit:   .ascii "INPUT_EXCEEDS_1048575_BYTES"
        .equ DETAIL_BUFFER_LIMIT_LEN, . - detail_buffer_limit
err_file_format:       .ascii "INVALID_FILE_FORMAT"
        .equ ERR_FILE_FORMAT_LEN, . - err_file_format
detail_missing_header: .ascii "CSV_HEADER_NOT_FOUND"
        .equ DETAIL_MISSING_HEADER_LEN, . - detail_missing_header
err_invalid_value:     .ascii "INVALID_VALUE"
        .equ ERR_INVALID_VALUE_LEN, . - err_invalid_value
detail_non_numeric:    .ascii "NON_NUMERIC_VALUE"
        .equ DETAIL_NON_NUMERIC_LEN, . - detail_non_numeric
err_insufficient:      .ascii "INSUFFICIENT_DATA"
        .equ ERR_INSUFFICIENT_LEN, . - err_insufficient
detail_empty_range:    .ascii "EMPTY_RANGE"
        .equ DETAIL_EMPTY_RANGE_LEN, . - detail_empty_range

col_temp:              .asciz "TEMP"
header_temp:           .asciz "TEMP"
        .equ HEADER_TEMP_LEN, 4
col_hum_aire:          .asciz "HUM_AIRE"
header_hum_aire:       .asciz "HUM_AIRE"
        .equ HEADER_HUM_AIRE_LEN, 8
col_soil1:             .asciz "SOIL1"
header_soil1:          .asciz "HUM_SUELO_1"
        .equ HEADER_SOIL1_LEN, 11
col_soil2:             .asciz "SOIL2"
header_soil2:          .asciz "HUM_SUELO_2"
        .equ HEADER_SOIL2_LEN, 11
col_luz:               .asciz "LUZ"
header_luz:            .asciz "LUZ"
        .equ HEADER_LUZ_LEN, 3
col_gas:               .asciz "GAS"
header_gas:            .asciz "GAS"
        .equ HEADER_GAS_LEN, 3

        .bss
        .balign 8
file_buffer:           .skip BUFFER_SIZE
number_buffer:         .skip 64
start_value:           .skip 8
end_value:             .skip 8
selected_column:       .skip 8
requested_column_ptr:  .skip 8
requested_column_len:  .skip 8
expected_header_ptr:   .skip 8
expected_header_len:   .skip 8
count_value:           .skip 8
sum_value:             .skip 8
min_value:             .skip 8
max_value:             .skip 8

        .text
        .global _start

// Inicio del programa. Valida argumentos y prepara el analisis.
_start:
        ldr x0, [sp]               // argc
        cmp x0, #5
        bne error_invalid_arguments // deben venir 4 argumentos

        ldr x0, [sp, #24]          // argv[2] = linea inicial
        bl parse_uint              // convierto texto a numero
        cbz x1, error_start_invalid // si no es numero, error
        cmp x0, #1
        blt error_start_invalid    // la primera fila valida es 1
        ldr x2, =start_value
        str x0, [x2]

        ldr x0, [sp, #32]          // argv[3] = linea final
        bl parse_uint              // convierto texto a numero
        cbz x1, error_end_before_start
        ldr x2, =end_value
        str x0, [x2]
        ldr x3, =start_value
        ldr x3, [x3]
        cmp x0, x3
        blt error_end_before_start // fin no puede ser menor que inicio

        ldr x0, [sp, #40]          // argv[4] = columna pedida
        ldr x1, =requested_column_ptr
        str x0, [x1]
        bl cstrlen                 // guardo longitud para imprimir la columna
        ldr x1, =requested_column_len
        str x0, [x1]
        bl select_requested_column // valido columna logica
        cbz x0, error_invalid_column // si no existe, error

        mov x0, #-100
        ldr x1, [sp, #16]          // argv[1] = ruta CSV
        mov x2, #0
        mov x3, #0
        mov x8, #56                // syscall openat
        svc #0
        cmp x0, #0
        blt error_file_not_found
        mov x18, x0                // descriptor del archivo

        mov x0, x18
        ldr x1, =file_buffer
        ldr x2, =BUFFER_READ_MAX
        mov x8, #63                // syscall read
        svc #0
        mov x17, x0                // bytes leidos

        mov x0, x18
        mov x8, #57                // syscall close
        svc #0

        cmp x17, #0
        blt error_file_read
        beq error_missing_header
        ldr x9, =BUFFER_READ_MAX
        cmp x17, x9
        bge error_file_too_large

        ldr x19, =file_buffer      // cursor dentro del CSV
        add x20, x19, x17          // fin del buffer
        bl find_header_column      // busco columna en el encabezado
        cbz x0, error_column_not_in_header
        mov x19, x1                // primera fila de datos

        ldr x0, =count_value
        str xzr, [x0]
        ldr x0, =sum_value
        str xzr, [x0]
        mov x21, #1                // fila actual de datos

// Recorre las filas del CSV.
row_loop:
        cmp x19, x20
        bge end_of_file
        ldr x0, =end_value
        ldr x0, [x0]
        cmp x21, x0
        bgt finish_success         // ya pase el rango pedido
        ldr x0, =start_value
        ldr x0, [x0]
        cmp x21, x0
        blt skip_current_row       // aun no llego a la fila inicial

        ldr x0, =selected_column
        ldr x22, [x0]              // columna que se quiere leer
        mov x23, #1                // columna actual
        mov x24, x19               // inicio del campo actual
        mov x25, x19               // cursor dentro de la fila

// Busca el campo de la columna seleccionada.
find_field_loop:
        cmp x25, x20
        bge field_delimiter_found
        ldrb w9, [x25]
        cmp w9, #44                // coma termina campo
        beq field_delimiter_found
        cmp w9, #10                // salto de linea termina fila
        beq field_delimiter_found
        cmp w9, #13
        beq field_delimiter_found
        add x25, x25, #1
        b find_field_loop

field_delimiter_found:
        cmp x23, x22
        beq parse_selected_field   // ya estoy en la columna pedida
        cmp x25, x20
        bge error_non_numeric
        ldrb w9, [x25]
        cmp w9, #44
        bne error_non_numeric
        add x23, x23, #1           // sigo con la siguiente columna
        add x25, x25, #1
        mov x24, x25
        b find_field_loop

// Convierte el campo elegido a numero.
parse_selected_field:
        mov x0, x24
        mov x1, x25
        bl parse_int_span          // convierte texto del CSV a entero
        cbz x1, error_non_numeric  // si falla, el campo no es numerico
        mov x26, x0                // valor leido de la columna

        ldr x9, =count_value
        ldr x10, [x9]
        cbnz x10, update_existing_stats
        ldr x11, =min_value
        str x26, [x11]             // primer dato tambien es MIN
        ldr x11, =max_value
        str x26, [x11]             // primer dato tambien es MAX
        b update_sum_and_count

// Actualiza MIN y MAX si ya habia datos.
update_existing_stats:
        ldr x11, =min_value
        ldr x12, [x11]
        cmp x26, x12
        bge check_maximum
        str x26, [x11]             // nuevo minimo
check_maximum:
        ldr x11, =max_value
        ldr x12, [x11]
        cmp x26, x12
        ble update_sum_and_count
        str x26, [x11]             // nuevo maximo

// Acumula SUM y COUNT.
update_sum_and_count:
        ldr x11, =sum_value
        ldr x12, [x11]
        add x12, x12, x26          // SUM += valor
        str x12, [x11]
        add x10, x10, #1           // COUNT++
        str x10, [x9]
        mov x19, x25
        b skip_to_next_row

skip_current_row:
        b skip_to_next_row

// Avanza hasta la siguiente fila.
skip_to_next_row:
        cmp x19, x20
        bge row_finished
        ldrb w9, [x19], #1
        cmp w9, #10
        bne skip_to_next_row
row_finished:
        ldr x0, =end_value
        ldr x0, [x0]
        cmp x21, x0
        beq finish_success
        add x21, x21, #1           // siguiente fila
        b row_loop

// Revisa si el rango pedido existe cuando se acaba el archivo.
end_of_file:
        sub x9, x21, #1            // ultima fila alcanzada
        ldr x10, =start_value
        ldr x10, [x10]
        cmp x10, x9
        bgt error_start_exceeds_file
        ldr x10, =end_value
        ldr x10, [x10]
        cmp x10, x9
        bgt error_end_exceeds_file
        ldr x10, =count_value
        ldr x10, [x10]
        cbnz x10, finish_success
        b error_insufficient_data

// Imprime salida estructurada con los resultados.
finish_success:
        ldr x0, =count_value
        ldr x0, [x0]
        cbz x0, error_insufficient_data
        ldr x0, =msg_module
        mov x1, #MSG_MODULE_LEN
        bl write_stdout            // MODULE
        ldr x0, =msg_status_ok
        mov x1, #MSG_STATUS_OK_LEN
        bl write_stdout            // STATUS=OK
        ldr x0, =msg_column
        mov x1, #MSG_COLUMN_LEN
        bl write_stdout
        ldr x0, =requested_column_ptr
        ldr x0, [x0]
        ldr x1, =requested_column_len
        ldr x1, [x1]
        bl write_stdout            // columna como la escribio el usuario
        ldr x0, =msg_newline
        mov x1, #1
        bl write_stdout
        ldr x0, =msg_window_start
        mov x1, #MSG_WINDOW_START_LEN
        ldr x2, =start_value
        ldr x2, [x2]
        bl write_number_field
        ldr x0, =msg_window_end
        mov x1, #MSG_WINDOW_END_LEN
        ldr x2, =end_value
        ldr x2, [x2]
        bl write_number_field
        ldr x0, =msg_count
        mov x1, #MSG_COUNT_LEN
        ldr x2, =count_value
        ldr x2, [x2]
        bl write_number_field
        ldr x0, =msg_min
        mov x1, #MSG_MIN_LEN
        ldr x2, =min_value
        ldr x2, [x2]
        bl write_number_field
        ldr x0, =msg_max
        mov x1, #MSG_MAX_LEN
        ldr x2, =max_value
        ldr x2, [x2]
        bl write_number_field
        ldr x0, =msg_sum
        mov x1, #MSG_SUM_LEN
        ldr x2, =sum_value
        ldr x2, [x2]
        bl write_number_field
        mov x0, #0
        mov x8, #93
        svc #0

// Traduce la columna pedida al nombre real del header.
select_requested_column:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        ldr x0, =requested_column_ptr
        ldr x0, [x0]
        ldr x1, =col_temp
        bl match_cstr              // reviso TEMP
        cbnz x0, select_temp
        ldr x0, =requested_column_ptr
        ldr x0, [x0]
        ldr x1, =col_hum_aire
        bl match_cstr              // reviso HUM_AIRE
        cbnz x0, select_hum
        ldr x0, =requested_column_ptr
        ldr x0, [x0]
        ldr x1, =col_soil1
        bl match_cstr              // reviso SOIL1
        cbnz x0, select_soil1
        ldr x0, =requested_column_ptr
        ldr x0, [x0]
        ldr x1, =col_soil2
        bl match_cstr              // reviso SOIL2
        cbnz x0, select_soil2
        ldr x0, =requested_column_ptr
        ldr x0, [x0]
        ldr x1, =col_luz
        bl match_cstr              // reviso LUZ
        cbnz x0, select_luz
        ldr x0, =requested_column_ptr
        ldr x0, [x0]
        ldr x1, =col_gas
        bl match_cstr              // reviso GAS
        cbnz x0, select_gas
        mov x0, #0
        b select_return
select_temp:
        ldr x2, =header_temp
        mov x3, #HEADER_TEMP_LEN
        b store_header
select_hum:
        ldr x2, =header_hum_aire
        mov x3, #HEADER_HUM_AIRE_LEN
        b store_header
select_soil1:
        ldr x2, =header_soil1
        mov x3, #HEADER_SOIL1_LEN
        b store_header
select_soil2:
        ldr x2, =header_soil2
        mov x3, #HEADER_SOIL2_LEN
        b store_header
select_luz:
        ldr x2, =header_luz
        mov x3, #HEADER_LUZ_LEN
        b store_header
select_gas:
        ldr x2, =header_gas
        mov x3, #HEADER_GAS_LEN
store_header:
        ldr x4, =expected_header_ptr
        str x2, [x4]               // guardo header real
        ldr x4, =expected_header_len
        str x3, [x4]               // guardo longitud del header
        mov x0, #1
select_return:
        ldp x29, x30, [sp], #16
        ret

// Busca la columna dentro del encabezado del CSV.
find_header_column:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!
        stp x23, x24, [sp, #-16]!
        mov x21, x19               // cursor del header
        mov x22, x19               // inicio del campo actual
        mov x23, #1                // numero de columna
        mov x24, #0                // columna encontrada
header_scan:
        cmp x21, x20
        bge header_not_found
        ldrb w9, [x21]
        cmp w9, #44                // coma separa columnas
        beq header_comma
        cmp w9, #10                // salto termina header
        beq header_end
        cmp w9, #13
        beq header_end
        add x21, x21, #1
        b header_scan
header_comma:
        mov x0, x22
        sub x1, x21, x22
        ldr x2, =expected_header_ptr
        ldr x2, [x2]
        ldr x3, =expected_header_len
        ldr x3, [x3]
        bl bytes_equal             // comparo texto del header
        cbz x0, header_next
        mov x24, x23
header_next:
        add x23, x23, #1           // siguiente columna
        add x21, x21, #1
        mov x22, x21
        b header_scan
header_end:
        mov x0, x22
        sub x1, x21, x22
        ldr x2, =expected_header_ptr
        ldr x2, [x2]
        ldr x3, =expected_header_len
        ldr x3, [x3]
        bl bytes_equal             // comparo ultimo campo
        cbz x0, header_validate
        mov x24, x23
header_validate:
        cbz x24, header_not_found  // no se encontro la columna
        cmp x21, x20
        bge header_success
        ldrb w9, [x21]
        cmp w9, #13
        bne header_lf
        add x21, x21, #1
header_lf:
        cmp x21, x20
        bge header_success
        ldrb w9, [x21]
        cmp w9, #10
        bne header_success
        add x21, x21, #1
header_success:
        ldr x0, =selected_column
        str x24, [x0]              // guardo columna seleccionada
        mov x1, x21                // inicio de la primera fila de datos
        mov x0, #1
        b header_return
header_not_found:
        mov x0, #0
        mov x1, #0
header_return:
        ldp x23, x24, [sp], #16
        ldp x21, x22, [sp], #16
        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret

// Convierte argv numerico positivo a entero.
// Salida: x0 = numero, x1 = 1 valido o 0 invalido.
parse_uint:
        mov x2, #0                 // acumulador
        mov x3, #0                 // cantidad de digitos
parse_uint_loop:
        ldrb w4, [x0], #1          // leo caracter y avanzo
        cbz w4, parse_uint_done
        cmp w4, #48
        blt parse_uint_invalid
        cmp w4, #57
        bgt parse_uint_invalid
        mov x5, #10
        mul x2, x2, x5             // valor = valor * 10
        sub w4, w4, #48            // ASCII a digito
        add x2, x2, x4
        add x3, x3, #1
        b parse_uint_loop
parse_uint_done:
        cbz x3, parse_uint_invalid // no acepta texto vacio
        mov x0, x2
        mov x1, #1
        ret
parse_uint_invalid:
        mov x0, #0
        mov x1, #0
        ret

// Convierte un campo del CSV a entero con signo.
// Entrada: x0 = inicio, x1 = fin del campo.
// Salida: x0 = numero, x1 = 1 valido o 0 invalido.
parse_int_span:
        cmp x0, x1
        bge parse_int_invalid
        mov x2, #0                 // acumulador
        mov x3, #0                 // digitos leidos
        mov x4, #0                 // bandera de negativo
        ldrb w5, [x0]
        cmp w5, #45                // signo '-'
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
        mul x2, x2, x6             // valor = valor * 10
        sub w5, w5, #48            // ASCII a digito
        add x2, x2, x5
        add x3, x3, #1
        b parse_int_loop
parse_int_done:
        cbz x3, parse_int_invalid
        cbz x4, parse_int_positive
        neg x2, x2                 // aplico signo negativo
parse_int_positive:
        mov x0, x2
        mov x1, #1
        ret
parse_int_invalid:
        mov x0, #0
        mov x1, #0
        ret

// Compara dos strings terminados en cero.
match_cstr:
        ldrb w2, [x0], #1
        ldrb w3, [x1], #1
        cmp w2, w3                 // comparo caracter actual
        bne match_false
        cbnz w2, match_cstr
        mov x0, #1
        ret
match_false:
        mov x0, #0
        ret

// Compara dos textos con longitud conocida.
bytes_equal:
        cmp x1, x3                 // si cambia la longitud, no son iguales
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

// Calcula longitud de string terminado en cero.
cstrlen:
        mov x1, x0
cstrlen_loop:
        ldrb w2, [x1], #1          // avanzo hasta encontrar cero
        cbnz w2, cstrlen_loop
        sub x0, x1, x0
        sub x0, x0, #1
        ret

// Escribe texto en stdout.
// Entrada: x0 = texto, x1 = longitud.
write_stdout:
        mov x2, x1                 // cantidad de bytes
        mov x1, x0                 // direccion del texto
        mov x0, #1                 // fd 1 = stdout
        mov x8, #64                // syscall write
        svc #0
        ret

// Imprime etiqueta, numero y salto de linea.
write_number_field:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        mov x13, x2                // guardo numero mientras imprimo etiqueta
        bl write_stdout            // imprime ETIQUETA=
        mov x0, x13
        bl int_to_ascii            // numero a texto
        bl write_stdout            // imprime numero
        ldr x0, =msg_newline
        mov x1, #1
        bl write_stdout
        ldp x29, x30, [sp], #16
        ret

// Convierte entero con signo a texto ASCII.
int_to_ascii:
        ldr x2, =number_buffer
        add x2, x2, #63            // escribo desde el final del buffer
        mov x3, #0
        strb w3, [x2]
        mov x3, x0
        mov x4, #0
        cmp x3, #0
        bge int_abs_ready
        mov x4, #1                 // marco signo negativo
        neg x3, x3                 // convierto usando valor positivo
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
        msub x7, x6, x5, x3        // residuo del digito
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
        ldr x1, =number_buffer
        add x1, x1, #63
        sub x1, x1, x2
        mov x0, x2
        ret

// Imprime errores estructurados.
emit_error:
        mov x13, x0                // puntero ERROR
        mov x14, x1                // longitud ERROR
        mov x15, x2                // puntero DETAIL
        mov x16, x3                // longitud DETAIL
        ldr x0, =msg_module
        mov x1, #MSG_MODULE_LEN
        bl write_stdout
        ldr x0, =msg_status_error
        mov x1, #MSG_STATUS_ERROR_LEN
        bl write_stdout
        ldr x0, =msg_error_prefix
        mov x1, #MSG_ERROR_PREFIX_LEN
        bl write_stdout
        mov x0, x13
        mov x1, x14
        bl write_stdout
        ldr x0, =msg_newline
        mov x1, #1
        bl write_stdout
        ldr x0, =msg_detail_prefix
        mov x1, #MSG_DETAIL_PREFIX_LEN
        bl write_stdout
        mov x0, x15
        mov x1, x16
        bl write_stdout
        ldr x0, =msg_newline
        mov x1, #1
        bl write_stdout
        mov x0, #1
        mov x8, #93
        svc #0

// Cada etiqueta prepara ERROR y DETAIL antes de llamar a emit_error.
error_invalid_arguments:
        ldr x0, =err_invalid_arguments
        mov x1, #ERR_INVALID_ARGUMENTS_LEN
        ldr x2, =detail_expected_args
        mov x3, #DETAIL_EXPECTED_ARGS_LEN
        b emit_error
error_start_invalid:
        ldr x0, =err_invalid_range
        mov x1, #ERR_INVALID_RANGE_LEN
        ldr x2, =detail_start_positive
        mov x3, #DETAIL_START_POSITIVE_LEN
        b emit_error
error_end_before_start:
        ldr x0, =err_invalid_range
        mov x1, #ERR_INVALID_RANGE_LEN
        ldr x2, =detail_end_before
        mov x3, #DETAIL_END_BEFORE_LEN
        b emit_error
error_start_exceeds_file:
        ldr x0, =err_invalid_range
        mov x1, #ERR_INVALID_RANGE_LEN
        ldr x2, =detail_start_exceeds
        mov x3, #DETAIL_START_EXCEEDS_LEN
        b emit_error
error_end_exceeds_file:
        ldr x0, =err_invalid_range
        mov x1, #ERR_INVALID_RANGE_LEN
        ldr x2, =detail_end_exceeds
        mov x3, #DETAIL_END_EXCEEDS_LEN
        b emit_error
error_invalid_column:
        ldr x0, =err_invalid_column
        mov x1, #ERR_INVALID_COLUMN_LEN
        ldr x2, =detail_unknown_column
        mov x3, #DETAIL_UNKNOWN_COLUMN_LEN
        b emit_error
error_column_not_in_header:
        ldr x0, =err_invalid_column
        mov x1, #ERR_INVALID_COLUMN_LEN
        ldr x2, =detail_column_header
        mov x3, #DETAIL_COLUMN_HEADER_LEN
        b emit_error
error_file_not_found:
        ldr x0, =err_file_not_found
        mov x1, #ERR_FILE_NOT_FOUND_LEN
        ldr x2, =detail_file_not_found
        mov x3, #DETAIL_FILE_NOT_FOUND_LEN
        b emit_error
error_file_read:
        ldr x0, =err_file_read
        mov x1, #ERR_FILE_READ_LEN
        ldr x2, =detail_file_read
        mov x3, #DETAIL_FILE_READ_LEN
        b emit_error
error_file_too_large:
        ldr x0, =err_file_too_large
        mov x1, #ERR_FILE_TOO_LARGE_LEN
        ldr x2, =detail_buffer_limit
        mov x3, #DETAIL_BUFFER_LIMIT_LEN
        b emit_error
error_missing_header:
        ldr x0, =err_file_format
        mov x1, #ERR_FILE_FORMAT_LEN
        ldr x2, =detail_missing_header
        mov x3, #DETAIL_MISSING_HEADER_LEN
        b emit_error
error_non_numeric:
        ldr x0, =err_invalid_value
        mov x1, #ERR_INVALID_VALUE_LEN
        ldr x2, =detail_non_numeric
        mov x3, #DETAIL_NON_NUMERIC_LEN
        b emit_error
error_insufficient_data:
        ldr x0, =err_insufficient
        mov x1, #ERR_INSUFFICIENT_LEN
        ldr x2, =detail_empty_range
        mov x3, #DETAIL_EMPTY_RANGE_LEN
        b emit_error
