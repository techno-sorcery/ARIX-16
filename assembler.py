# ARIX-16 Cross Assemble
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

dir_def = { ".byte":8, ".word":16, ".double":32, ".quad":64 }
dir_res = { ".resb":0.5, ".resw":1, ".resd":2,  ".resq":4 }
dir_misc = [ ".org", ".equ", ".seg" ]

error_msg = [ "Too few arguments", "Invalid register", "Invalid argument", "Oversized argument", 
              "Invalid label name", "Duplicate label", "Invalid data type" ]

width = 16
page = 2048

# Global variables
labels = {}
abs_num = 0
rel_num = 0
line_num = 0


# File management
path = "test.asm"

def main():
    global labels
    global abs_num
    global rel_num
    global line_num

    with open (path) as file:

        # Reset vars
        abs_num = 0
        rel_num = 0
        line_num = 0

        # First pass, generate symbol table
        for line in file:

            # Remove leading/trailing spaces and comments, and replace tabs
            line = line.replace("\;","a16-placeholder=semicolon")
            line = line.split(';', 1)[0].strip()
            line = line.replace("a16-placeholder=semicolon",";").expandtabs()

            # Ignore if blank
            if len(line) != 0:
                print(line)
                pass_first(line)

            line_num += 1

        # Dump symbol table
        dump_table(labels)


# First pass
def pass_first(line) -> None:
    global rel_num

    # Split line on first space, make lowercase
    line = line.split(' ', 1)
    op = line[0].lower()

    # Increment if instruction
    if op in op_alu or op in op_imm or op in op_mov or op in op_bra:
        rel_num += 1

    # Parse directives
    elif op in dir_res or op in dir_def or op in dir_misc:

        # Throw error if no arguments
        if len(line) <= 1:
            error(0, line[0])
            exit()

        rel_num = parse_dir(op, line[1].strip(), rel_num)

    # Parse labels
    else:
        parse_label(op)

        # Continue parsing if not empty
        if len(line) > 1:
            pass_first(line[1].strip())


# Parse labels
def parse_label(label) -> None:

    # Check if valid, non-duplicate label
    if not label[0].isalpha():
        error(4,label)
        exit()

    if label in labels:
        error(5,label)
        exit()

    # Add label to symbol table
    labels[label] = [line_num, rel_num]


# Parse directives 
def parse_dir(op, args, rel_num) -> int:

    # Parse def directives
    if op in dir_def:
        vals = parse_def(op, args) 

        # rel_num offset
        rel_num += len(vals)
    
    # Parse res directives
    elif op in dir_res:
        arg = parse_val(args, width)[1]

        # rel_num offset
        rel_num += int(math.ceil(dir_res[op] * arg))

    # Parse org directive
    elif op == ".org":
        rel_num = parse_val(args, width)[1]

    # Parse equ directive
    elif op == ".equ":
        parse_equ(args)

    # Parse seg directive
    elif op == ".seg":
        rel_num = parse_seg(args)

    return rel_num


# Parse seg directive
def parse_seg(args) -> int:
    # args = args.split(',')
    # alignment = 0

    # # Throw error if no args
    # if len(args) == 0:
    #     error(0, args)
    #     exit()

    # # Two args
    # if len(args >= 2):

    #     # Set alignment
    #     alignment = args[1]

    # # Create label
    # parse_label(args[0])
    # # labels[]
    
    return 0


# Parse equ directive
def parse_equ(args) -> None:
    args = args.split(',')

    # Throw error if less than two args
    if len(args) < 2:
        error(0, args)
        exit()

    # Extract arguments
    arg = parse_val(args[0].strip(), width)[1]
    label = args[1].strip()

    # Create label, and set to arg
    parse_label(label)
    labels[label][1] = arg



# Parse def directives
def parse_def(op: str, args) -> list:
    vals = []
    bits = dir_def[op]

    # Split and strip arguments
    args = args.split(',')

    # Iterate through args
    for arg in args:
        arg = arg.strip()

        # Parse string
        if arg.startswith("\"") and arg.endswith("\""):
            for char in arg[1:-1]:
                vals = def_words(format(ord(char), "0" + str(bits) + "b"), vals, bits)

        # Parse numbers
        else:
            vals = def_words(parse_val(arg, bits)[0], vals, bits)

    return vals


# Split words for def 
def def_words(val, vals, bits):
    len_vals = len(vals)-1

    # Byte, or less
    if bits <= width / 2:

        # High byte
        if len(vals) >= 1 and len(vals[len_vals]) <= bits:
            vals[len_vals] = vals[len_vals] + str(val)
        # Low byte
        else:
            vals.append(val)

    # Word or greater
    else:
        for i in range(math.ceil(bits/width)):
            vals.append(val[:width])
            val = val[width:]

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


# Parse opcode arguments
def parse_args(line: list, form: str) -> str:

    # Throw error if no arguments
    if len(line) <= 1:
        error(0, line[0])
        exit()

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
    print("\n" + error_msg[error_num] + " on line " + str(line_num) +", \n\"" + text+ "\"")


# Dump symbol table entries
def dump_table(labels):
    header = ["Number", "Line", "Label", "Address"]
    index = 0
    print("\n{: <20} {: <20} {: <20} {: <20}\n".format(*header))

    # Step through entries
    for label in labels:
        row =[index, labels[label][0], label, labels[label][1]]
        print("{: <20} {: <20} {: <20} {: <20}".format(*row))

        index += 1


# Run main function
if __name__ == "__main__":
    main()
