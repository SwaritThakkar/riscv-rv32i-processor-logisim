# Demo RV32I program preloaded in Instruction_Memory.
# Exercises the addi datapath, including a sign-extended negative immediate.
#
#   addr   machine code   instruction
#   0x00   0x00500093     addi x1, x0, 5
#   0x04   0x00708113     addi x2, x1, 7
#   0x08   0xffe10193     addi x3, x2, -2
#   0x0c   0x0000006f     jal  x0, 0
#
# Expected after 3 ticks: x1=5, x2=12, x3=10.

addi x1, x0, 5      # x1 = 5
addi x2, x1, 7      # x2 = 12
addi x3, x2, -2     # x3 = 10
jal  x0, 0          # halt (loop on self)
