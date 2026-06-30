
.equ MAX_VALORES, 8192

        .equ COD_OK, 0
        .equ COD_ARGUMENTOS_INVALIDOS, -1
        .equ COD_RANGO_INVALIDO, -2
        .equ COD_COLUMNA_INVALIDA, -3
        .equ COD_ARCHIVO_NO_EXISTE, -4
        .equ COD_ERROR_LECTURA, -5
        .equ COD_ARCHIVO_GRANDE, -6
        .equ COD_ENCABEZADO_FALTANTE, -7
        .equ COD_COLUMNA_AUSENTE, -8
        .equ COD_VALOR_NO_NUMERICO, -9
        .equ COD_DATOS_INSUFICIENTES, -10
        .equ COD_LIMITE_SALIDA, -11

        .data
msg_calc:
        .ascii "CALC=MEAN\n"
        .equ MSG_CALC_LEN, . - msg_calc
msg_status_ok:
        .ascii "STATUS=OK\n"
        .equ MSG_STATUS_OK_LEN, . - msg_status_ok
msg_status_error:
        .ascii "STATUS=ERROR\n"
        .equ MSG_STATUS_ERROR_LEN, . - msg_status_error
msg_column:
        .ascii "COLUMN="
        .equ MSG_COLUMN_LEN, . - msg_column
msg_window_start:
        .ascii "WINDOW_START="
        .equ MSG_WINDOW_START_LEN, . - msg_window_start
msg_window_end:
        .ascii "WINDOW_END="
        .equ MSG_WINDOW_END_LEN, . - msg_window_end
msg_count:
        .ascii "COUNT="
        .equ MSG_COUNT_LEN, . - msg_count
msg_mean:
        .ascii "MEAN="
        .equ MSG_MEAN_LEN, . - msg_mean
msg_error:
        .ascii "ERROR="
        .equ MSG_ERROR_LEN, . - msg_error
msg_detail:
        .ascii "DETAIL="
        .equ MSG_DETAIL_LEN, . - msg_detail
msg_newline:
        .ascii "\n"

err_argumentos_invalidos:
        .ascii "invalid_arguments"
        .equ ERR_ARGUMENTOS_INVALIDOS_LEN, . - err_argumentos_invalidos
err_rango_invalido:
        .ascii "invalid_range"
        .equ ERR_RANGO_INVALIDO_LEN, . - err_rango_invalido
err_columna_invalida:
        .ascii "invalid_column"
        .equ ERR_COLUMNA_INVALIDA_LEN, . - err_columna_invalida
err_archivo_no_existe:
        .ascii "file_not_found"
        .equ ERR_ARCHIVO_NO_EXISTE_LEN, . - err_archivo_no_existe
err_error_lectura:
        .ascii "file_read_error"
        .equ ERR_ERROR_LECTURA_LEN, . - err_error_lectura
err_archivo_grande:
        .ascii "file_too_large"
        .equ ERR_ARCHIVO_GRANDE_LEN, . - err_archivo_grande
err_encabezado_faltante:
        .ascii "missing_header"
        .equ ERR_ENCABEZADO_FALTANTE_LEN, . - err_encabezado_faltante
err_columna_ausente:
        .ascii "column_not_present"
        .equ ERR_COLUMNA_AUSENTE_LEN, . - err_columna_ausente
err_valor_no_numerico:
        .ascii "non_numeric_value"
        .equ ERR_VALOR_NO_NUMERICO_LEN, . - err_valor_no_numerico
err_datos_insuficientes:
        .ascii "insufficient_data"
        .equ ERR_DATOS_INSUFICIENTES_LEN, . - err_datos_insuficientes
err_limite_salida:
        .ascii "output_limit_reached"
        .equ ERR_LIMITE_SALIDA_LEN, . - err_limite_salida
err_desconocido:
        .ascii "unknown_error"
        .equ ERR_DESCONOCIDO_LEN, . - err_desconocido

det_argumentos:
        .ascii "uso_modulo_1_media_archivo_inicio_fin_columna"
        .equ DET_ARGUMENTOS_LEN, . - det_argumentos
det_rango:
        .ascii "rango_invalido_o_fuera_del_archivo"
        .equ DET_RANGO_LEN, . - det_rango
det_columna:
        .ascii "columna_logica_no_permitida"
        .equ DET_COLUMNA_LEN, . - det_columna
det_archivo:
        .ascii "no_se_pudo_abrir_el_archivo"
        .equ DET_ARCHIVO_LEN, . - det_archivo
det_lectura:
        .ascii "no_se_pudo_leer_el_archivo"
        .equ DET_LECTURA_LEN, . - det_lectura
det_archivo_grande:
        .ascii "archivo_mayor_al_buffer"
        .equ DET_ARCHIVO_GRANDE_LEN, . - det_archivo_grande
det_encabezado:
        .ascii "encabezado_csv_no_encontrado"
        .equ DET_ENCABEZADO_LEN, . - det_encabezado
det_columna_ausente:
        .ascii "columna_no_presente_en_encabezado"
        .equ DET_COLUMNA_AUSENTE_LEN, . - det_columna_ausente
det_no_numerico:
        .ascii "valor_no_numerico_en_el_rango"
        .equ DET_NO_NUMERICO_LEN, . - det_no_numerico
det_sin_datos:
        .ascii "rango_sin_datos"
        .equ DET_SIN_DATOS_LEN, . - det_sin_datos
det_limite:
        .ascii "rango_supera_el_arreglo_destino"
        .equ DET_LIMITE_LEN, . - det_limite
det_desconocido:
        .ascii "error_no_mapeado"
        .equ DET_DESCONOCIDO_LEN, . - det_desconocido

        .bss
        .balign 8
valores:
        .skip MAX_VALORES * 8
ruta_guardada:
        .skip 8
inicio_guardado:
        .skip 8
fin_guardado:
        .skip 8
columna_guardada:
        .skip 8
columna_largo:
        .skip 8
conteo_guardado:
        .skip 8
media_guardada:
        .skip 8

        .text
        .global _start
        .extern leer_csv_rango_columna
        .extern convertir_texto_entero_sin_signo
        .extern contar_cadena
        .extern escribir_salida
        .extern escribir_campo_numero

_start:
        // esto valida la cantidad de argumentos
        ldr x0, [sp]
        cmp x0, #5
        bne error_argumentos

        // esto guarda la ruta del archivo
        ldr x0, [sp, #16]
        ldr x1, =ruta_guardada
        str x0, [x1]

        // esto convierte la linea inicial
        ldr x0, [sp, #24]
        bl convertir_texto_entero_sin_signo
        cbz x1, error_argumentos
        ldr x2, =inicio_guardado
        str x0, [x2]

        // esto convierte la linea final
        ldr x0, [sp, #32]
        bl convertir_texto_entero_sin_signo
        cbz x1, error_argumentos
        ldr x2, =fin_guardado
        str x0, [x2]

        // esto guarda la columna pedida
        ldr x0, [sp, #40]
        ldr x1, =columna_guardada
        str x0, [x1]
        bl contar_cadena
        ldr x1, =columna_largo
        str x0, [x1]

        // esto lee el rango de datos con utils
        ldr x0, =ruta_guardada
        ldr x0, [x0]
        ldr x1, =inicio_guardado
        ldr x1, [x1]
        ldr x2, =fin_guardado
        ldr x2, [x2]
        ldr x3, =columna_guardada
        ldr x3, [x3]
        ldr x4, =valores
        ldr x5, =MAX_VALORES
        bl leer_csv_rango_columna
        cmp x0, #COD_OK
        bne error_utils

        // esto valida que haya datos
        cbz x1, error_sin_datos
        ldr x2, =conteo_guardado
        str x1, [x2]

        // esto calcula la media en arm64
        ldr x19, =valores
        mov x20, x1
        mov x21, #0
        mov x22, #0
sumar_valores:
        cmp x21, x20
        bge calcular_media
        ldr x23, [x19, x21, lsl #3]
        add x22, x22, x23
        add x21, x21, #1
        b sumar_valores

calcular_media:
        sdiv x24, x22, x20
        ldr x0, =media_guardada
        str x24, [x0]
        bl imprimir_ok
        mov x0, #0
        mov x8, #93
        svc #0

error_argumentos:
        mov x0, #COD_ARGUMENTOS_INVALIDOS
        b imprimir_error_y_salir

error_utils:
        b imprimir_error_y_salir

error_sin_datos:
        mov x0, #COD_DATOS_INSUFICIENTES

imprimir_error_y_salir:
        mov x19, x0
        bl imprimir_error
        mov x0, #1
        mov x8, #93
        svc #0

imprimir_ok:
        stp x29, x30, [sp, #-16]!
        mov x29, sp

        // esto imprime el nombre del calculo
        ldr x0, =msg_calc
        mov x1, #MSG_CALC_LEN
        bl escribir_salida

        // esto imprime la columna solicitada
        ldr x0, =msg_column
        mov x1, #MSG_COLUMN_LEN
        bl escribir_salida
        ldr x0, =columna_guardada
        ldr x0, [x0]
        ldr x1, =columna_largo
        ldr x1, [x1]
        bl escribir_salida
        bl imprimir_salto

        // esto imprime la linea inicial
        ldr x0, =msg_window_start
        mov x1, #MSG_WINDOW_START_LEN
        ldr x2, =inicio_guardado
        ldr x2, [x2]
        bl escribir_campo_numero
        bl imprimir_salto

        // esto imprime la linea final
        ldr x0, =msg_window_end
        mov x1, #MSG_WINDOW_END_LEN
        ldr x2, =fin_guardado
        ldr x2, [x2]
        bl escribir_campo_numero
        bl imprimir_salto

        // esto imprime el conteo
        ldr x0, =msg_count
        mov x1, #MSG_COUNT_LEN
        ldr x2, =conteo_guardado
        ldr x2, [x2]
        bl escribir_campo_numero
        bl imprimir_salto

        // esto imprime la media
        ldr x0, =msg_mean
        mov x1, #MSG_MEAN_LEN
        ldr x2, =media_guardada
        ldr x2, [x2]
        bl escribir_campo_numero
        bl imprimir_salto

        // esto imprime estado correcto
        ldr x0, =msg_status_ok
        mov x1, #MSG_STATUS_OK_LEN
        bl escribir_salida

        ldp x29, x30, [sp], #16
        ret

imprimir_error:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        str x19, [sp, #-16]!

        // esto imprime el nombre del calculo
        ldr x0, =msg_calc
        mov x1, #MSG_CALC_LEN
        bl escribir_salida

        // esto imprime estado de error
        ldr x0, =msg_status_error
        mov x1, #MSG_STATUS_ERROR_LEN
        bl escribir_salida

        // esto imprime el codigo de error
        ldr x0, =msg_error
        mov x1, #MSG_ERROR_LEN
        bl escribir_salida
        ldr x0, [sp]
        bl seleccionar_texto_error
        bl escribir_salida
        bl imprimir_salto

        // esto imprime el detalle del error
        ldr x0, =msg_detail
        mov x1, #MSG_DETAIL_LEN
        bl escribir_salida
        ldr x0, [sp]
        bl seleccionar_texto_detalle
        bl escribir_salida
        bl imprimir_salto

        ldr x19, [sp], #16
        ldp x29, x30, [sp], #16
        ret

seleccionar_texto_error:
        mov x9, #COD_ARGUMENTOS_INVALIDOS
        cmp x0, x9
        beq texto_error_argumentos
        mov x9, #COD_RANGO_INVALIDO
        cmp x0, x9
        beq texto_error_rango
        mov x9, #COD_COLUMNA_INVALIDA
        cmp x0, x9
        beq texto_error_columna
        mov x9, #COD_ARCHIVO_NO_EXISTE
        cmp x0, x9
        beq texto_error_archivo
        mov x9, #COD_ERROR_LECTURA
        cmp x0, x9
        beq texto_error_lectura
        mov x9, #COD_ARCHIVO_GRANDE
        cmp x0, x9
        beq texto_error_archivo_grande
        mov x9, #COD_ENCABEZADO_FALTANTE
        cmp x0, x9
        beq texto_error_encabezado
        mov x9, #COD_COLUMNA_AUSENTE
        cmp x0, x9
        beq texto_error_columna_ausente
        mov x9, #COD_VALOR_NO_NUMERICO
        cmp x0, x9
        beq texto_error_no_numerico
        mov x9, #COD_DATOS_INSUFICIENTES
        cmp x0, x9
        beq texto_error_sin_datos
        mov x9, #COD_LIMITE_SALIDA
        cmp x0, x9
        beq texto_error_limite
        ldr x0, =err_desconocido
        mov x1, #ERR_DESCONOCIDO_LEN
        ret
texto_error_argumentos:
        ldr x0, =err_argumentos_invalidos
        mov x1, #ERR_ARGUMENTOS_INVALIDOS_LEN
        ret
texto_error_rango:
        ldr x0, =err_rango_invalido
        mov x1, #ERR_RANGO_INVALIDO_LEN
        ret
texto_error_columna:
        ldr x0, =err_columna_invalida
        mov x1, #ERR_COLUMNA_INVALIDA_LEN
        ret
texto_error_archivo:
        ldr x0, =err_archivo_no_existe
        mov x1, #ERR_ARCHIVO_NO_EXISTE_LEN
        ret
texto_error_lectura:
        ldr x0, =err_error_lectura
        mov x1, #ERR_ERROR_LECTURA_LEN
        ret
texto_error_archivo_grande:
        ldr x0, =err_archivo_grande
        mov x1, #ERR_ARCHIVO_GRANDE_LEN
        ret
texto_error_encabezado:
        ldr x0, =err_encabezado_faltante
        mov x1, #ERR_ENCABEZADO_FALTANTE_LEN
        ret
texto_error_columna_ausente:
        ldr x0, =err_columna_ausente
        mov x1, #ERR_COLUMNA_AUSENTE_LEN
        ret
texto_error_no_numerico:
        ldr x0, =err_valor_no_numerico
        mov x1, #ERR_VALOR_NO_NUMERICO_LEN
        ret
texto_error_sin_datos:
        ldr x0, =err_datos_insuficientes
        mov x1, #ERR_DATOS_INSUFICIENTES_LEN
        ret
texto_error_limite:
        ldr x0, =err_limite_salida
        mov x1, #ERR_LIMITE_SALIDA_LEN
        ret

seleccionar_texto_detalle:
        mov x9, #COD_ARGUMENTOS_INVALIDOS
        cmp x0, x9
        beq texto_detalle_argumentos
        mov x9, #COD_RANGO_INVALIDO
        cmp x0, x9
        beq texto_detalle_rango
        mov x9, #COD_COLUMNA_INVALIDA
        cmp x0, x9
        beq texto_detalle_columna
        mov x9, #COD_ARCHIVO_NO_EXISTE
        cmp x0, x9
        beq texto_detalle_archivo
        mov x9, #COD_ERROR_LECTURA
        cmp x0, x9
        beq texto_detalle_lectura
        mov x9, #COD_ARCHIVO_GRANDE
        cmp x0, x9
        beq texto_detalle_archivo_grande
        mov x9, #COD_ENCABEZADO_FALTANTE
        cmp x0, x9
        beq texto_detalle_encabezado
        mov x9, #COD_COLUMNA_AUSENTE
        cmp x0, x9
        beq texto_detalle_columna_ausente
        mov x9, #COD_VALOR_NO_NUMERICO
        cmp x0, x9
        beq texto_detalle_no_numerico
        mov x9, #COD_DATOS_INSUFICIENTES
        cmp x0, x9
        beq texto_detalle_sin_datos
        mov x9, #COD_LIMITE_SALIDA
        cmp x0, x9
        beq texto_detalle_limite
        ldr x0, =det_desconocido
        mov x1, #DET_DESCONOCIDO_LEN
        ret
texto_detalle_argumentos:
        ldr x0, =det_argumentos
        mov x1, #DET_ARGUMENTOS_LEN
        ret
texto_detalle_rango:
        ldr x0, =det_rango
        mov x1, #DET_RANGO_LEN
        ret
texto_detalle_columna:
        ldr x0, =det_columna
        mov x1, #DET_COLUMNA_LEN
        ret
texto_detalle_archivo:
        ldr x0, =det_archivo
        mov x1, #DET_ARCHIVO_LEN
        ret
texto_detalle_lectura:
        ldr x0, =det_lectura
        mov x1, #DET_LECTURA_LEN
        ret
texto_detalle_archivo_grande:
        ldr x0, =det_archivo_grande
        mov x1, #DET_ARCHIVO_GRANDE_LEN
        ret
texto_detalle_encabezado:
        ldr x0, =det_encabezado
        mov x1, #DET_ENCABEZADO_LEN
        ret
texto_detalle_columna_ausente:
        ldr x0, =det_columna_ausente
        mov x1, #DET_COLUMNA_AUSENTE_LEN
        ret
texto_detalle_no_numerico:
        ldr x0, =det_no_numerico
        mov x1, #DET_NO_NUMERICO_LEN
        ret
texto_detalle_sin_datos:
        ldr x0, =det_sin_datos
        mov x1, #DET_SIN_DATOS_LEN
        ret
texto_detalle_limite:
        ldr x0, =det_limite
        mov x1, #DET_LIMITE_LEN
        ret

imprimir_salto:
        ldr x0, =msg_newline
        mov x1, #1
        b escribir_salida
