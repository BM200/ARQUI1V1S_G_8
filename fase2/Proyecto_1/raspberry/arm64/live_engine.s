.data

msg_action:
    .ascii "ACTION="
    len_msg_action = . - msg_action

msg_target:
    .ascii "TARGET="
    len_msg_target = . - msg_target

msg_risk:
    .ascii "RISK="
    len_msg_risk = . - msg_risk

msg_reason:
    .ascii "REASON="
    len_msg_reason = . - msg_reason

msg_value:
    .ascii "VALUE="
    len_msg_value = . - msg_value

msg_indicator:
    .ascii "INDICATOR="
    len_msg_indicator = . - msg_indicator

msg_status_ok:
    .ascii "STATUS=OK\n"
    len_msg_status_ok = . - msg_status_ok

msg_status_error:
    .ascii "STATUS=ERROR\n"
    len_msg_status_error = . - msg_status_error

msg_error_invalid:
    .ascii "ERROR=INVALID_INPUT\n"
    len_msg_error_invalid = . - msg_error_invalid

msg_detail_invalid:
    .ascii "DETAIL=se esperaban 7 campos numericos\n"
    len_msg_detail_invalid = . - msg_detail_invalid

txt_alarm:
    .ascii "ALARM_ON"
    len_txt_alarm = . - txt_alarm

txt_riego1:
    .ascii "RIEGO_1_ON"
    len_txt_riego1 = . - txt_riego1

txt_riego2:
    .ascii "RIEGO_2_ON"
    len_txt_riego2 = . - txt_riego2

txt_light:
    .ascii "LIGHT_ON"
    len_txt_light = . - txt_light

txt_fan:
    .ascii "FAN_ON"
    len_txt_fan = . - txt_fan

txt_green:
    .ascii "LED_GREEN"
    len_txt_green = . - txt_green

txt_none:
    .ascii "NO_ACTION"
    len_txt_none = . - txt_none

txt_target_gas:
    .ascii "GAS"
    len_txt_target_gas = . - txt_target_gas

txt_target_soil1:
    .ascii "SOIL1"
    len_txt_target_soil1 = . - txt_target_soil1

txt_target_soil2:
    .ascii "SOIL2"
    len_txt_target_soil2 = . - txt_target_soil2

txt_target_luz:
    .ascii "LUZ"
    len_txt_target_luz = . - txt_target_luz

txt_target_temp:
    .ascii "TEMP"
    len_txt_target_temp = . - txt_target_temp

txt_target_system:
    .ascii "SYSTEM"
    len_txt_target_system = . - txt_target_system

txt_risk_high:
    .ascii "HIGH"
    len_txt_risk_high = . - txt_risk_high

txt_risk_medium:
    .ascii "MEDIUM"
    len_txt_risk_medium = . - txt_risk_medium

txt_risk_normal:
    .ascii "NORMAL"
    len_txt_risk_normal = . - txt_risk_normal

txt_reason_gas:
    .ascii "gas_alto"
    len_txt_reason_gas = . - txt_reason_gas

txt_reason_soil1:
    .ascii "suelo1_bajo"
    len_txt_reason_soil1 = . - txt_reason_soil1

txt_reason_soil2:
    .ascii "suelo2_bajo"
    len_txt_reason_soil2 = . - txt_reason_soil2

txt_reason_luz:
    .ascii "luz_baja"
    len_txt_reason_luz = . - txt_reason_luz

txt_reason_temp:
    .ascii "temperatura_alta"
    len_txt_reason_temp = . - txt_reason_temp

txt_reason_ok:
    .ascii "condicion_normal"
    len_txt_reason_ok = . - txt_reason_ok

txt_indicator_amp:
    .ascii "GAS_AMP"
    len_txt_indicator_amp = . - txt_indicator_amp

txt_indicator_avg:
    .ascii "AVG"
    len_txt_indicator_avg = . - txt_indicator_avg

txt_indicator_trend:
    .ascii "TREND"
    len_txt_indicator_trend = . - txt_indicator_trend

newline:
    .ascii "\n"

.bss

input_buffer:
    .skip 256

values:
    .skip 56

histories:
    .skip 240

hist_count:
    .skip 8

hist_index:
    .skip 8

num_buffer:
    .skip 32

.text
.global _start
.extern convertir_span_entero

_start:
bucle_principal:
    bl leer_linea
    cmp x0, #0
    ble salir_ok

    ldr x19, =input_buffer
    add x20, x19, x0
    bl limpiar_fin_linea

    ldrb w0, [x19]
    cmp w0, #'n'
    beq salir_ok

    bl parsear_lectura
    cbz x0, entrada_invalida

    bl guardar_historial
    bl decidir_accion
    bl emitir_respuesta_ok
    b bucle_principal

entrada_invalida:
    bl emitir_respuesta_error
    b bucle_principal

salir_ok:
    mov x0, #0
    mov x8, #93
    svc #0


// esto lee una linea desde stdin
leer_linea:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    ldr x19, =input_buffer
    mov x20, #0

leer_linea_loop:
    cmp x20, #255
    bge leer_linea_fin
    mov x0, #0
    add x1, x19, x20
    mov x2, #1
    mov x8, #63
    svc #0

    cmp x0, #0
    blt leer_linea_error
    cbz x0, leer_linea_eof

    ldrb w1, [x19, x20]
    add x20, x20, #1
    cmp w1, #10
    beq leer_linea_fin
    b leer_linea_loop

leer_linea_eof:
    cbnz x20, leer_linea_fin
    mov x0, #0
    b leer_linea_ret

leer_linea_error:
    mov x0, #0
    b leer_linea_ret

leer_linea_fin:
    mov x0, x20

leer_linea_ret:
    ldp x29, x30, [sp], #16
    ret


// esto elimina saltos de linea al final
limpiar_fin_linea:
    cmp x20, x19
    ble limpiar_fin_linea_fin
    sub x0, x20, #1
    ldrb w1, [x0]
    cmp w1, #10
    beq limpiar_fin_linea_recorta
    cmp w1, #13
    beq limpiar_fin_linea_recorta
    b limpiar_fin_linea_fin
limpiar_fin_linea_recorta:
    mov x20, x0
    b limpiar_fin_linea
limpiar_fin_linea_fin:
    ret


// esto separa los 7 campos csv
parsear_lectura:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    stp x19, x20, [sp, #-16]!
    stp x21, x22, [sp, #-16]!
    stp x23, x24, [sp, #-16]!
    stp x25, x26, [sp, #-16]!

    mov x21, x19
    mov x22, x20
    mov x23, #0
    ldr x26, =values

parsear_campo:
    cmp x23, #7
    bge parsear_invalido
    cmp x21, x22
    bge parsear_invalido

    mov x24, x21
    mov x25, #0

buscar_fin_campo:
    cmp x24, x22
    bge fin_campo
    ldrb w0, [x24]
    cmp w0, #','
    beq fin_campo_con_coma
    add x24, x24, #1
    b buscar_fin_campo

fin_campo_con_coma:
    mov x25, #1

fin_campo:
    cmp x24, x21
    beq parsear_invalido

    mov x0, x21
    mov x1, x24
    bl convertir_span_entero
    cbz x1, parsear_invalido

    str x0, [x26, x23, lsl #3]
    add x23, x23, #1

    cmp x23, #7
    beq validar_fin_csv
    cbz x25, parsear_invalido
    add x21, x24, #1
    b parsear_campo

validar_fin_csv:
    cbnz x25, parsear_invalido
    mov x0, #1
    b parsear_fin

parsear_invalido:
    mov x0, #0

parsear_fin:
    ldp x25, x26, [sp], #16
    ldp x23, x24, [sp], #16
    ldp x21, x22, [sp], #16
    ldp x19, x20, [sp], #16
    ldp x29, x30, [sp], #16
    ret


// esto guarda la lectura en historial circular
guardar_historial:
    stp x29, x30, [sp, #-16]!
    mov x29, sp

    ldr x0, =hist_index
    ldr x1, [x0]
    mov x2, #6
    mul x3, x1, x2
    ldr x4, =histories
    add x4, x4, x3, lsl #3
    ldr x5, =values
    mov x6, #0

guardar_historial_loop:
    cmp x6, #6
    bge guardar_historial_count
    ldr x7, [x5, x6, lsl #3]
    str x7, [x4, x6, lsl #3]
    add x6, x6, #1
    b guardar_historial_loop

guardar_historial_count:
    add x1, x1, #1
    cmp x1, #5
    blt guardar_historial_index_ok
    mov x1, #0
guardar_historial_index_ok:
    str x1, [x0]

    ldr x0, =hist_count
    ldr x1, [x0]
    cmp x1, #5
    bge guardar_historial_fin
    add x1, x1, #1
    str x1, [x0]

guardar_historial_fin:
    ldp x29, x30, [sp], #16
    ret


// esto decide la accion principal por prioridad
decidir_accion:
    stp x29, x30, [sp, #-16]!
    mov x29, sp

    ldr x19, =values

    mov x0, #5
    bl calcular_amplitud
    mov x28, x0

    ldr x0, [x19, #40]
    cmp x0, #800
    bge decidir_alarm
    cmp x28, #400
    bge decidir_alarm

    ldr x0, [x19, #16]
    cmp x0, #30
    blt decidir_riego1

    ldr x0, [x19, #24]
    cmp x0, #30
    blt decidir_riego2

    ldr x0, [x19, #32]
    cmp x0, #300
    blt decidir_light

    mov x0, #0
    bl calcular_promedio
    cmp x0, #30
    bge decidir_fan

    ldr x0, [x19, #0]
    cmp x0, #30
    bge decidir_fan

    b decidir_green

decidir_alarm:
    ldr x21, =txt_alarm
    mov x22, #len_txt_alarm
    ldr x23, =txt_target_gas
    mov x24, #len_txt_target_gas
    ldr x25, =txt_risk_high
    mov x26, #len_txt_risk_high
    ldr x27, =txt_reason_gas
    mov x28, #len_txt_reason_gas
    ldr x0, [x19, #40]
    ldr x1, =txt_indicator_amp
    mov x2, #len_txt_indicator_amp
    b decidir_fin

decidir_riego1:
    ldr x21, =txt_riego1
    mov x22, #len_txt_riego1
    ldr x23, =txt_target_soil1
    mov x24, #len_txt_target_soil1
    ldr x25, =txt_risk_medium
    mov x26, #len_txt_risk_medium
    ldr x27, =txt_reason_soil1
    mov x28, #len_txt_reason_soil1
    ldr x0, [x19, #16]
    ldr x1, =txt_indicator_avg
    mov x2, #len_txt_indicator_avg
    b decidir_fin

decidir_riego2:
    ldr x21, =txt_riego2
    mov x22, #len_txt_riego2
    ldr x23, =txt_target_soil2
    mov x24, #len_txt_target_soil2
    ldr x25, =txt_risk_medium
    mov x26, #len_txt_risk_medium
    ldr x27, =txt_reason_soil2
    mov x28, #len_txt_reason_soil2
    ldr x0, [x19, #24]
    ldr x1, =txt_indicator_avg
    mov x2, #len_txt_indicator_avg
    b decidir_fin

decidir_light:
    ldr x21, =txt_light
    mov x22, #len_txt_light
    ldr x23, =txt_target_luz
    mov x24, #len_txt_target_luz
    ldr x25, =txt_risk_medium
    mov x26, #len_txt_risk_medium
    ldr x27, =txt_reason_luz
    mov x28, #len_txt_reason_luz
    ldr x0, [x19, #32]
    ldr x1, =txt_indicator_trend
    mov x2, #len_txt_indicator_trend
    b decidir_fin

decidir_fan:
    ldr x21, =txt_fan
    mov x22, #len_txt_fan
    ldr x23, =txt_target_temp
    mov x24, #len_txt_target_temp
    ldr x25, =txt_risk_medium
    mov x26, #len_txt_risk_medium
    ldr x27, =txt_reason_temp
    mov x28, #len_txt_reason_temp
    ldr x0, [x19, #0]
    ldr x1, =txt_indicator_avg
    mov x2, #len_txt_indicator_avg
    b decidir_fin

decidir_green:
    ldr x21, =txt_green
    mov x22, #len_txt_green
    ldr x23, =txt_target_system
    mov x24, #len_txt_target_system
    ldr x25, =txt_risk_normal
    mov x26, #len_txt_risk_normal
    ldr x27, =txt_reason_ok
    mov x28, #len_txt_reason_ok
    mov x0, #0
    ldr x1, =txt_indicator_avg
    mov x2, #len_txt_indicator_avg

decidir_fin:
    ldr x3, =decision_action_ptr
    str x21, [x3]
    ldr x3, =decision_action_len
    str x22, [x3]
    ldr x3, =decision_target_ptr
    str x23, [x3]
    ldr x3, =decision_target_len
    str x24, [x3]
    ldr x3, =decision_risk_ptr
    str x25, [x3]
    ldr x3, =decision_risk_len
    str x26, [x3]
    ldr x3, =decision_reason_ptr
    str x27, [x3]
    ldr x3, =decision_reason_len
    str x28, [x3]
    ldr x3, =decision_value
    str x0, [x3]
    ldr x3, =decision_indicator_ptr
    str x1, [x3]
    ldr x3, =decision_indicator_len
    str x2, [x3]

    ldp x29, x30, [sp], #16
    ret


// esto calcula promedio reciente de un sensor
calcular_promedio:
    ldr x1, =hist_count
    ldr x1, [x1]
    cbz x1, promedio_cero
    ldr x2, =histories
    mov x3, #0
    mov x4, #0
promedio_loop:
    cmp x4, x1
    bge promedio_divide
    mov x5, #6
    mul x6, x4, x5
    add x6, x6, x0
    ldr x7, [x2, x6, lsl #3]
    add x3, x3, x7
    add x4, x4, #1
    b promedio_loop
promedio_divide:
    sdiv x0, x3, x1
    ret
promedio_cero:
    mov x0, #0
    ret


// esto calcula amplitud reciente de un sensor
calcular_amplitud:
    ldr x1, =hist_count
    ldr x1, [x1]
    cbz x1, amplitud_cero
    ldr x2, =histories
    mov x3, #6
    mul x4, x0, xzr
    ldr x5, [x2, x0, lsl #3]
    mov x6, x5
    mov x7, #1
amplitud_loop:
    cmp x7, x1
    bge amplitud_fin
    mul x8, x7, x3
    add x8, x8, x0
    ldr x9, [x2, x8, lsl #3]
    cmp x9, x5
    bge amplitud_max_ok
    mov x5, x9
amplitud_max_ok:
    cmp x9, x6
    ble amplitud_min_ok
    mov x6, x9
amplitud_min_ok:
    add x7, x7, #1
    b amplitud_loop
amplitud_fin:
    sub x0, x6, x5
    ret
amplitud_cero:
    mov x0, #0
    ret


// esto emite una respuesta correcta
emitir_respuesta_ok:
    stp x29, x30, [sp, #-16]!
    mov x29, sp

    ldr x1, =msg_action
    mov x2, #len_msg_action
    bl escribir_salida_local
    ldr x0, =decision_action_ptr
    ldr x1, [x0]
    ldr x0, =decision_action_len
    ldr x2, [x0]
    bl escribir_salida_local
    bl escribir_nueva_linea

    ldr x1, =msg_target
    mov x2, #len_msg_target
    bl escribir_salida_local
    ldr x0, =decision_target_ptr
    ldr x1, [x0]
    ldr x0, =decision_target_len
    ldr x2, [x0]
    bl escribir_salida_local
    bl escribir_nueva_linea

    ldr x1, =msg_risk
    mov x2, #len_msg_risk
    bl escribir_salida_local
    ldr x0, =decision_risk_ptr
    ldr x1, [x0]
    ldr x0, =decision_risk_len
    ldr x2, [x0]
    bl escribir_salida_local
    bl escribir_nueva_linea

    ldr x1, =msg_reason
    mov x2, #len_msg_reason
    bl escribir_salida_local
    ldr x0, =decision_reason_ptr
    ldr x1, [x0]
    ldr x0, =decision_reason_len
    ldr x2, [x0]
    bl escribir_salida_local
    bl escribir_nueva_linea

    ldr x1, =msg_value
    mov x2, #len_msg_value
    bl escribir_salida_local
    ldr x0, =decision_value
    ldr x0, [x0]
    bl imprimir_entero
    bl escribir_nueva_linea

    ldr x1, =msg_indicator
    mov x2, #len_msg_indicator
    bl escribir_salida_local
    ldr x0, =decision_indicator_ptr
    ldr x1, [x0]
    ldr x0, =decision_indicator_len
    ldr x2, [x0]
    bl escribir_salida_local
    bl escribir_nueva_linea

    ldr x1, =msg_status_ok
    mov x2, #len_msg_status_ok
    bl escribir_salida_local

    ldp x29, x30, [sp], #16
    ret


// esto emite error de entrada
emitir_respuesta_error:
    stp x29, x30, [sp, #-16]!
    mov x29, sp

    ldr x1, =msg_status_error
    mov x2, #len_msg_status_error
    bl escribir_salida_local

    ldr x1, =msg_error_invalid
    mov x2, #len_msg_error_invalid
    bl escribir_salida_local

    ldr x1, =msg_detail_invalid
    mov x2, #len_msg_detail_invalid
    bl escribir_salida_local

    ldp x29, x30, [sp], #16
    ret


// esto escribe una cadena en stdout
escribir_salida_local:
    mov x0, #1
    mov x8, #64
    svc #0
    ret


// esto escribe salto de linea
escribir_nueva_linea:
    ldr x1, =newline
    mov x2, #1
    b escribir_salida_local


// esto imprime un entero con signo
imprimir_entero:
    stp x29, x30, [sp, #-16]!
    mov x29, sp
    mov x9, x0
    ldr x1, =num_buffer
    add x1, x1, #31
    mov x2, #0

    cmp x9, #0
    bge imprimir_entero_abs
    neg x9, x9
    mov x10, #1
    b imprimir_entero_convertir
imprimir_entero_abs:
    mov x10, #0

imprimir_entero_convertir:
    cmp x9, #0
    bne imprimir_entero_loop
    mov w3, #'0'
    strb w3, [x1], #-1
    mov x2, #1
    b imprimir_entero_signo

imprimir_entero_loop:
    mov x5, #10
    udiv x3, x9, x5
    msub x4, x3, x5, x9
    add w4, w4, #'0'
    strb w4, [x1], #-1
    add x2, x2, #1
    mov x9, x3
    cbnz x9, imprimir_entero_loop

imprimir_entero_signo:
    cbz x10, imprimir_entero_emitir
    mov w3, #'-'
    strb w3, [x1], #-1
    add x2, x2, #1

imprimir_entero_emitir:
    add x1, x1, #1
    bl escribir_salida_local
    ldp x29, x30, [sp], #16
    ret

.bss

decision_action_ptr:
    .skip 8
decision_action_len:
    .skip 8
decision_target_ptr:
    .skip 8
decision_target_len:
    .skip 8
decision_risk_ptr:
    .skip 8
decision_risk_len:
    .skip 8
decision_reason_ptr:
    .skip 8
decision_reason_len:
    .skip 8
decision_value:
    .skip 8
decision_indicator_ptr:
    .skip 8
decision_indicator_len:
    .skip 8
