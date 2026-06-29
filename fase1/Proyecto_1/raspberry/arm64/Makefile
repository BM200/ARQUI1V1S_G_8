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

COL ?= 2

all: $(BUILD)/$(MOD1) $(BUILD)/$(MOD2) $(BUILD)/$(MOD3) $(BUILD)/$(MOD4) $(BUILD)/$(MOD5)

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