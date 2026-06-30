	.arch armv8-a
	.file	"historical_analyzer_gen.c"
	.text
	.align	2
	.p2align 4,,11
	.type	local_slope_x100, %function
local_slope_x100:
.LFB61:
	.cfi_startproc
	adrp	x2, values
	add	x2, x2, :lo12:values
	add	x0, x2, x0, lsl 3
	mov	x1, 0
	mov	x3, 0
	mov	x4, 0
	.p2align 3,,7
.L2:
	ldr	x2, [x0, x1, lsl 3]
	add	x4, x4, x2
	madd	x3, x2, x1, x3
	add	x1, x1, 1
	cmp	x1, 5
	bne	.L2
	neg	x0, x4, lsl 2
	add	x3, x3, x3, lsl 2
	sub	x0, x0, x4
	add	x0, x3, x0, lsl 1
	lsl	x0, x0, 1
	ret
	.cfi_endproc
.LFE61:
	.size	local_slope_x100, .-local_slope_x100
	.align	2
	.p2align 4,,11
	.type	parse_positive, %function
parse_positive:
.LFB55:
	.cfi_startproc
	sub	sp, sp, #48
	.cfi_def_cfa_offset 48
	adrp	x2, :got:__stack_chk_guard
	ldr	x2, [x2, :got_lo12:__stack_chk_guard]
	stp	x29, x30, [sp, 16]
	.cfi_offset 29, -32
	.cfi_offset 30, -24
	add	x29, sp, 16
	str	x19, [sp, 32]
	.cfi_offset 19, -16
	mov	x19, x1
	ldr	x1, [x2]
	str	x1, [sp, 8]
	mov	x1, 0
	str	xzr, [sp]
	cbz	x0, .L8
	ldrb	w1, [x0]
	cbnz	w1, .L14
.L8:
	mov	w0, 0
.L5:
	adrp	x1, :got:__stack_chk_guard
	ldr	x1, [x1, :got_lo12:__stack_chk_guard]
	ldr	x3, [sp, 8]
	ldr	x2, [x1]
	subs	x3, x3, x2
	mov	x2, 0
	bne	.L15
	ldp	x29, x30, [sp, 16]
	ldr	x19, [sp, 32]
	add	sp, sp, 48
	.cfi_remember_state
	.cfi_restore 29
	.cfi_restore 30
	.cfi_restore 19
	.cfi_def_cfa_offset 0
	ret
.L14:
	.cfi_restore_state
	mov	x1, sp
	mov	w2, 10
	bl	strtol
	mov	x1, x0
	ldr	x2, [sp]
	ldrb	w0, [x2]
	cmp	w0, 0
	ccmp	x1, 0, 4, eq
	ble	.L8
	mov	w0, 1
	str	x1, [x19]
	b	.L5
.L15:
	bl	__stack_chk_fail
	.cfi_endproc
.LFE55:
	.size	parse_positive, .-parse_positive
	.section	.rodata.str1.8,"aMS",@progbits,1
	.align	3
.LC0:
	.string	"STABLE"
	.align	3
.LC1:
	.string	"ASCENDING"
	.align	3
.LC2:
	.string	"DESCENDING"
	.align	3
.LC3:
	.string	"SOIL_TREND_BELOW_IDEAL"
	.align	3
.LC4:
	.string	"CHECK_IRRIGATION"
	.align	3
.LC5:
	.string	"TEMPERATURE_ASCENDING"
	.align	3
.LC6:
	.string	"CHECK_VENTILATION"
	.align	3
.LC7:
	.string	"WINDOW_STABLE"
	.align	3
.LC8:
	.string	"NO_ACTION"
	.align	3
.LC9:
	.string	"GAS_ASCENDING"
	.align	3
.LC10:
	.string	"CHECK_GAS_ALERT"
	.align	3
.LC11:
	.string	"EXPECTED_FILE_START_END_COLUMN_IDEAL_K"
	.align	3
.LC12:
	.string	"INVALID_ARGUMENTS"
	.align	3
.LC13:
	.string	"STATUS=ERROR\nERROR=%s\nDETAIL=%s\n"
	.align	3
.LC14:
	.string	"START_END_RANGE_INVALID"
	.align	3
.LC15:
	.string	"INVALID_RANGE"
	.align	3
.LC16:
	.string	"IDEAL_AND_K_MUST_BE_POSITIVE_INTEGERS"
	.align	3
.LC17:
	.string	"TEMP"
	.align	3
.LC18:
	.string	"HUM_AIRE"
	.align	3
.LC19:
	.string	"SOIL1"
	.align	3
.LC20:
	.string	"SOIL2"
	.align	3
.LC21:
	.string	"LUZ"
	.align	3
.LC22:
	.string	"GAS"
	.align	3
.LC23:
	.string	"UNKNOWN_SENSOR_COLUMN"
	.align	3
.LC24:
	.string	"INVALID_COLUMN"
	.align	3
.LC25:
	.string	"r"
	.align	3
.LC26:
	.string	"INPUT_FILE_COULD_NOT_BE_OPENED"
	.align	3
.LC27:
	.string	"FILE_NOT_FOUND"
	.align	3
.LC28:
	.string	"CSV_HEADER_NOT_FOUND"
	.align	3
.LC29:
	.string	"INVALID_FILE_FORMAT"
	.align	3
.LC30:
	.string	"TEMP,HUM_AIRE,SOIL1,SOIL2,LUZ,GAS"
	.align	3
.LC31:
	.string	"CSV_HEADER_INVALID"
	.align	3
.LC32:
	.string	"WINDOW_EXCEEDS_INTERNAL_BUFFER"
	.align	3
.LC33:
	.string	"RANGE_TOO_LARGE"
	.align	3
.LC34:
	.string	",\r\n"
	.align	3
.LC35:
	.string	"NON_NUMERIC_VALUE_IN_SELECTED_COLUMN"
	.align	3
.LC36:
	.string	"INVALID_VALUE"
	.align	3
.LC37:
	.string	"RANGE_OUTSIDE_FILE"
	.align	3
.LC38:
	.string	"LOCAL_DERIVATIVE_REQUIRES_AT_LEAST_5_VALUES"
	.align	3
.LC39:
	.string	"INSUFFICIENT_DATA"
	.align	3
.LC40:
	.string	"REGRESSION_DENOMINATOR_ZERO"
	.align	3
.LC41:
	.string	"INVALID_REGRESSION"
	.align	3
.LC42:
	.string	"WINDOW_START=%ld\n"
	.align	3
.LC43:
	.string	"WINDOW_END=%ld\n"
	.align	3
.LC44:
	.string	"COLUMN=%s\n"
	.align	3
.LC45:
	.string	"COUNT=%ld\n"
	.align	3
.LC46:
	.string	"IDEAL=%ld\n"
	.align	3
.LC47:
	.string	"RMSE=%ld\n"
	.align	3
.LC48:
	.string	"SLOPE_X100=%ld\n"
	.align	3
.LC49:
	.string	"TREND=%s\n"
	.align	3
.LC50:
	.string	"PREDICTED_%ld=%ld\n"
	.align	3
.LC51:
	.string	"ERROR_INTEGRAL=%ld\n"
	.align	3
.LC52:
	.string	"MAX_LOCAL_SLOPE_X100=%ld\n"
	.align	3
.LC53:
	.string	"MAX_ACCELERATION_X100=%ld\n"
	.align	3
.LC54:
	.string	"RECOMMENDATION=%s\n"
	.align	3
.LC55:
	.string	"REASON=%s\n"
	.align	3
.LC56:
	.string	"STATUS=OK"
	.align	3
.LC57:
	.string	"CALC=HISTORICAL_ANALYZER\n"
	.section	.text.startup,"ax",@progbits
	.align	2
	.p2align 4,,11
	.global	main
	.type	main, %function
main:
.LFB62:
	.cfi_startproc
	stp	x29, x30, [sp, -96]!
	.cfi_def_cfa_offset 96
	.cfi_offset 29, -96
	.cfi_offset 30, -88
	mov	x13, 4208
	mov	x29, sp
	stp	x19, x20, [sp, 16]
	stp	x21, x22, [sp, 32]
	sub	sp, sp, x13
	.cfi_def_cfa_offset 4304
	.cfi_offset 19, -80
	.cfi_offset 20, -72
	.cfi_offset 21, -64
	.cfi_offset 22, -56
	str	xzr, [sp, 1024]
	adrp	x2, :got:__stack_chk_guard
	ldr	x2, [x2, :got_lo12:__stack_chk_guard]
	mov	x19, x1
	ldr	x1, [x2]
	str	x1, [sp, 4200]
	mov	x1, 0
	cmp	w0, 7
	beq	.L17
	adrp	x3, .LC11
	adrp	x2, .LC12
	adrp	x1, .LC13
	add	x3, x3, :lo12:.LC11
	add	x2, x2, :lo12:.LC12
	add	x1, x1, :lo12:.LC13
	mov	w0, 2
	bl	__printf_chk
.L18:
	mov	w22, 1
.L16:
	adrp	x0, :got:__stack_chk_guard
	ldr	x0, [x0, :got_lo12:__stack_chk_guard]
	ldr	x2, [sp, 4200]
	ldr	x1, [x0]
	subs	x2, x2, x1
	mov	x1, 0
	bne	.L104
	mov	x13, 4208
	add	sp, sp, x13
	.cfi_remember_state
	.cfi_def_cfa_offset 96
	mov	w0, w22
	ldp	x19, x20, [sp, 16]
	ldp	x21, x22, [sp, 32]
	ldp	x29, x30, [sp], 96
	.cfi_restore 30
	.cfi_restore 29
	.cfi_restore 21
	.cfi_restore 22
	.cfi_restore 19
	.cfi_restore 20
	.cfi_def_cfa_offset 0
	ret
.L17:
	.cfi_restore_state
	ldp	x20, x0, [x19, 8]
	add	x1, sp, 56
	str	x27, [sp, 4288]
	.cfi_offset 27, -16
	ldr	x27, [x19, 32]
	str	x28, [sp, 4296]
	.cfi_offset 28, -8
	bl	parse_positive
	cbz	w0, .L21
	ldr	x0, [x19, 24]
	add	x1, sp, 64
	bl	parse_positive
	cbz	w0, .L21
	str	x25, [sp, 4272]
	.cfi_offset 25, -32
	str	x26, [sp, 4280]
	.cfi_offset 26, -24
	ldp	x25, x26, [sp, 56]
	cmp	x26, x25
	bge	.L105
	ldr	x25, [sp, 4272]
	.cfi_restore 25
	ldr	x26, [sp, 4280]
	.cfi_restore 26
.L21:
	adrp	x3, .LC14
	adrp	x2, .LC15
	add	x3, x3, :lo12:.LC14
	add	x2, x2, :lo12:.LC15
	adrp	x1, .LC13
	mov	w0, 2
	add	x1, x1, :lo12:.LC13
	bl	__printf_chk
	ldr	x27, [sp, 4288]
	.cfi_restore 27
	ldr	x28, [sp, 4296]
	.cfi_restore 28
	b	.L18
.L105:
	.cfi_offset 25, -32
	.cfi_offset 26, -24
	.cfi_offset 27, -16
	.cfi_offset 28, -8
	ldr	x0, [x19, 40]
	add	x1, sp, 72
	bl	parse_positive
	cbz	w0, .L23
	ldr	x0, [x19, 48]
	add	x1, sp, 80
	bl	parse_positive
	cbz	w0, .L23
	mov	x0, x27
	adrp	x1, .LC17
	add	x1, x1, :lo12:.LC17
	bl	strcmp
	mov	w19, w0
	cbz	w0, .L24
	adrp	x1, .LC18
	mov	x0, x27
	add	x1, x1, :lo12:.LC18
	bl	strcmp
	cbz	w0, .L62
	adrp	x1, .LC19
	mov	x0, x27
	add	x1, x1, :lo12:.LC19
	bl	strcmp
	cbz	w0, .L63
	adrp	x1, .LC20
	mov	x0, x27
	add	x1, x1, :lo12:.LC20
	bl	strcmp
	cbz	w0, .L64
	adrp	x1, .LC21
	mov	x0, x27
	add	x1, x1, :lo12:.LC21
	bl	strcmp
	cbz	w0, .L65
	mov	x0, x27
	adrp	x1, .LC22
	mov	w19, 5
	add	x1, x1, :lo12:.LC22
	bl	strcmp
	cbnz	w0, .L106
.L24:
	mov	x0, x20
	adrp	x1, .LC25
	add	x1, x1, :lo12:.LC25
	bl	fopen
	str	x0, [sp, 8]
	cbz	x0, .L107
	ldr	x2, [sp, 8]
	add	x0, sp, 104
	mov	w1, 4096
	str	x0, [sp]
	bl	fgets
	cbz	x0, .L108
	ldr	x0, [sp]
	adrp	x1, .LC30
	mov	x2, 33
	add	x1, x1, :lo12:.LC30
	bl	strncmp
	mov	w22, w0
	cbnz	w0, .L109
	adrp	x20, .LC34
	add	x21, sp, 88
	add	x20, x20, :lo12:.LC34
	add	x0, sp, 96
	str	x0, [sp, 40]
	str	x23, [sp, 4256]
	.cfi_offset 23, -48
	mov	x23, 0
	str	x24, [sp, 4264]
	.cfi_offset 24, -40
	mov	x24, 0
.L27:
	ldp	x0, x2, [sp]
	mov	w1, 4096
	bl	fgets
	cbz	x0, .L29
	add	x23, x23, 1
	cmp	x25, x23
	bgt	.L27
	cmp	x26, x23
	blt	.L29
	mov	x0, 8191
	cmp	x24, x0
	bgt	.L110
	ldr	x0, [sp]
	mov	x2, x21
	mov	x1, x20
	str	xzr, [sp, 88]
	bl	strtok_r
	cbz	x0, .L32
	cbz	w19, .L33
	mov	w28, 0
	b	.L34
	.p2align 2,,3
.L39:
	cmp	w28, w19
	beq	.L33
.L34:
	add	w28, w28, 1
	mov	x2, x21
	mov	x1, x20
	mov	x0, 0
	bl	strtok_r
	cbnz	x0, .L39
.L32:
	ldr	x0, [sp, 8]
	bl	fclose
	adrp	x3, .LC35
	adrp	x2, .LC36
	add	x3, x3, :lo12:.LC35
	add	x2, x2, :lo12:.LC36
.L101:
	adrp	x1, .LC13
	mov	w0, 2
	add	x1, x1, :lo12:.LC13
	bl	__printf_chk
	ldr	x23, [sp, 4256]
	.cfi_restore 23
	ldr	x24, [sp, 4264]
	.cfi_restore 24
	ldr	x25, [sp, 4272]
	.cfi_restore 25
	ldr	x26, [sp, 4280]
	.cfi_restore 26
	ldr	x27, [sp, 4288]
	.cfi_restore 27
	ldr	x28, [sp, 4296]
	.cfi_restore 28
	b	.L18
.L23:
	.cfi_offset 25, -32
	.cfi_offset 26, -24
	.cfi_offset 27, -16
	.cfi_offset 28, -8
	adrp	x3, .LC16
	adrp	x2, .LC12
	add	x3, x3, :lo12:.LC16
	add	x2, x2, :lo12:.LC12
.L102:
	adrp	x1, .LC13
	mov	w0, 2
	add	x1, x1, :lo12:.LC13
	bl	__printf_chk
	ldr	x25, [sp, 4272]
	.cfi_restore 25
	ldr	x26, [sp, 4280]
	.cfi_restore 26
	ldr	x27, [sp, 4288]
	.cfi_restore 27
	ldr	x28, [sp, 4296]
	.cfi_restore 28
	b	.L18
.L33:
	.cfi_offset 23, -48
	.cfi_offset 24, -40
	.cfi_offset 25, -32
	.cfi_offset 26, -24
	.cfi_offset 27, -16
	.cfi_offset 28, -8
	ldr	x1, [sp, 40]
	mov	w2, 10
	str	xzr, [sp, 96]
	bl	strtol
	mov	x4, x0
	ldr	x2, [sp, 96]
	str	x2, [sp, 24]
	ldrb	w1, [x2]
	str	w1, [sp, 16]
	cbz	w1, .L35
	str	x0, [sp, 32]
	bl	__ctype_b_loc
	ldp	x2, x4, [sp, 24]
	ldr	x3, [x0]
	ldr	w1, [sp, 16]
	add	x2, x2, 1
	b	.L36
	.p2align 2,,3
.L37:
	str	x2, [sp, 96]
	ldrb	w1, [x2], 1
	cbz	w1, .L35
.L36:
	ubfiz	x1, x1, 1, 8
	ldrh	w1, [x3, x1]
	tbnz	x1, 13, .L37
	b	.L32
.L35:
	adrp	x1, values
	add	x1, x1, :lo12:values
	str	x4, [x1, x24, lsl 3]
	add	x24, x24, 1
	b	.L27
.L29:
	ldr	x0, [sp, 8]
	bl	fclose
	cmp	x26, x25
	csel	x0, x26, x25, ge
	cmp	x24, 0
	ccmp	x23, x0, 1, gt
	bge	.L42
	adrp	x3, .LC37
	adrp	x2, .LC15
	add	x3, x3, :lo12:.LC37
	add	x2, x2, :lo12:.LC15
	b	.L101
.L106:
	.cfi_restore 23
	.cfi_restore 24
	adrp	x3, .LC23
	adrp	x2, .LC24
	add	x3, x3, :lo12:.LC23
	add	x2, x2, :lo12:.LC24
	b	.L102
.L62:
	mov	w19, 1
	b	.L24
.L109:
	ldr	x0, [sp, 8]
	bl	fclose
	adrp	x3, .LC31
	adrp	x2, .LC29
	add	x3, x3, :lo12:.LC31
	add	x2, x2, :lo12:.LC29
	b	.L102
.L42:
	.cfi_offset 23, -48
	.cfi_offset 24, -40
	cmp	x24, 4
	ble	.L111
	adrp	x0, values
	add	x9, x0, :lo12:values
	ldr	x20, [sp, 72]
	mov	x1, 1
	ldr	x8, [x0, #:lo12:values]
	mov	x21, 0
	mov	x7, 0
	mov	x5, 0
	sub	x0, x8, x20
	mov	x6, 0
	mul	x3, x0, x0
.L44:
	ldr	x2, [x9, 8]!
	cmp	x0, 0
	csneg	x10, x0, x0, ge
	madd	x5, x1, x1, x5
	subs	x0, x2, x20
	add	x6, x6, x1
	csneg	x4, x0, x0, pl
	madd	x7, x2, x1, x7
	add	x4, x4, x10
	add	x1, x1, 1
	madd	x3, x0, x0, x3
	add	x8, x8, x2
	add	x21, x21, x4, asr 1
	cmp	x24, x1
	bne	.L44
	mul	x1, x24, x5
	msub	x1, x6, x6, x1
	cbz	x1, .L112
	mul	x19, x24, x7
	mov	x2, 100
	msub	x19, x8, x6, x19
	mov	x23, 1073741824
	ldr	x0, [sp, 80]
	str	x0, [sp, 24]
	mul	x8, x8, x2
	mul	x19, x19, x2
	add	x5, x0, x24
	sdiv	x0, x3, x24
	sdiv	x3, x19, x1
	msub	x1, x3, x6, x8
	sdiv	x1, x1, x24
	madd	x1, x5, x3, x1
	sdiv	x1, x1, x2
	stp	x3, x1, [sp, 8]
	b	.L46
.L47:
	asr	x23, x23, 2
.L46:
	cmp	x0, x23
	blt	.L47
	mov	x28, 0
.L48:
	cbz	x23, .L113
	add	x1, x28, x23
	asr	x28, x28, 1
	cmp	x1, x0
	bgt	.L49
	sub	x0, x0, x1
	add	x28, x28, x23
.L49:
	asr	x23, x23, 2
	b	.L48
.L110:
	ldr	x0, [sp, 8]
	bl	fclose
	adrp	x3, .LC32
	adrp	x2, .LC33
	add	x3, x3, :lo12:.LC32
	add	x2, x2, :lo12:.LC33
	b	.L101
.L63:
	.cfi_restore 23
	.cfi_restore 24
	mov	w19, 2
	b	.L24
.L108:
	ldr	x0, [sp, 8]
	bl	fclose
	adrp	x3, .LC28
	adrp	x2, .LC29
	add	x3, x3, :lo12:.LC28
	add	x2, x2, :lo12:.LC29
	b	.L102
.L64:
	mov	w19, 3
	b	.L24
.L113:
	.cfi_offset 23, -48
	.cfi_offset 24, -40
	mov	x0, 0
	sub	x9, x24, #4
	bl	local_slope_x100
	mov	x6, 1
	mov	x19, x0
	mov	x7, x0
	b	.L51
.L53:
	mov	x0, x6
	bl	local_slope_x100
	subs	x1, x0, x7
	add	x6, x6, 1
	csneg	x1, x1, x1, pl
	cmp	x19, 0
	csneg	x8, x19, x19, ge
	cmp	x0, 0
	csneg	x2, x0, x0, ge
	mov	x7, x0
	cmp	x8, x2
	csel	x19, x19, x0, ge
	cmp	x23, x1
	csel	x23, x23, x1, ge
.L51:
	cmp	x9, x6
	bgt	.L53
	mov	x0, x27
	adrp	x1, .LC19
	add	x1, x1, :lo12:.LC19
	bl	strcmp
	ldr	x1, [sp, 8]
	cmp	x1, 0
	ble	.L114
	adrp	x1, .LC1
	add	x1, x1, :lo12:.LC1
	str	x1, [sp]
.L54:
	cbz	w0, .L56
	adrp	x1, .LC20
	mov	x0, x27
	add	x1, x1, :lo12:.LC20
	bl	strcmp
	cbz	w0, .L56
.L57:
	adrp	x0, .LC17
	add	x1, x0, :lo12:.LC17
	mov	x0, x27
	bl	strcmp
	ldr	x2, [sp]
	adrp	x1, .LC1
	add	x1, x1, :lo12:.LC1
	cmp	x2, x1
	cset	w2, eq
	str	w2, [sp, 32]
	cmp	w0, 0
	ccmp	w2, 0, 4, eq
	bne	.L71
	mov	x0, x27
	adrp	x1, .LC22
	add	x1, x1, :lo12:.LC22
	bl	strcmp
	ldr	w2, [sp, 32]
	cmp	w0, 0
	ccmp	w2, 0, 4, eq
	bne	.L72
.L59:
	adrp	x1, .LC57
	mov	w0, 2
	add	x1, x1, :lo12:.LC57
	bl	__printf_chk
	adrp	x6, .LC7
	adrp	x7, .LC8
	add	x6, x6, :lo12:.LC7
	add	x7, x7, :lo12:.LC8
.L58:
	mov	x2, x25
	adrp	x1, .LC42
	mov	w0, 2
	add	x1, x1, :lo12:.LC42
	stp	x7, x6, [sp, 32]
	bl	__printf_chk
	mov	x2, x26
	adrp	x1, .LC43
	mov	w0, 2
	add	x1, x1, :lo12:.LC43
	bl	__printf_chk
	mov	x2, x27
	adrp	x1, .LC44
	mov	w0, 2
	add	x1, x1, :lo12:.LC44
	bl	__printf_chk
	mov	x2, x24
	adrp	x1, .LC45
	mov	w0, 2
	add	x1, x1, :lo12:.LC45
	bl	__printf_chk
	mov	x2, x20
	adrp	x1, .LC46
	mov	w0, 2
	add	x1, x1, :lo12:.LC46
	bl	__printf_chk
	mov	x2, x28
	adrp	x1, .LC47
	mov	w0, 2
	add	x1, x1, :lo12:.LC47
	bl	__printf_chk
	ldr	x2, [sp, 8]
	adrp	x1, .LC48
	mov	w0, 2
	add	x1, x1, :lo12:.LC48
	bl	__printf_chk
	ldr	x2, [sp]
	adrp	x1, .LC49
	mov	w0, 2
	add	x1, x1, :lo12:.LC49
	bl	__printf_chk
	ldp	x3, x2, [sp, 16]
	adrp	x1, .LC50
	mov	w0, 2
	add	x1, x1, :lo12:.LC50
	bl	__printf_chk
	mov	x2, x21
	adrp	x1, .LC51
	mov	w0, 2
	add	x1, x1, :lo12:.LC51
	bl	__printf_chk
	mov	x2, x19
	adrp	x1, .LC52
	mov	w0, 2
	add	x1, x1, :lo12:.LC52
	bl	__printf_chk
	mov	x2, x23
	adrp	x1, .LC53
	mov	w0, 2
	add	x1, x1, :lo12:.LC53
	bl	__printf_chk
	ldr	x7, [sp, 32]
	adrp	x1, .LC54
	mov	w0, 2
	add	x1, x1, :lo12:.LC54
	mov	x2, x7
	bl	__printf_chk
	ldr	x6, [sp, 40]
	adrp	x1, .LC55
	add	x1, x1, :lo12:.LC55
	mov	w0, 2
	mov	x2, x6
	bl	__printf_chk
	adrp	x0, .LC56
	add	x0, x0, :lo12:.LC56
	bl	puts
	ldr	x23, [sp, 4256]
	.cfi_restore 23
	ldr	x24, [sp, 4264]
	.cfi_restore 24
	ldr	x25, [sp, 4272]
	.cfi_restore 25
	ldr	x26, [sp, 4280]
	.cfi_restore 26
	ldr	x27, [sp, 4288]
	.cfi_restore 27
	ldr	x28, [sp, 4296]
	.cfi_restore 28
	b	.L16
.L65:
	.cfi_offset 25, -32
	.cfi_offset 26, -24
	.cfi_offset 27, -16
	.cfi_offset 28, -8
	mov	w19, 4
	b	.L24
.L56:
	.cfi_offset 23, -48
	.cfi_offset 24, -40
	ldr	x1, [sp]
	adrp	x0, .LC2
	add	x0, x0, :lo12:.LC2
	cmp	x1, x0
	ldr	x0, [sp, 16]
	ccmp	x20, x0, 0, ne
	ble	.L59
	adrp	x6, .LC3
	adrp	x7, .LC4
	add	x6, x6, :lo12:.LC3
	add	x7, x7, :lo12:.LC4
	b	.L58
.L112:
	adrp	x3, .LC40
	adrp	x2, .LC41
	add	x3, x3, :lo12:.LC40
	add	x2, x2, :lo12:.LC41
	b	.L101
.L114:
	bne	.L55
	adrp	x1, .LC0
	add	x1, x1, :lo12:.LC0
	str	x1, [sp]
	b	.L54
.L111:
	adrp	x3, .LC38
	adrp	x2, .LC39
	add	x3, x3, :lo12:.LC38
	add	x2, x2, :lo12:.LC39
	b	.L101
.L55:
	cbz	w0, .L74
	adrp	x1, .LC20
	mov	x0, x27
	add	x1, x1, :lo12:.LC20
	bl	strcmp
	cbz	w0, .L74
	adrp	x0, .LC2
	add	x0, x0, :lo12:.LC2
	str	x0, [sp]
	b	.L57
.L104:
	.cfi_restore 23
	.cfi_restore 24
	.cfi_restore 25
	.cfi_restore 26
	.cfi_restore 27
	.cfi_restore 28
	str	x23, [sp, 4256]
	.cfi_offset 23, -48
	str	x24, [sp, 4264]
	.cfi_offset 24, -40
	str	x25, [sp, 4272]
	.cfi_offset 25, -32
	str	x26, [sp, 4280]
	.cfi_offset 26, -24
	str	x27, [sp, 4288]
	.cfi_offset 27, -16
	str	x28, [sp, 4296]
	.cfi_offset 28, -8
	bl	__stack_chk_fail
.L74:
	adrp	x0, .LC2
	adrp	x6, .LC3
	add	x0, x0, :lo12:.LC2
	adrp	x7, .LC4
	add	x6, x6, :lo12:.LC3
	add	x7, x7, :lo12:.LC4
	str	x0, [sp]
	b	.L58
.L71:
	adrp	x6, .LC5
	adrp	x7, .LC6
	add	x6, x6, :lo12:.LC5
	add	x7, x7, :lo12:.LC6
	b	.L58
.L72:
	adrp	x6, .LC9
	adrp	x7, .LC10
	add	x6, x6, :lo12:.LC9
	add	x7, x7, :lo12:.LC10
	b	.L58
.L107:
	.cfi_restore 23
	.cfi_restore 24
	adrp	x3, .LC26
	adrp	x2, .LC27
	add	x3, x3, :lo12:.LC26
	add	x2, x2, :lo12:.LC27
	b	.L102
	.cfi_endproc
.LFE62:
	.size	main, .-main
	.bss
	.align	4
	.type	values, %object
	.size	values, 65536
values:
	.zero	65536
	.section	.note.GNU-stack,"",@progbits
