# ARIX-16 Cross Assembler
# Written by Hayden Buscher, 2023

import re
import os

op_alu = { "inc":"00000100", "dec":"00001000", "add":"00001100", "adc":"00010000", "sub":"00010100",
           "sbb":"00011000", "and":"00011100", "or":"00100000",  "xor":"00100100", "not":"00101000",
           "lsh":"00101100", "lrt":"00110000" }
op_imm = { "ldi":"0100", "ldih":"0101" }
op_mov = { "mov":"10000000", "swp":"10001000", "ldm":"10010000", "lds":"10011000", "ldp":"10100000",
           "stb":"10000001", "stm":"10000010", "sts":"10000011", "jmp":"10000100" }
op_bra = { "jre":"11000", "bin":"11001", "bic":"11010", "bie":"11011",
           "bnn":"11101", "bnc":"11110", "bne":"11111" }

op_regs = { "r0":"0000",  "r1":"0001",  "r2":"0010",  "r3":"0011", 
            "r4":"0100",  "r5":"0101",  "r6":"0110",  "r7":"0111", 
            "r8":"1000",  "r9":"1001",  "r10":"1010", "r11":"1011", 
            "r12":"1100", "r13":"1101", "r14":"1110", "r15":"1111",

            "a0":"0000", "a1":"0001", "a2":"0010", "a3":"0011", 
            "t0":"0100", "t1":"0101", "v0":"0110", "v1":"0111", 
            "v2":"1000", "v3":"1001", "v4":"1010", "v5":"1011", 
            "v6":"1100", "lr":"1101", "fp":"1110", "sp":"1111" }

error_msg = [ "Instruction called without arguments", "Invalid register called" ]

labels = {}
linenum=0


# File management
path = "test.asm"

def main():
    with open (path) as file:
        for line in file:

            # Remove leading/trailing spaces and comments
            line = line.replace("\\;","acasm16-placeholder=semicolon")
            line = line.strip().split(';', 1)[0]
            line = line.replace("acasm16-placeholder=semicolon",";")
            
            # Don't parse if empty
            if len(line) != 0:
                parse_op(line)


# Parse opcodes
def parse_op(line):

    # Remove leading/trailing spaces, and split
    line = line.strip().split(' ',1)

    line_op = line[0].lower()
    op_word = ""

    print(line)
    
    # ALU instructions
    if line_op in op_alu:
        op_word = op_alu[line_op] + parse_alu(line)
        print(op_word)

    # IMM instructions
    elif line_op in op_imm:
        op_word = op_imm[line_op]
        # parse_params(line)

    # MOV instructions
    elif line_op in op_mov:
        op_word = op_mov[line_op]
        # parse_params(line)

    # BRA instructions
    elif line_op in op_bra:
        op_word = op_bra[line_op]
        # parse_params(line)

    # Labels
    else:
        labels[line_op] = 0
        
        # Continue parsing if more commands
        if len(line) > 1:
            parse_op(line[1])


    # print(op_word)


# Parse ALU instructions
def parse_alu(line):

    # Check if instruction has arguments
    if len(line) > 1:

        # Split and strip arguments
        args = line[1].split(',',1)
        for i in range(len(args)):
            args[i] = args[i].strip()

        print(args)
        
        # One argument
        if len(args) == 1:
            reg0 = parse_reg(args[0])

            return(reg0 + reg0)
        
        # Two arguments
        else:
            reg0 = parse_reg(args[0])
            reg1 = parse_reg(args[1])

            return(reg0 + reg1)

    else:
        error(0, line)
        exit()


# Parse register names
def parse_reg(reg):
    if reg in op_regs:
        return op_regs[reg]
    else:
        error(1, reg)
        exit()


# Error codes
def error(error_num, text):
    print(error_msg[error_num] + " on line " + str(linenum) +", \n\"" + text+ "\"")


# Run main function
if __name__ == "__main__":
    main()
