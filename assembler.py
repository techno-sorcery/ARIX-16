# ARIX-16 Cross Assembler
# Written by Hayden Buscher, 2023

# import re
import os
import math

# Constants
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

dir_def = [".byte", ".word", ".double", ".quad"]
dir_res = [".resb", ".resw", ".resd", "resq"]
dir_misc = [".org",".seg", ".equ", ".rep"]

error_msg = [ "Too few arguments", "Invalid register", "Invalid argument",
              "Oversized argument", "Invalid label name", "Duplicate label"]


# Variables
labels = {}
linenum = 0


# File management
path = "test.asm"

def main():
    with open (path) as file:

        # First pass, generate symbol table
        for line in file:

            # Remove leading/trailing spaces and comments
            line = line.replace("\;","a16-placeholder=semicolon")
            line = line.strip().split(';', 1)[0]
            line = line.replace("a16-placeholder=semicolon",";")
            
            # Don't parse if empty
            if len(line) != 0:
                parse_label(line)


# Parse labels
def parse_label(line) -> None:
    global labels
    global linenum

    # Remove leading/trailing spaces, and split
    line = line.strip().split(' ',1)
    line[0] = line[0].lower()

    # Increment line num if instruction
    if line[0] in op_alu or line[0] in op_imm or line[0] in op_mov or line[0] in op_bra:
        linenum += 1

    # Parse directives
    elif line[0] in directives:
        parse_directive(line) 

    else:

        print(line[0] + " : " + str(linenum))

        # Check if valid, non-duplicate label
        if not line[0][0].isalpha():
            error(4,line[0])
            exit()

        if line[0] in labels:
            error(5,line[0])
            exit()

        # Add label to symbol table
        labels[line[0]] = linenum

        # Continue parsing if more commands
        if len(line) > 1:
            parse_label(line[1])


# Parse directives
def parse_directive(line) -> None:
    global labels
    global linenum

    # Check if directive has arguments
    if len(line) > 1:
        line[1] = line[1].strip()

        if line[0] == ".org":
            linenum = parse_val(line[1], 16)[1]

        elif line[0] == ".word" or line[0] == ".byte":
            vals = parse_def(line[1], line[0])
            linenum += len(vals)

        elif line[0] == ".res":
            linenum += parse_val(line[1], 16)[1]

        elif line[0] == "equ":
            
        
        
    else:
        error(0, line[0])
        exit()

    print(linenum)

# Parse resb and resw
# def parse_res(line, )

# Parse dw and db args
def parse_def(line, form: str) -> list:
        vals = []
        byte_low = True

        # Split and strip arguments
        line = line.split(',')

        # Iterate through args
        for arg in line:
            arg = arg.strip()

            # Parse string
            if arg.startswith("\"") and arg.endswith("\""):
                for char in arg[1:-1]:

                    # Define byte
                    if form == ".byte":

                        # Low byte
                        if byte_low:
                            vals.append(format(ord(char), "08b"))
                            
                        # High byte
                        else:
                            vals[len(vals)-1] = vals[len(vals)-1] + (format(ord(char), "08b"))

                        byte_low = not byte_low
                        
                    # Define word
                    else:
                        vals.append(format(ord(char), "016b"))

                    # Throw error if too long
                    if(len(vals[len(vals)-1]) > 16):
                        error(3, arg)
                        exit();
                
                # # Null terminator
                # if (byte_low and form == ".byte") or form == "dw":
                #     vals.append(0)

                # byte_low = True

            # Parse numbers
            else:

                # Define byte
                if form == ".byte":

                    # Low byte
                    if byte_low:
                        vals.append(parse_val(arg, 8))
                    
                    # High byte
                    else:
                        vals[len(vals)-1] = vals[len(vals)-1] + parse_val(arg, 8)

                    byte_low = not byte_low

                # Define word
                else:
                    vals.append(parse_val(arg, 16))

        return vals


# Parse opcodes
def parse_op(line):

    # Remove leading/trailing spaces, and split
    line = line.strip().split(' ',1)

    line_op = line[0].lower()
    op_word = ""

    print(line)
    
    # ALU instructions
    if line_op in op_alu:
        op_word = op_alu[line_op] + parse_args(line, "ALU")

    # IMM instructions
    elif line_op in op_imm:
        op_word = op_imm[line_op] + parse_args(line, "IMM")

    # MOV instructions
    elif line_op in op_mov:
        op_word = op_mov[line_op] + parse_args(line, "MOV")

    # BRA instructions
    elif line_op in op_bra:
        op_word = op_bra[line_op] + parse_args(line, "BRA")

    # Labels
    else:
        labels[line_op] = 0
        
        # Continue parsing if more commands
        if len(line) > 1:
            parse_op(line[1])

    print(op_word)


# Parse arguments
def parse_args(line: list, form: str) -> str:

    # Check if instruction has arguments
    if len(line) > 1:

        # Split and strip arguments
        args = line[1].split(',',1)
        for i in range(len(args)):
            args[i] = args[i].strip()

        print(args)
        
        # Parse ALU and MOV args
        if form == "ALU" or form == "MOV":

            # One argument
            if len(args) == 1:
                return parse_reg(args[0]) + parse_reg(args[0])
            
            # Two arguments
            else:
                return parse_reg(args[0]) + parse_reg(args[1])

        # Parse IMM args
        elif form == "IMM":

            # Two arguments
            if len(args) > 1:
                return parse_val(args[0], 8)[0] + parse_reg(args[1])

            # Throw error if one argument
            else:
                error(0, line)
                exit()

        # Parse BRA args
        else:
            return parse_val(args[0], 11)[0]

    else:
        error(0, line)
        exit()


# Parse register names
def parse_reg(reg: str) -> str:
    if reg in op_regs:
        return op_regs[reg]
    else:
        error(1, reg)
        exit()


# Parse numerical values
def parse_val(val: str, bits: int) -> tuple:
    val_dec = 0 
    val_bin = "0"
    
    # Char
    if (val.startswith('\'') and val.endswith('\'')) and len(val) == 3:
        val_dec = ord(val[1])

    # Number
    else:
        try:
            val_dec = int(val,0)

        except:
            error(2, val)
            exit()

    # Check if too long
    if val_dec >= 2**bits:
        error(3, val)
        exit()

    return (format(val_dec, "0" + str(bits) + "b"), val_dec)


# Error codes
def error(error_num, text):
    print(error_msg[error_num] + " on line " + str(linenum) +", \n\"" + text+ "\"")


# Run main function
if __name__ == "__main__":
    main()
