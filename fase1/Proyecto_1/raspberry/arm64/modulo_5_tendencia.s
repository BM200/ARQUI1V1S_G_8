// ============================================================
// MODULO 5: TENDENCIA ACUMULADA AVANZADA
// Recibe la columna desde argumento y procesa 30 datos de lecturas.csv.
// Salida: resultados_arm64/resultado_tendencia.txt
// ============================================================

        .equ N_VALUES, 30
        .equ DEFAULT_COLUMN, 2

        .data
csv_file:
        .asciz "lecturas.csv"
txt_file:
        .asciz "resultados_arm64/resultado_tendencia.txt"
msg_nl:
        .asciz "\n"
msg_error_archivo:
        .asciz "ERROR: no se pudo abrir o leer lecturas.csv\n"
msg_error_datos:
        .asciz "ERROR: no se pudieron leer 30 datos\n"

msg_module:
        .asciz "MODULE=ADVANCED_TREND\n"
msg_total:
        .asciz "TOTAL_VALUES="
msg_inc:
        .asciz "INCREMENTS="
msg_dec:
        .asciz "DECREMENTS="
msg_max_up:
        .asciz "MAX_UP_STREAK="
msg_max_down:
        .asciz "MAX_DOWN_STREAK="
msg_accum:
        .asciz "ACCUM_DIFF="
msg_trend:
        .asciz "TREND="
msg_up:
        .asciz "UP\n"
msg_down:
        .asciz "DOWN\n"
msg_stable:
        .asciz "STABLE\n"

        .bss
        .align 3
values:
        .skip N_VALUES * 8
outbuf:
        .skip 768
tmpnum:
        .skip 32
inc_mem:
        .skip 8
dec_mem:
        .skip 8
max_up_mem:
        .skip 8
max_down_mem:
        .skip 8
accum_mem:
        .skip 8

        .text
        .extern read_csv_column
        .extern write_file
        .global _start

_start:
// =====================================
// OBTENER COLUMNA SELECCIONADA
// =====================================
        mov x0, sp
        bl obtener_columna
        mov x19, x0

// =====================================
// LEER CSV USANDO UTILS.S
// =====================================
        ldr x0, =csv_file
        mov x1, x19
        ldr x2, =values
        mov x3, #N_VALUES
        bl read_csv_column
        cmp x0, #0
        blt error_archivo
        cmp x0, #N_VALUES
        bne error_datos
        mov x20, x0

// =====================================
// INICIALIZAR VARIABLES DE TENDENCIA
// Se comparan pares consecutivos: X_i - X_(i-1)
// Con 30 datos existen 29 diferencias.
// =====================================
        ldr x21, =values
        ldr x22, [x21], #8           // x22 = valor anterior = X_1
        mov x23, #0                  // INCREMENTS
        mov x24, #0                  // DECREMENTS
        mov x25, #0                  // racha actual de subida
        mov x26, #0                  // racha actual de bajada
        mov x27, #0                  // MAX_UP_STREAK
        mov x28, #0                  // MAX_DOWN_STREAK
        mov x9, #0                   // ACCUM_DIFF
        mov x10, #1                  // contador, ya se tomo el primer dato

// =====================================
// CICLO PRINCIPAL: CALCULAR DIFERENCIAS CONSECUTIVAS
// DIF_i = X_i - X_(i-1)
// =====================================
ciclo_tendencia:
        cmp x10, x20
        b.ge fin_tendencia

        ldr x11, [x21], #8           // x11 = valor actual
        sub x12, x11, x22            // x12 = diferencia actual
        add x9, x9, x12              // ACCUM_DIFF += diferencia

        cmp x12, #0
        b.gt tendencia_incremento
        b.lt tendencia_decremento

// =====================================
// CASO ESTABLE: DIF = 0
// Se reinician las rachas actuales.
// =====================================
tendencia_estable:
        mov x25, #0                  // racha subida = 0
        mov x26, #0                  // racha bajada = 0
        b avanzar_tendencia

// =====================================
// CASO INCREMENTO: DIF > 0
// =====================================
tendencia_incremento:
        add x23, x23, #1             // INCREMENTS++
        add x25, x25, #1             // racha actual de subida++
        mov x26, #0                  // se rompe racha de bajada
        cmp x25, x27
        b.le avanzar_tendencia
        mov x27, x25                 // actualizar MAX_UP_STREAK
        b avanzar_tendencia

// =====================================
// CASO DECREMENTO: DIF < 0
// =====================================
tendencia_decremento:
        add x24, x24, #1             // DECREMENTS++
        add x26, x26, #1             // racha actual de bajada++
        mov x25, #0                  // se rompe racha de subida
        cmp x26, x28
        b.le avanzar_tendencia
        mov x28, x26                 // actualizar MAX_DOWN_STREAK

avanzar_tendencia:
        mov x22, x11                 // valor anterior = valor actual
        add x10, x10, #1             // avanzar contador
        b ciclo_tendencia

// =====================================
// GUARDAR RESULTADOS EN MEMORIA
// =====================================
fin_tendencia:
        ldr x11, =inc_mem
        str x23, [x11]
        ldr x11, =dec_mem
        str x24, [x11]
        ldr x11, =max_up_mem
        str x27, [x11]
        ldr x11, =max_down_mem
        str x28, [x11]
        ldr x11, =accum_mem
        str x9, [x11]

// =====================================
// CONSTRUIR FORMATO DE SALIDA DEL ENUNCIADO
// =====================================
        ldr x27, =outbuf
        ldr x1, =msg_module
        mov x0, x27
        bl append_cstr
        mov x27, x0

        ldr x1, =msg_total
        mov x0, x27
        bl append_cstr
        mov x27, x0
        mov x1, #N_VALUES
        mov x0, x27
        bl append_uint
        mov x27, x0
        ldr x1, =msg_nl
        mov x0, x27
        bl append_cstr
        mov x27, x0

        ldr x1, =msg_inc
        mov x0, x27
        bl append_cstr
        mov x27, x0
        ldr x11, =inc_mem
        ldr x1, [x11]
        mov x0, x27
        bl append_uint
        mov x27, x0
        ldr x1, =msg_nl
        mov x0, x27
        bl append_cstr
        mov x27, x0

        ldr x1, =msg_dec
        mov x0, x27
        bl append_cstr
        mov x27, x0
        ldr x11, =dec_mem
        ldr x1, [x11]
        mov x0, x27
        bl append_uint
        mov x27, x0
        ldr x1, =msg_nl
        mov x0, x27
        bl append_cstr
        mov x27, x0

        ldr x1, =msg_max_up
        mov x0, x27
        bl append_cstr
        mov x27, x0
        ldr x11, =max_up_mem
        ldr x1, [x11]
        mov x0, x27
        bl append_uint
        mov x27, x0
        ldr x1, =msg_nl
        mov x0, x27
        bl append_cstr
        mov x27, x0

        ldr x1, =msg_max_down
        mov x0, x27
        bl append_cstr
        mov x27, x0
        ldr x11, =max_down_mem
        ldr x1, [x11]
        mov x0, x27
        bl append_uint
        mov x27, x0
        ldr x1, =msg_nl
        mov x0, x27
        bl append_cstr
        mov x27, x0

        ldr x1, =msg_accum
        mov x0, x27
        bl append_cstr
        mov x27, x0
        ldr x11, =accum_mem
        ldr x1, [x11]
        mov x0, x27
        bl append_sint
        mov x27, x0
        ldr x1, =msg_nl
        mov x0, x27
        bl append_cstr
        mov x27, x0

        ldr x1, =msg_trend
        mov x0, x27
        bl append_cstr
        mov x27, x0

// =====================================
// CLASIFICAR TENDENCIA FINAL
// ACCUM_DIFF > 0 = UP
// ACCUM_DIFF < 0 = DOWN
// ACCUM_DIFF = 0 = STABLE
// =====================================
        ldr x11, =accum_mem
        ldr x9, [x11]
        cmp x9, #0
        b.gt tendencia_final_up
        b.lt tendencia_final_down
        ldr x1, =msg_stable
        b agregar_tendencia_final

tendencia_final_up:
        ldr x1, =msg_up
        b agregar_tendencia_final

tendencia_final_down:
        ldr x1, =msg_down

agregar_tendencia_final:
        mov x0, x27
        bl append_cstr
        mov x27, x0
        bl imprimir_y_guardar
        b salir_ok

error_archivo:
        ldr x27, =outbuf
        ldr x1, =msg_error_archivo
        mov x0, x27
        bl append_cstr
        mov x27, x0
        bl imprimir_y_guardar
        b salir_error

error_datos:
        ldr x27, =outbuf
        ldr x1, =msg_error_datos
        mov x0, x27
        bl append_cstr
        mov x27, x0
        bl imprimir_y_guardar
        b salir_error

salir_ok:
        mov x0, #0
        mov x8, #93
        svc #0
salir_error:
        mov x0, #1
        mov x8, #93
        svc #0


// =====================================
// SUBRUTINA: OBTENER COLUMNA DESDE ARGUMENTO
// Entrada: x0 = SP original del proceso Linux
// Salida:  x0 = columna seleccionada
// Uso: qemu-aarch64 build/modulo_X N
// Columnas recomendadas:
// 2=TEMP, 3=HUM_AIRE, 4=HUM_SUELO_1, 5=HUM_SUELO_2, 6=LUZ, 7=GAS
// Si no se envia argumento o es invalido, usa DEFAULT_COLUMN.
// =====================================
obtener_columna:
        ldr x1, [x0]                 // x1 = argc, cantidad de argumentos
        cmp x1, #2                   // si argc < 2, no enviaron columna
        b.lt columna_default

        ldr x2, [x0, #16]            // x2 = argv[1], texto con la columna
        mov x3, #0                   // x3 = valor acumulado de la columna

parsear_columna:
        ldrb w4, [x2], #1            // leer un caracter del argumento
        cbz w4, validar_columna      // si es \0, termino el texto

        cmp w4, #48                  // verificar que sea >= '0'
        b.lt validar_columna
        cmp w4, #57                  // verificar que sea <= '9'
        b.gt validar_columna

        mov x5, #10                  // multiplicador decimal
        mul x3, x3, x5              // valor = valor * 10
        sub w4, w4, #48              // caracter ASCII -> digito
        add x3, x3, x4              // valor += digito
        b parsear_columna

validar_columna:
        cmp x3, #2                   // evitar ID; usar sensores desde columna 2
        b.lt columna_default
        cmp x3, #9                   // maximo permitido en el CSV
        b.gt columna_default
        mov x0, x3                   // retornar columna valida
        ret

columna_default:
        mov x0, #DEFAULT_COLUMN
        ret

// =====================================
// SUBRUTINA: APPEND_CSTR
// Copia una cadena terminada en cero al buffer de salida.
// Entrada: x0 = destino, x1 = cadena origen
// Salida:  x0 = nueva posicion final del buffer
// =====================================
append_cstr:
append_cstr_loop:
        ldrb w2, [x1], #1            // leer caracter de la cadena
        cbz w2, append_cstr_fin      // si es 0, termino la cadena
        strb w2, [x0], #1            // copiar caracter al buffer
        b append_cstr_loop
append_cstr_fin:
        ret

// =====================================
// SUBRUTINA: APPEND_UINT
// Convierte un entero sin signo a ASCII y lo agrega al buffer.
// Entrada: x0 = destino, x1 = numero
// Salida:  x0 = nueva posicion final del buffer
// =====================================
append_uint:
        mov x9, x0                   // x9 = puntero destino
        mov x10, x1                  // x10 = numero a convertir
        ldr x11, =tmpnum             // x11 = buffer temporal
        add x11, x11, #31            // apuntar al final del buffer
        mov x12, #0                  // x12 = contador de digitos
        mov x13, #10                 // base decimal

        cmp x10, #0                  // caso especial: numero cero
        b.ne append_uint_convertir
        mov w14, #48                 // '0'
        sub x11, x11, #1
        strb w14, [x11]
        mov x12, #1
        b append_uint_copiar

append_uint_convertir:
        udiv x14, x10, x13           // x14 = cociente
        msub x15, x14, x13, x10      // x15 = residuo
        add x15, x15, #48            // residuo -> ASCII
        sub x11, x11, #1             // retroceder en buffer temporal
        strb w15, [x11]              // guardar digito
        add x12, x12, #1             // aumentar longitud
        mov x10, x14                 // numero = cociente
        cmp x10, #0
        b.ne append_uint_convertir

append_uint_copiar:
        cbz x12, append_uint_fin
        ldrb w14, [x11], #1          // leer digito convertido
        strb w14, [x9], #1           // copiarlo al buffer final
        subs x12, x12, #1
        b.ne append_uint_copiar

append_uint_fin:
        mov x0, x9                   // retornar nuevo puntero final
        ret

// =====================================
// SUBRUTINA: APPEND_SINT
// Imprime entero con signo.
// Entrada: x0 = destino, x1 = numero con signo
// Salida:  x0 = nueva posicion final del buffer
// =====================================
append_sint:
        // Esta subrutina llama a append_uint con BL.
        // Por eso se guarda x30; si no, RET regresaria a esta misma subrutina.
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!

        mov x19, x0                  // x19 = destino actual del buffer
        mov x20, x1                  // x20 = numero con signo
        cmp x20, #0
        b.ge append_sint_positivo

        mov w11, #45                 // '-'
        strb w11, [x19], #1          // escribir signo negativo
        neg x20, x20                 // convertir a positivo

append_sint_positivo:
        mov x0, x19                  // destino actualizado
        mov x1, x20                  // numero positivo
        bl append_uint

        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret

// =====================================
// SUBRUTINA: APPEND_FIXED2
// Imprime un entero escalado por 100 con dos decimales.
// Ejemplo: 9931 -> 99.31, -25 -> -0.25
// Entrada: x0 = destino, x1 = numero escalado por 100
// Salida:  x0 = nueva posicion final del buffer
// =====================================
append_fixed2:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!

        mov x19, x0                  // x19 = destino
        mov x20, x1                  // x20 = valor escalado

        cmp x20, #0
        b.ge fixed2_positivo
        mov w9, #45                  // '-'
        strb w9, [x19], #1
        neg x20, x20

fixed2_positivo:
        mov x21, #100
        udiv x22, x20, x21           // parte entera
        msub x10, x22, x21, x20      // parte decimal
        str x10, [sp, #-16]!         // guardar decimal porque append_uint usa temporales

        mov x0, x19
        mov x1, x22
        bl append_uint               // escribir parte entera
        mov x19, x0

        mov w9, #46                  // '.'
        strb w9, [x19], #1

        ldr x10, [sp], #16           // recuperar decimal
        cmp x10, #10
        b.ge fixed2_dos_digitos
        mov w9, #48                  // agregar 0 si decimal < 10
        strb w9, [x19], #1

fixed2_dos_digitos:
        mov x0, x19
        mov x1, x10
        bl append_uint               // escribir decimales
        mov x19, x0

        mov x0, x19
        ldp x21, x22, [sp], #16
        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret

// =====================================
// SUBRUTINA: INT_SQRT_U64
// Calcula raiz cuadrada entera por busqueda binaria.
// Entrada: x0 = numero
// Salida:  x0 = floor(sqrt(numero))
// =====================================
int_sqrt_u64:
        cmp x0, #1
        b.ls sqrt_pequeno
        mov x1, #1                   // limite inferior
        lsr x2, x0, #1               // limite superior aproximado = n/2
        add x2, x2, #1

sqrt_loop:
        cmp x1, x2
        b.hi sqrt_fin
        add x3, x1, x2
        lsr x3, x3, #1               // x3 = punto medio
        mul x4, x3, x3               // x4 = mid^2
        cmp x4, x0
        b.ls sqrt_subir
        sub x2, x3, #1               // si mid^2 > n, bajar limite superior
        b sqrt_loop

sqrt_subir:
        add x1, x3, #1               // si mid^2 <= n, subir limite inferior
        b sqrt_loop

sqrt_fin:
        sub x0, x1, #1               // respuesta = limite inferior - 1
        ret

sqrt_pequeno:
        ret

// =====================================
// SUBRUTINA: IMPRIMIR_Y_GUARDAR
// Imprime outbuf en terminal y tambien lo guarda en txt_file.
// Entrada: x27 = puntero al final del texto construido
// =====================================
imprimir_y_guardar:
        // Esta subrutina llama a write_file con BL.
        // Se guarda x30 para poder regresar correctamente al punto donde fue llamada.
        stp x29, x30, [sp, #-16]!
        mov x29, sp

        mov w1, #0
        strb w1, [x27]               // terminar buffer con 0

        mov x0, #1                   // stdout
        ldr x1, =outbuf              // inicio del texto
        sub x2, x27, x1              // longitud = final - inicio
        mov x8, #64                  // syscall write
        svc #0

        ldr x0, =txt_file            // archivo destino
        ldr x1, =outbuf              // contenido a guardar
        sub x2, x27, x1              // longitud
        bl write_file

        ldp x29, x30, [sp], #16
        ret