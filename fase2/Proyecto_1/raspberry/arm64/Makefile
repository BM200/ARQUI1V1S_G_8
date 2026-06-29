AS      = aarch64-linux-gnu-as
LD      = aarch64-linux-gnu-ld
QEMU    = qemu-aarch64

BUILD   = build
RESULTS = resultados_arm64

UTILS   = utils.s
UTILSO  = $(BUILD)/utils.o

MOD1    = modulo_1_media
MOD2    = modulo_2_varianza
MOD3    = modulo_3_anomalias
MOD4    = modulo_4_prediccion
MOD5    = modulo_5_tendencia
HIST    = historical_analyzer
LIVE    = live_engine
RMSE    = modulo_rmse
REGRESION = modulo_2_regresion
PREDICCION = modulo_3_prediccion
INTEGRAL = modulo_4_integral_error
DERIVADA_LOCAL = modulo_5_derivada_local
TEST_UTILS_WINDOW = test_utils_window

COL ?= 2

.PHONY: live_engine run_live_engine rmse run_rmse regresion run_regresion prediccion run_prediccion integral_error run_integral_error derivada_local run_derivada_local test_utils_window

all: $(BUILD)/$(MOD1) $(BUILD)/$(MOD2) $(BUILD)/$(MOD3) $(BUILD)/$(MOD4) $(BUILD)/$(MOD5) $(BUILD)/$(HIST) $(BUILD)/$(RMSE) $(BUILD)/$(INTEGRAL) $(BUILD)/$(DERIVADA_LOCAL) $(BUILD)/$(REGRESION) $(BUILD)/$(PREDICCION)

$(BUILD):
	mkdir -p $(BUILD)

$(RESULTS):
	mkdir -p $(RESULTS)

$(UTILSO): $(UTILS) | $(BUILD)
	$(AS) -g $(UTILS) -o $(UTILSO)

$(BUILD)/$(MOD1).o: $(MOD1).s | $(BUILD)
	$(AS) -g $(MOD1).s -o $(BUILD)/$(MOD1).o

$(BUILD)/$(MOD2).o: $(MOD2).s | $(BUILD)
	$(AS) -g $(MOD2).s -o $(BUILD)/$(MOD2).o

$(BUILD)/$(MOD3).o: $(MOD3).s | $(BUILD)
	$(AS) -g $(MOD3).s -o $(BUILD)/$(MOD3).o

$(BUILD)/$(MOD4).o: $(MOD4).s | $(BUILD)
	$(AS) -g $(MOD4).s -o $(BUILD)/$(MOD4).o

$(BUILD)/$(MOD5).o: $(MOD5).s | $(BUILD)
	$(AS) -g $(MOD5).s -o $(BUILD)/$(MOD5).o

$(BUILD)/$(HIST).o: $(HIST).s | $(BUILD)
	$(AS) -g $(HIST).s -o $(BUILD)/$(HIST).o

$(BUILD)/$(LIVE).o: $(LIVE).s | $(BUILD)
	$(AS) -g $(LIVE).s -o $(BUILD)/$(LIVE).o

$(BUILD)/$(RMSE).o: $(RMSE).s | $(BUILD)
	$(AS) -g $(RMSE).s -o $(BUILD)/$(RMSE).o

$(BUILD)/$(REGRESION).o: $(REGRESION).s | $(BUILD)
	$(AS) -g $(REGRESION).s -o $(BUILD)/$(REGRESION).o

$(BUILD)/$(PREDICCION).o: $(PREDICCION).s | $(BUILD)
	$(AS) -g $(PREDICCION).s -o $(BUILD)/$(PREDICCION).o

$(BUILD)/$(INTEGRAL).o: $(INTEGRAL).s | $(BUILD)
	$(AS) -g $(INTEGRAL).s -o $(BUILD)/$(INTEGRAL).o

$(BUILD)/$(DERIVADA_LOCAL).o: $(DERIVADA_LOCAL).s | $(BUILD)
	$(AS) -g $(DERIVADA_LOCAL).s -o $(BUILD)/$(DERIVADA_LOCAL).o

$(BUILD)/$(TEST_UTILS_WINDOW).o: $(TEST_UTILS_WINDOW).s | $(BUILD)
	$(AS) -g $(TEST_UTILS_WINDOW).s -o $(BUILD)/$(TEST_UTILS_WINDOW).o

$(BUILD)/$(MOD1): $(BUILD)/$(MOD1).o $(UTILSO)
	$(LD) $(BUILD)/$(MOD1).o $(UTILSO) -o $(BUILD)/$(MOD1)

$(BUILD)/$(MOD2): $(BUILD)/$(MOD2).o $(UTILSO)
	$(LD) $(BUILD)/$(MOD2).o $(UTILSO) -o $(BUILD)/$(MOD2)

$(BUILD)/$(MOD3): $(BUILD)/$(MOD3).o $(UTILSO)
	$(LD) $(BUILD)/$(MOD3).o $(UTILSO) -o $(BUILD)/$(MOD3)

$(BUILD)/$(MOD4): $(BUILD)/$(MOD4).o $(UTILSO)
	$(LD) $(BUILD)/$(MOD4).o $(UTILSO) -o $(BUILD)/$(MOD4)

$(BUILD)/$(MOD5): $(BUILD)/$(MOD5).o $(UTILSO)
	$(LD) $(BUILD)/$(MOD5).o $(UTILSO) -o $(BUILD)/$(MOD5)

$(BUILD)/$(HIST): $(BUILD)/$(HIST).o
	$(LD) $(BUILD)/$(HIST).o -o $(BUILD)/$(HIST)

$(BUILD)/$(LIVE): $(BUILD)/$(LIVE).o $(UTILSO)
	$(LD) $(BUILD)/$(LIVE).o $(UTILSO) -o $(BUILD)/$(LIVE)

$(BUILD)/$(RMSE): $(BUILD)/$(RMSE).o $(UTILSO)
	$(LD) $(BUILD)/$(RMSE).o $(UTILSO) -o $(BUILD)/$(RMSE)

$(BUILD)/$(REGRESION): $(BUILD)/$(REGRESION).o $(UTILSO)
	$(LD) $(BUILD)/$(REGRESION).o $(UTILSO) -o $(BUILD)/$(REGRESION)

$(BUILD)/$(PREDICCION): $(BUILD)/$(PREDICCION).o $(UTILSO)
	$(LD) $(BUILD)/$(PREDICCION).o $(UTILSO) -o $(BUILD)/$(PREDICCION)

$(BUILD)/$(INTEGRAL): $(BUILD)/$(INTEGRAL).o $(UTILSO)
	$(LD) $(BUILD)/$(INTEGRAL).o $(UTILSO) -o $(BUILD)/$(INTEGRAL)

$(BUILD)/$(DERIVADA_LOCAL): $(BUILD)/$(DERIVADA_LOCAL).o $(UTILSO)
	$(LD) $(BUILD)/$(DERIVADA_LOCAL).o $(UTILSO) -o $(BUILD)/$(DERIVADA_LOCAL)

$(BUILD)/$(TEST_UTILS_WINDOW): $(BUILD)/$(TEST_UTILS_WINDOW).o $(UTILSO)
	$(LD) $(BUILD)/$(TEST_UTILS_WINDOW).o $(UTILSO) -o $(BUILD)/$(TEST_UTILS_WINDOW)

live_engine: $(BUILD)/$(LIVE)
	@echo "OK: build/live_engine generado"

rmse: $(BUILD)/$(RMSE)
	@echo "OK: build/modulo_rmse generado"

regresion: $(BUILD)/$(REGRESION)
	@echo "OK: build/modulo_2_regresion generado"

prediccion: $(BUILD)/$(PREDICCION)
	@echo "OK: build/modulo_3_prediccion generado"

integral_error: $(BUILD)/$(INTEGRAL)
	@echo "OK: build/modulo_4_integral_error generado"

derivada_local: $(BUILD)/$(DERIVADA_LOCAL)
	@echo "OK: build/modulo_5_derivada_local generado"

test_utils_window: $(BUILD)/$(TEST_UTILS_WINDOW)
	$(QEMU) $(BUILD)/$(TEST_UTILS_WINDOW)

run1: $(BUILD)/$(MOD1) | $(RESULTS)
	$(QEMU) $(BUILD)/$(MOD1) $(COL)

run2: $(BUILD)/$(MOD2) | $(RESULTS)
	$(QEMU) $(BUILD)/$(MOD2) $(COL)

run3: $(BUILD)/$(MOD3) | $(RESULTS)
	$(QEMU) $(BUILD)/$(MOD3) $(COL)

run4: $(BUILD)/$(MOD4) | $(RESULTS)
	$(QEMU) $(BUILD)/$(MOD4) $(COL)

run5: $(BUILD)/$(MOD5) | $(RESULTS)
	$(QEMU) $(BUILD)/$(MOD5) $(COL)

run_live_engine: $(BUILD)/$(LIVE)
	$(QEMU) $(BUILD)/$(LIVE)

run_rmse: $(BUILD)/$(RMSE)
	$(QEMU) $(BUILD)/$(RMSE) lecturas.csv 1 10 TEMP 25

run_regresion: $(BUILD)/$(REGRESION)
	$(QEMU) $(BUILD)/$(REGRESION) lecturas.csv 1 10 TEMP

run_prediccion: $(BUILD)/$(PREDICCION)
	$(QEMU) $(BUILD)/$(PREDICCION) lecturas.csv 1 10 TEMP 5

run_integral_error: $(BUILD)/$(INTEGRAL)
	$(QEMU) $(BUILD)/$(INTEGRAL) lecturas.csv 1 10 TEMP 25

run_derivada_local: $(BUILD)/$(DERIVADA_LOCAL)
	$(QEMU) $(BUILD)/$(DERIVADA_LOCAL) lecturas.csv 1 10 TEMP

save1: run1
save2: run2
save3: run3
save4: run4
save5: run5

# Debug con GDB. Abrir dos terminales:
# Terminal 1: make debug1 COL=7
# Terminal 2: make gdb1
debug1: $(BUILD)/$(MOD1) | $(RESULTS)
	$(QEMU) -g 1231 $(BUILD)/$(MOD1) $(COL)

debug2: $(BUILD)/$(MOD2) | $(RESULTS)
	$(QEMU) -g 1232 $(BUILD)/$(MOD2) $(COL)

debug3: $(BUILD)/$(MOD3) | $(RESULTS)
	$(QEMU) -g 1233 $(BUILD)/$(MOD3) $(COL)

debug4: $(BUILD)/$(MOD4) | $(RESULTS)
	$(QEMU) -g 1234 $(BUILD)/$(MOD4) $(COL)

debug5: $(BUILD)/$(MOD5) | $(RESULTS)
	$(QEMU) -g 1235 $(BUILD)/$(MOD5) $(COL)

gdb1:
	gdb-multiarch $(BUILD)/$(MOD1) -x debug_modulo1.gdb

gdb2:
	gdb-multiarch $(BUILD)/$(MOD2) -x debug_modulo2.gdb

gdb3:
	gdb-multiarch $(BUILD)/$(MOD3) -x debug_modulo3.gdb

gdb4:
	gdb-multiarch $(BUILD)/$(MOD4) -x debug_modulo4.gdb

gdb5:
	gdb-multiarch $(BUILD)/$(MOD5) -x debug_modulo5.gdb

clean:
	rm -rf $(BUILD)
