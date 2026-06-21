<div align="center">

# 🖥️ RV32I CPU in Logisim-Evolution

### A complete single-cycle RISC-V (RV32I) microprocessor, built gate-by-gate

[![ISA](https://img.shields.io/badge/ISA-RISC--V%20RV32I-blue?style=for-the-badge&logo=riscv)](https://riscv.org/)
[![Tool](https://img.shields.io/badge/Logisim--Evolution-4.1.0-8957e5?style=for-the-badge)](https://github.com/logisim-evolution/logisim-evolution)
[![Type](https://img.shields.io/badge/Microarchitecture-Single--Cycle-bb8009?style=for-the-badge)]()
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

*Course Project 2 · DAC-102 / DAE-101 (2026)*
*Mehta Family School of Data Science & Artificial Intelligence, IIT Roorkee*

<br/>

![Architecture](docs/images/architecture.svg)

</div>

---

## 🎯 Overview

This repository contains a fully working implementation of a **RISC-V `RV32I` base-integer
microprocessor** designed in [Logisim-Evolution](https://github.com/logisim-evolution/logisim-evolution).
It executes the complete RV32I instruction set — every R, I, S, B, U and J-format
instruction — **except `ecall` and `ebreak`**, exactly as required by the assignment.

The processor is a **single-cycle datapath**: every instruction is fetched, decoded,
executed, accesses memory and writes back its result within one clock cycle. The design
is fully hierarchical — the top-level `CPU` circuit wires together ten self-contained
subcircuits, each implementing one architectural unit.

| | |
|---|---|
| **Architecture** | Single-cycle, Harvard (separate instruction & data memory) |
| **ISA** | RISC-V RV32I base integer (37 instructions) |
| **Data width** | 32-bit |
| **Registers** | 32 × 32-bit, `x0` hard-wired to zero |
| **Endianness** | Little-endian |
| **Built from** | 427 components and 1,315 wires across 10 subcircuits |

---

## 🧭 Architecture at a glance

The datapath follows the classic five logical stages, all collapsed into a single clock cycle:

```
        ┌──────┐   ┌─────────────┐   ┌──────────┐   ┌─────┐   ┌────────────┐   ┌────────────┐
 PC ──► │ IMEM │──►│   Decode    │──►│ Register │──►│ ALU │──►│ Data Memory│──►│ Write-Back │──┐
        │ ROM  │   │ Control+Imm │   │   File   │   └─────┘   │    RAM     │   │    MUX     │  │
        └──────┘   └─────────────┘   └──────────┘            └────────────┘   └────────────┘  │
   ▲                                       ▲                                                    │
   │                                       └────────────────── write-back ───────────────────-─┘
   └──── next-PC MUX ◄── PC+4 / PC+imm (branch & jump target) ◄── Branch Comparator
```

| Stage | Subcircuit(s) | Job |
|-------|---------------|-----|
| **Fetch** | `PC`, `Instruction_Memory` | Hold the program counter, read the 32-bit instruction, compute `PC+4`. |
| **Decode** | `Control_Unit`, `Imediate_Generator`, `Register_File` | Generate control signals from the opcode, sign-extend the immediate, read `rs1`/`rs2`. |
| **Execute** | `ALU`, `ALU_Control`, `Branch_Comparator` | Perform the arithmetic/logic operation; resolve branch conditions. |
| **Memory** | `Data_Memory` | Byte/half/word loads and stores into RAM. |
| **Write-back** | (muxing in `CPU`) | Select ALU result, memory data, or `PC+4` and write back to `rd`. |

---

## 🧩 The modules

Each block below is a real subcircuit in the `.circ` file. The schematics are rendered
directly from the saved component coordinates — so what you see is the actual wiring.

### Top-level CPU datapath
The `CPU` circuit ties everything together: instruction fetch, the next-PC logic
(PC+4, branch target, jump target) and the write-back multiplexers.

![CPU datapath](docs/images/CPU.svg)

### Arithmetic Logic Unit (ALU)
Computes all RV32I operations — `add`, `sub`, `and`, `or`, `xor`, `sll`, `srl`, `sra`,
`slt`, `sltu` — plus a pass-through path for `lui`. A dedicated comparator produces the
`zero` flag. The operation is chosen by a 4-bit `alu_ctrl` code.

![ALU](docs/images/ALU.svg)

<table>
<tr><td width="50%" valign="top">

### Register File
32 general-purpose registers built from 31 hardware registers (`x0` is constant 0),
with a decoder for the write port and two read multiplexers.

![Register File](docs/images/Register_File.svg)

</td><td width="50%" valign="top">

### Immediate Generator
Reconstructs and sign-extends the immediate for all five immediate formats
(I, S, B, U, J), selected by a 3-bit `imm_sel` signal from the control unit.

![Immediate Generator](docs/images/Imediate_Generator.svg)

</td></tr>
<tr><td valign="top">

### Control Unit
A ROM-based decoder mapping each 7-bit opcode to its bundle of control signals
(`reg_write`, `alu_src`, `mem_read`, `mem_write`, `mem_to_reg`, `branch`, `jump`, `alu_op`, `imm_sel`).

![Control Unit](docs/images/Control_Unit.svg)

</td><td valign="top">

### ALU Control
A second ROM that decodes `alu_op` + `funct3` + `funct7[5]` into the exact 4-bit ALU
operation code, distinguishing e.g. `add`/`sub` and `srl`/`sra`.

![ALU Control](docs/images/ALU_Control.svg)

</td></tr>
<tr><td valign="top">

### Data Memory
A 32-bit-wide RAM with full sub-word access: `lb`, `lh`, `lw`, `lbu`, `lhu` (with correct
sign/zero extension) and `sb`, `sh`, `sw`, decoded from `funct3`.

![Data Memory](docs/images/Data_Memory.svg)

</td><td valign="top">

### Branch Comparator
Evaluates `beq`, `bne`, `blt`, `bge`, `bltu`, `bgeu` and drives the branch-taken signal
into the next-PC multiplexer.

![Branch Comparator](docs/images/Branch_Comparator.svg)

</td></tr>
<tr><td valign="top">

### Program Counter
A 32-bit register with synchronous reset that latches the next-PC value each clock edge.

![PC](docs/images/PC.svg)

</td><td valign="top">

### Instruction Memory
A 32-bit-wide ROM holding the program; addressed by the PC (word-aligned).

![Instruction Memory](docs/images/Instruction_Memory.svg)

</td></tr>
</table>

---

## 📜 Supported instruction set

All 37 base-integer instructions (everything in RV32I except `ecall`/`ebreak`/`fence`):

| Format | Instructions |
|--------|--------------|
| **R-type** | `add` `sub` `sll` `slt` `sltu` `xor` `srl` `sra` `or` `and` |
| **I-type (ALU)** | `addi` `slti` `sltiu` `xori` `ori` `andi` `slli` `srli` `srai` |
| **I-type (Load)** | `lb` `lh` `lw` `lbu` `lhu` |
| **I-type (Jump)** | `jalr` |
| **S-type (Store)** | `sb` `sh` `sw` |
| **B-type (Branch)** | `beq` `bne` `blt` `bge` `bltu` `bgeu` |
| **U-type** | `lui` `auipc` |
| **J-type** | `jal` |

The `Control_Unit` ROM contains a decode entry for every one of the nine RV32I opcode
groups (`0x03 0x13 0x17 0x23 0x33 0x37 0x63 0x67 0x6F`).

---

## ▶️ Running it

> Requires [Logisim-Evolution **4.1.0** or newer](https://github.com/logisim-evolution/logisim-evolution/releases).

1. Open `RV32I_CPU.circ` in Logisim-Evolution.
2. The top-level circuit is `CPU` (set as `main`). Select it in the explorer pane.
3. Load your program into `Instruction_Memory`'s ROM (right-click → *Edit Contents…*),
   or use the bundled demo (see [`programs/`](programs/)).
4. **Simulate → Reset Simulation**, then tick the clock
   (**Simulate → Tick** / `Ctrl-T`, or enable auto-ticking).
5. Watch register values update through the `Register_File` and memory through `Data_Memory`.

### Bundled demo program
A small program is preloaded in the instruction ROM:

```asm
addi x1, x0, 5      # x1 = 5
addi x2, x1, 7      # x2 = 12
addi x3, x2, -2     # x3 = 10
jal  x0, 0          # loop forever (halt)
```

After three cycles the register file holds `x1=5`, `x2=12`, `x3=10` — a quick end-to-end
sanity check of fetch, decode, immediate sign-extension (note the negative immediate),
the ALU adder and write-back. See [`programs/README.md`](programs/README.md) for the
machine code and how to assemble your own.

---

## 🗂️ Repository structure

```
.
├── RV32I_CPU.circ            # ← the processor (open this in Logisim-Evolution)
├── README.md
├── LICENSE
├── docs/
│   ├── REPORT.md             # full project report & design write-up
│   └── images/               # schematics (SVG + PNG) of every subcircuit
├── programs/                 # demo program: assembly, machine code, notes
│   └── README.md
└── tools/
    └── render_circuits.py    # script that renders the .circ into the schematics above
```

---

## 📖 Documentation

- **[Full Project Report](docs/REPORT.md)** — design rationale, datapath walk-through,
  control-signal tables, per-module description and verification.
- **[Programs](programs/README.md)** — the demo program and an assembly cheat-sheet.

---

## 📝 Notes & honesty

- The processor is **single-cycle**: there is no pipelining, hazard logic or caching —
  by design, for clarity.
- `ecall` and `ebreak` are intentionally **not** implemented (excluded by the assignment).
- The schematic images are generated by [`tools/render_circuits.py`](tools/render_circuits.py)
  directly from the `.circ` geometry, so they faithfully reflect the saved circuit.

---

<div align="center">

*Built for DAC-102, IIT Roorkee · 2026.*
RISC-V is an open standard maintained by [RISC-V International](https://riscv.org/).

</div>
