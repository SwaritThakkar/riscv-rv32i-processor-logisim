# Demo Programs

This folder documents the program preloaded into the `Instruction_Memory` ROM of
`RV32I_CPU.circ`, and how to write your own.

## Bundled demo: `demo.asm`

```asm
# A tiny RV32I program that exercises the addi datapath and a negative immediate.
addi x1, x0, 5      # x1 = 5
addi x2, x1, 7      # x2 = x1 + 7 = 12
addi x3, x2, -2     # x3 = x2 - 2 = 10   (tests sign-extended negative immediate)
jal  x0, 0          # infinite loop -> acts as a halt
```

### Machine code (what is stored in the ROM)

| Address | Hex (instruction) | Assembly |
|--------:|-------------------|----------|
| `0x00` | `0x00500093` | `addi x1, x0, 5` |
| `0x04` | `0x00708113` | `addi x2, x1, 7` |
| `0x08` | `0xffe10193` | `addi x3, x2, -2` |
| `0x0c` | `0x0000006f` | `jal x0, 0` |

In Logisim-Evolution ROM "v2.0 raw" / hex format this is simply:

```
00500093 00708113 ffe10193 0000006f
```

### Expected result

After 3 clock ticks (the fourth instruction loops on itself):

| Register | Value |
|----------|------:|
| `x1` | `5` |
| `x2` | `12` |
| `x3` | `10` |

`x0` stays `0` throughout (it is hard-wired).

## Loading a program into the CPU

1. Open `RV32I_CPU.circ` and select the `Instruction_Memory` subcircuit.
2. Right-click the ROM component → **Edit Contents…**.
3. Paste your space-separated 32-bit hex words (one instruction per word).
4. Return to the `CPU` circuit, **Reset Simulation**, and tick the clock.

## Writing your own

Assemble RV32I by hand, or use any RISC-V toolchain and extract the `.text` section as hex:

```bash
# Example with the GNU toolchain
riscv64-unknown-elf-as -march=rv32i -o demo.o demo.asm
riscv64-unknown-elf-objcopy -O binary demo.o demo.bin
xxd -e -c4 demo.bin | awk '{print $2}'   # -> hex words for the ROM
```

Stick to the RV32I base set (no `ecall`/`ebreak`), keep instructions word-aligned, and
remember that branch/jump offsets are PC-relative.
