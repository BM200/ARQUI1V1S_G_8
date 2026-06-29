// ============================================================
// UTILS.S
// Biblioteca comun para todos los modulos ARM64.
// Contiene:
//   - read_csv_column: lee una columna numerica de lecturas.csv
//   - write_file: escribe un buffer en un archivo .txt
//   - uint_to_ascii: convierte entero sin signo a texto decimal
// ============================================================

.bss
.balign 8
csv_buffer:
        .skip 4096

.text

// ============================================================
// read_csv_column
// Entrada:
//   x0 = direccion del nombre del archivo CSV
//   x1 = numero de columna a leer, empezando en 1
//   x2 = arreglo destino donde se guardan los valores
//   x3 = cantidad maxima de datos a leer
// Salida:
//   x0 = cantidad de datos leidos
//        -1 si no pudo abrir el archivo
//        -2 si no pudo leer el archivo
// ============================================================
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

        mov x19, x0              // nombre del archivo
        mov x20, x1              // columna seleccionada
        mov x21, x2              // arreglo destino
        mov x22, x3              // maximo de valores

// =====================================
// ABRIR ARCHIVO CSV
// =====================================
        mov x0, #-100            // AT_FDCWD
        mov x1, x19              // filename
        mov x2, #0               // O_RDONLY
        mov x3, #0
        mov x8, #56              // syscall openat
        svc #0
        cmp x0, #0
        blt read_csv_open_error
        mov x23, x0              // fd

// =====================================
// LEER CONTENIDO DEL CSV AL BUFFER
// =====================================
        mov x0, x23
        ldr x1, =csv_buffer
        mov x2, #4095
        mov x8, #63              // syscall read
        svc #0
        cmp x0, #0
        blt read_csv_read_error
        mov x24, x0              // bytes leidos

// =====================================
// CERRAR ARCHIVO CSV
// =====================================
        mov x0, x23
        mov x8, #57              // syscall close
        svc #0

// =====================================
// AGREGAR TERMINADOR 0 AL BUFFER
// =====================================
        ldr x25, =csv_buffer
        add x26, x25, x24
        mov w9, #0
        strb w9, [x26]
        ldr x25, =csv_buffer

// =====================================
// SALTAR ENCABEZADO DEL CSV
// =====================================
skip_header_utils:
        cmp x25, x26
        bge read_csv_done_empty
        ldrb w9, [x25], #1
        cmp w9, #10              // '\n'
        beq start_csv_lines
        b skip_header_utils

start_csv_lines:
        mov x27, #0              // contador de valores leidos

// =====================================
// RECORRER CADA LINEA DEL CSV
// =====================================
csv_line_start:
        cmp x27, x22
        bge read_csv_done
        cmp x25, x26
        bge read_csv_done
        mov x28, #1              // columna actual

// =====================================
// SALTAR COLUMNAS HASTA LLEGAR A LA ELEGIDA
// =====================================
csv_skip_columns:
        cmp x28, x20
        beq csv_read_selected_column
        cmp x25, x26
        bge read_csv_done
        ldrb w9, [x25], #1
        cmp w9, #10              // salto de linea
        beq csv_line_start
        cmp w9, #44              // coma
        bne csv_skip_columns
        add x28, x28, #1
        b csv_skip_columns

// =====================================
// CONVERTIR COLUMNA ASCII A ENTERO
// =====================================
csv_read_selected_column:
        mov x9, #0               // valor acumulado
        mov x10, #0              // bandera: hubo digitos

csv_parse_number:
        cmp x25, x26
        bge csv_store_number
        ldrb w11, [x25], #1
        cmp w11, #44             // coma
        beq csv_store_number
        cmp w11, #10             // '\n'
        beq csv_store_number_newline
        cmp w11, #13             // '\r'
        beq csv_parse_number
        cmp w11, #48             // '0'
        blt csv_parse_number
        cmp w11, #57             // '9'
        bgt csv_parse_number

        mov x12, #10
        mul x9, x9, x12
        sub w11, w11, #48
        add x9, x9, x11
        mov x10, #1
        b csv_parse_number

// =====================================
// GUARDAR NUMERO LEIDO EN EL ARREGLO
// =====================================
csv_store_number:
        cbz x10, csv_skip_rest_line
        str x9, [x21, x27, lsl #3]
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
        str x9, [x21, x27, lsl #3]
        add x27, x27, #1
        b csv_line_start

read_csv_done_empty:
        mov x0, #0
        b read_csv_return

read_csv_done:
        mov x0, x27
        b read_csv_return

read_csv_open_error:
        mov x0, #-1
        b read_csv_return

read_csv_read_error:
        mov x0, #-2

read_csv_return:
        ldp x27, x28, [sp], #16
        ldp x25, x26, [sp], #16
        ldp x23, x24, [sp], #16
        ldp x21, x22, [sp], #16
        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret

// ============================================================
// write_file
// Entrada:
//   x0 = nombre del archivo destino
//   x1 = direccion del buffer a escribir
//   x2 = cantidad de bytes a escribir
// Salida:
//   x0 = bytes escritos o -1 si fallo al abrir
// ============================================================
.global write_file
.type write_file, %function
write_file:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!

        mov x19, x0
        mov x20, x1
        mov x21, x2

        mov x0, #-100
        mov x1, x19
        mov x2, #577             // O_WRONLY + O_CREAT + O_TRUNC
        mov x3, #420             // permisos 0644
        mov x8, #56              // openat
        svc #0
        cmp x0, #0
        blt write_file_open_error
        mov x22, x0

        mov x0, x22
        mov x1, x20
        mov x2, x21
        mov x8, #64              // write
        svc #0
        mov x23, x0

        mov x0, x22
        mov x8, #57              // close
        svc #0

        mov x0, x23
        b write_file_return

write_file_open_error:
        mov x0, #-1

write_file_return:
        ldp x21, x22, [sp], #16
        ldp x19, x20, [sp], #16
        ldp x29, x30, [sp], #16
        ret

// ============================================================
// uint_to_ascii
// Entrada:
//   x0 = numero entero sin signo
//   x1 = direccion del buffer temporal
// Salida:
//   x0 = direccion donde inicia el numero convertido
//   x1 = longitud del texto convertido
// ============================================================
.global uint_to_ascii
.type uint_to_ascii, %function
uint_to_ascii:
        stp x29, x30, [sp, #-16]!
        mov x29, sp
        stp x19, x20, [sp, #-16]!
        stp x21, x22, [sp, #-16]!

        mov x19, x0
        mov x20, x1
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