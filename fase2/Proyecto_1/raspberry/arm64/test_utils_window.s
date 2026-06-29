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
csv_file:
        .asciz "lecturas.csv"
bad_csv_file:
        .asciz "test_utils_bad.csv"
bad_csv_content:
        .ascii "ID,TEMP,HUM_AIRE,HUM_SUELO_1,HUM_SUELO_2,LUZ,GAS\n"
        .ascii "1,20,50,100,110,300,10\n"
        .ascii "2,abc,51,101,111,301,11\n"
        .equ BAD_CSV_LEN, . - bad_csv_content

col_temp:
        .asciz "TEMP"
col_soil1:
        .asciz "SOIL1"
col_bad:
        .asciz "NO_EXISTE"

case_temp:
        .ascii "CASE=valid_temp\n"
        .equ CASE_TEMP_LEN, . - case_temp
case_soil1:
        .ascii "CASE=valid_soil1\n"
        .equ CASE_SOIL1_LEN, . - case_soil1
case_bad_range:
        .ascii "CASE=bad_range\n"
        .equ CASE_BAD_RANGE_LEN, . - case_bad_range
case_bad_column:
        .ascii "CASE=bad_column\n"
        .equ CASE_BAD_COLUMN_LEN, . - case_bad_column
case_end_out:
        .ascii "CASE=end_out_of_file\n"
        .equ CASE_END_OUT_LEN, . - case_end_out
case_non_numeric:
        .ascii "CASE=non_numeric_value\n"
        .equ CASE_NON_NUMERIC_LEN, . - case_non_numeric

msg_status_ok:
        .ascii "STATUS=OK\n"
        .equ MSG_STATUS_OK_LEN, . - msg_status_ok
msg_status_error:
        .ascii "STATUS=ERROR\n"
        .equ MSG_STATUS_ERROR_LEN, . - msg_status_error
msg_count:
        .ascii "COUNT="
        .equ MSG_COUNT_LEN, . - msg_count
msg_values:
        .ascii "VALUES="
        .equ MSG_VALUES_LEN, . - msg_values
msg_error:
        .ascii "ERROR="
        .equ MSG_ERROR_LEN, . - msg_error
msg_detail:
        .ascii "DETAIL="
        .equ MSG_DETAIL_LEN, . - msg_detail
msg_newline:
        .ascii "\n"
msg_comma:
        .ascii ","

err_invalid_arguments:
        .ascii "invalid_arguments"
        .equ ERR_INVALID_ARGUMENTS_LEN, . - err_invalid_arguments
err_invalid_range:
        .ascii "invalid_range"
        .equ ERR_INVALID_RANGE_LEN, . - err_invalid_range
err_invalid_column:
        .ascii "invalid_column"
        .equ ERR_INVALID_COLUMN_LEN, . - err_invalid_column
err_file_not_found:
        .ascii "file_not_found"
        .equ ERR_FILE_NOT_FOUND_LEN, . - err_file_not_found
err_file_read_error:
        .ascii "file_read_error"
        .equ ERR_FILE_READ_ERROR_LEN, . - err_file_read_error
err_file_too_large:
        .ascii "file_too_large"
        .equ ERR_FILE_TOO_LARGE_LEN, . - err_file_too_large
err_missing_header:
        .ascii "missing_header"
        .equ ERR_MISSING_HEADER_LEN, . - err_missing_header
err_column_not_present:
        .ascii "column_not_present"
        .equ ERR_COLUMN_NOT_PRESENT_LEN, . - err_column_not_present
err_non_numeric_value:
        .ascii "non_numeric_value"
        .equ ERR_NON_NUMERIC_VALUE_LEN, . - err_non_numeric_value
err_insufficient_data:
        .ascii "insufficient_data"
        .equ ERR_INSUFFICIENT_DATA_LEN, . - err_insufficient_data
err_output_limit:
        .ascii "output_limit_reached"
        .equ ERR_OUTPUT_LIMIT_LEN, . - err_output_limit
err_unknown:
        .ascii "unknown_error"
        .equ ERR_UNKNOWN_LEN, . - err_unknown

detail_ok:
        .ascii "ok"
        .equ DETAIL_OK_LEN, . - detail_ok
detail_bad_range:
        .ascii "linea_final_menor_que_linea_inicial"
        .equ DETAIL_BAD_RANGE_LEN, . - detail_bad_range
detail_bad_column:
        .ascii "columna_logica_no_permitida"
        .equ DETAIL_BAD_COLUMN_LEN, . - detail_bad_column
detail_end_out:
        .ascii "linea_final_fuera_del_archivo"
        .equ DETAIL_END_OUT_LEN, . - detail_end_out
detail_non_numeric:
        .ascii "valor_no_numerico_en_el_rango"
        .equ DETAIL_NON_NUMERIC_LEN, . - detail_non_numeric

        .bss
        .balign 8
values:
        .skip 64 * 8

        .text
        .global _start
        .extern leer_csv_rango_columna
        .extern escribir_archivo
        .extern escribir_salida
        .extern escribir_campo_numero
        .extern convertir_entero_ascii

_start:
        // esto crea un csv temporal para el caso no numerico
        ldr x0, =bad_csv_file
        ldr x1, =bad_csv_content
        mov x2, #BAD_CSV_LEN
        bl escribir_archivo

        // esto prueba rango valido con temp
        ldr x0, =case_temp
        mov x1, #CASE_TEMP_LEN
        bl escribir_salida
        ldr x0, =csv_file
        mov x1, #1
        mov x2, #3
        ldr x3, =col_temp
        ldr x4, =values
        mov x5, #16
        bl leer_csv_rango_columna
        ldr x2, =detail_ok
        mov x3, #DETAIL_OK_LEN
        bl imprimir_resultado

        // esto prueba rango valido con soil1
        ldr x0, =case_soil1
        mov x1, #CASE_SOIL1_LEN
        bl escribir_salida
        ldr x0, =csv_file
        mov x1, #2
        mov x2, #4
        ldr x3, =col_soil1
        ldr x4, =values
        mov x5, #16
        bl leer_csv_rango_columna
        ldr x2, =detail_ok
        mov x3, #DETAIL_OK_LEN
        bl imprimir_resultado

        // esto prueba rango invalido
        ldr x0, =case_bad_range
        mov x1, #CASE_BAD_RANGE_LEN
        bl escribir_salida
        ldr x0, =csv_file
        mov x1, #5
        mov x2, #3
        ldr x3, =col_temp
        ldr x4, =values
        mov x5, #16
        bl leer_csv_rango_columna
        ldr x2, =detail_bad_range
        mov x3, #DETAIL_BAD_RANGE_LEN
        bl imprimir_resultado

        // esto prueba columna inexistente
        ldr x0, =case_bad_column
        mov x1, #CASE_BAD_COLUMN_LEN
        bl escribir_salida
        ldr x0, =csv_file
        mov x1, #1
        mov x2, #3
        ldr x3, =col_bad
        ldr x4, =values
        mov x5, #16
        bl leer_csv_rango_columna
        ldr x2, =detail_bad_column
        mov x3, #DETAIL_BAD_COLUMN_LEN
        bl imprimir_resultado

        // esto prueba linea final fuera del archivo
        ldr x0, =case_end_out
        mov x1, #CASE_END_OUT_LEN
        bl escribir_salida
        ldr x0, =csv_file
        mov x1, #1
        mov x2, #50
        ldr x3, =col_temp
        ldr x4, =values
        mov x5, #64
        bl leer_csv_rango_columna
        ldr x2, =detail_end_out
        mov x3, #DETAIL_END_OUT_LEN
        bl imprimir_resultado

        // esto prueba valor no numerico
        ldr x0, =case_non_numeric
        mov x1, #CASE_NON_NUMERIC_LEN
        bl escribir_salida
        ldr x0, =bad_csv_file
        mov x1, #1
        mov x2, #2
        ldr x3, =col_temp
        ldr x4, =values
        mov x5, #16
        bl leer_csv_rango_columna
        ldr x2, =detail_non_numeric
        mov x3, #DETAIL_NON_NUMERIC_LEN
        bl imprimir_resultado

        // esto elimina el csv temporal
        mov x0, #-100
        ldr x1, =bad_csv_file
        mov x2, #0
        mov x8, #35
        svc #0

        mov x0, #0
        mov x8, #93
        svc #0

imprimir_resultado:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!
        stp x23, x24, [sp, #-16]!

        mov x19, x0                  // esto guarda el estado
        mov x20, x1                  // esto guarda la cantidad
        mov x21, x2                  // esto guarda el detalle
        mov x22, x3                  // esto guarda el largo del detalle

        cmp x19, #UTILS_OK
        bne imprimir_resultado_error

        ldr x0, =msg_status_ok
        mov x1, #MSG_STATUS_OK_LEN
        bl escribir_salida
        ldr x0, =msg_count
        mov x1, #MSG_COUNT_LEN
        mov x2, x20
        bl escribir_campo_numero
        bl imprimir_salto
        ldr x0, =msg_values
        mov x1, #MSG_VALUES_LEN
        bl escribir_salida
        bl imprimir_valores
        bl imprimir_blanco
        b imprimir_resultado_retornar

imprimir_resultado_error:
        ldr x0, =msg_status_error
        mov x1, #MSG_STATUS_ERROR_LEN
        bl escribir_salida
        ldr x0, =msg_error
        mov x1, #MSG_ERROR_LEN
        bl escribir_salida
        mov x0, x19
        bl imprimir_nombre_error
        bl imprimir_salto
        ldr x0, =msg_detail
        mov x1, #MSG_DETAIL_LEN
        bl escribir_salida
        mov x0, x21
        mov x1, x22
        bl escribir_salida
        bl imprimir_blanco

imprimir_resultado_retornar:
        ldp x23, x24, [sp], #16
        ldp x21, x22, [sp], #16
        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret

imprimir_valores:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!

        ldr x19, =values             // esto apunta al arreglo de valores
        mov x21, #0                  // esto cuenta valores impresos
imprimir_valores_bucle:
        cmp x21, x20
        bge imprimir_valores_fin
        ldr x0, [x19, x21, lsl #3]
        bl convertir_entero_ascii
        bl escribir_salida
        add x21, x21, #1
        cmp x21, x20
        bge imprimir_valores_bucle
        ldr x0, =msg_comma
        mov x1, #1
        bl escribir_salida
        b imprimir_valores_bucle
imprimir_valores_fin:
        bl imprimir_salto
        ldp x21, x22, [sp], #16
        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret

imprimir_nombre_error:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        mov x9, #UTILS_INVALID_ARGUMENTS
        cmp x0, x9
        beq nombre_error_argumentos_invalidos
        mov x9, #UTILS_INVALID_RANGE
        cmp x0, x9
        beq nombre_error_rango_invalido
        mov x9, #UTILS_INVALID_COLUMN
        cmp x0, x9
        beq nombre_error_columna_invalida
        mov x9, #UTILS_FILE_NOT_FOUND
        cmp x0, x9
        beq nombre_error_archivo_no_encontrado
        mov x9, #UTILS_FILE_READ_ERROR
        cmp x0, x9
        beq nombre_error_lectura_archivo
        mov x9, #UTILS_FILE_TOO_LARGE
        cmp x0, x9
        beq nombre_error_archivo_grande
        mov x9, #UTILS_MISSING_HEADER
        cmp x0, x9
        beq nombre_error_encabezado_faltante
        mov x9, #UTILS_COLUMN_NOT_PRESENT
        cmp x0, x9
        beq nombre_error_columna_ausente
        mov x9, #UTILS_NON_NUMERIC_VALUE
        cmp x0, x9
        beq nombre_error_valor_no_numerico
        mov x9, #UTILS_INSUFFICIENT_DATA
        cmp x0, x9
        beq nombre_error_datos_insuficientes
        mov x9, #UTILS_OUTPUT_LIMIT_REACHED
        cmp x0, x9
        beq nombre_error_limite_salida
        ldr x0, =err_unknown
        mov x1, #ERR_UNKNOWN_LEN
        b escribir_nombre_error
nombre_error_argumentos_invalidos:
        ldr x0, =err_invalid_arguments
        mov x1, #ERR_INVALID_ARGUMENTS_LEN
        b escribir_nombre_error
nombre_error_rango_invalido:
        ldr x0, =err_invalid_range
        mov x1, #ERR_INVALID_RANGE_LEN
        b escribir_nombre_error
nombre_error_columna_invalida:
        ldr x0, =err_invalid_column
        mov x1, #ERR_INVALID_COLUMN_LEN
        b escribir_nombre_error
nombre_error_archivo_no_encontrado:
        ldr x0, =err_file_not_found
        mov x1, #ERR_FILE_NOT_FOUND_LEN
        b escribir_nombre_error
nombre_error_lectura_archivo:
        ldr x0, =err_file_read_error
        mov x1, #ERR_FILE_READ_ERROR_LEN
        b escribir_nombre_error
nombre_error_archivo_grande:
        ldr x0, =err_file_too_large
        mov x1, #ERR_FILE_TOO_LARGE_LEN
        b escribir_nombre_error
nombre_error_encabezado_faltante:
        ldr x0, =err_missing_header
        mov x1, #ERR_MISSING_HEADER_LEN
        b escribir_nombre_error
nombre_error_columna_ausente:
        ldr x0, =err_column_not_present
        mov x1, #ERR_COLUMN_NOT_PRESENT_LEN
        b escribir_nombre_error
nombre_error_valor_no_numerico:
        ldr x0, =err_non_numeric_value
        mov x1, #ERR_NON_NUMERIC_VALUE_LEN
        b escribir_nombre_error
nombre_error_datos_insuficientes:
        ldr x0, =err_insufficient_data
        mov x1, #ERR_INSUFFICIENT_DATA_LEN
        b escribir_nombre_error
nombre_error_limite_salida:
        ldr x0, =err_output_limit
        mov x1, #ERR_OUTPUT_LIMIT_LEN
escribir_nombre_error:
        bl escribir_salida
        ldp x29, x30, [sp], #16
        ret

imprimir_salto:
        ldr x0, =msg_newline
        mov x1, #1
        b escribir_salida

imprimir_blanco:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        bl imprimir_salto
        bl imprimir_salto
        ldp x29, x30, [sp], #16
        ret
