# ARIX-16 Cross Assembler
# Written by Hayden Buscher, 2023

import os
import math
from datetime import datetime

# Constants
op_alu = { "inc":"00000100", "dec":"00001000", "add":"00001100", "adc":"00010000", "sub":"00010100",
           "sbb":"00011000", "and":"00011100", "or":"00100000",  "xor":"00100100", "not":"00101000",
           "lsh":"00101100", "lrt":"00110000", "cmp":"00110100" }
op_imm = { "ldi":"0100", "ldh":"0101", "ldl":"0110" }
op_mov = { "mov":"10000000", "swp":"10001000", "ldm":"10010000", "lds":"10011000", "ldp":"10100000",
           "stb":"10000001", "stm":"10000010", "sts":"10000011", "jmp":"10000100" }
op_bra = { "jre":"110000", "bie":"110001", "bne":"110010", "big":"110011", "bil":"110100", "bge":"110101",
           "ble":"110110", "bic":"110111", "bnc":"111000", "bin":"111001", "bnn":"111010", "biv":"111011",
           "bnv":"111100", "nop":"111101"}

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
dir_misc = [ ".org", ".equ", ".seg", ".macro", ".end"]

error_msg = [ "Too few arguments", "Invalid register", "Invalid argument", "Oversized argument", 
              "Invalid label name", "Duplicate label", "Invalid data type", "Invalid instruction" ]

width = 16
rel_width = 10
page = 2048
version = "1.0"

# Global variables
listing = True

def main():
    global full_line
    global line_num
    global symtable
    global rel_num

    path = "test.asm"
    full_line = ""

    symtable = {}
    macros = {}

    macmode = ""

    rel_num = 0
    line_num = 1

    seg_id = "None"
    seg_base = 0

    # Listing header
    if listing:
        print("ARIX-16 Cross Assembler, v" + version)
        print("File: " + path)
        print("Date: " + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
        print("\n")

    # First pass header
    if listing:
        header = ["Number", "Label", "Line", "Hex", "Dec", "Segment"]

        print("--- Pass 1, Symbol table ---")
        print("\n{: <10} {: <20} {: <8} {: <8} {: <10} {: <10}\n".format(*header))

    # First pass, generate symbol table
    with open (path) as file:
        for line in file:

            # Remove leading/trailing spaces and comments, and replace tabs
            line = line.replace("\;","a16-placeholder=semicolon")
            line = line.split(';', 1)[0].strip()
            line = line.replace("a16-placeholder=semicolon",";").expandtabs()

            full_line = line

            # Ignore if blank
            if len(line) != 0:
                len_orig = len(symtable)
                parsed = parse_line(1, 0, line, rel_num, symtable, seg_id, seg_base, macros, macmode)

                rel_num = parsed[0]
                symtable = parsed[1]
                seg_id = parsed[2]
                seg_base = parsed[3]
                macros = parsed[5]
                macmode = parsed[6]


                # Print last symtable entry
                if listing and len_orig < len(parsed[1]):
                    label = list(parsed[1])[-1]
                    val_hex = format(int(parse_val(str(symtable[label]),width)[0],2), "04X")
                    row = [len_orig + 1, label, line_num, val_hex, symtable[label], seg_id]

                    print("{: ^10} {: <20} {: <8} {: <8} {: <10} {: <10}".format(*row))

            line_num += 1

    # Second pass header 
    if listing:
        header = ["Address", "Data", "Line", "Text"]

        print("\n\n--- Pass 2, Assembly ---")
        print("\n{: <10} {: <22} {: <8} {: <10}\n".format(*header))

    # Reset counters
    rel_num = 0
    line_num = 1

    # Second pass, fill symbols, parse instructions, and generate hex
    with open (path) as file:
        for line in file: 
            full_line = line.strip("\n")
            rel_old = rel_num
            data = [""]

            # Remove leading/trailing spaces and comments, and replace tabs
            line = line.replace("\;","a16-placeholder=semicolon")
            line = line.split(';', 1)[0].strip()
            line = line.replace("a16-placeholder=semicolon",";").expandtabs()

            # Ignore if blank
            if len(line) != 0:
                parsed = parse_line(2, 0, line, rel_num, {}, seg_id, seg_base, macros, macmode)

                rel_num = parsed[0]
                data = parsed[4]

            # Print assembled code
            print_data(rel_old, data)

            line_num += 1


# Print assembled code
def print_data(rel_old, data):
    if listing:
        data_form = [""]

        # Format data by rows
        for val in data:

            # Create new row if width exceeded
            if len(data_form[-1]) >= 20:
                data_form.append("")

            # Format data if not blank
            if val != "":
                data_form [-1] += format(int(val,2), "04X") + " "
            
        first_line = True

        # Print rows
        for data in data_form:

            # First line
            if first_line:
                if data != "":
                    row = [format(rel_old, "04X"), data, line_num, full_line]
                else:
                    row = ["", "", line_num, full_line]

                first_line = False

            # Successive lines
            else:
                row = ["", data, "", ""]

            print("{: ^10} {: <22} {: <8} {: <10}".format(*row))


# Line parsing for both passes
def parse_line(pass_num, loop, line, rel_num, symtable, seg_id, seg_base, macros, macmode) -> tuple:
    data = [""]

    # Split line on first space, make lowercase
    line = line.split(' ', 1)
    op = line[0].lower()

    # Parse instruction
    if op in op_alu or op in op_imm or op in op_mov or op in op_bra:

        # Parse if second pass
        if pass_num == 2:

            # Throw error if no arguments
            if len(line) <= 1:
                error(0)
                exit()

            data = [parse_op(op, line[1].strip())]
        
        # Increment relative address
        rel_num += 1


    # Parse directives
    elif op in dir_res or op in dir_def or op in dir_misc:

        # Throw error if no arguments
        if len(line) <= 1:
            error(0)
            exit()

        parsed = parse_dir(op, line[1].strip(), rel_num, symtable, seg_id, seg_base, macros, macmode)

        rel_num = parsed[0]
        symtable = parsed[1]
        seg_id = parsed[2]
        seg_base = parsed[3]
        data = parsed[4]
        macros = parsed[5]
        macmode = parsed[6]

    # Parse symbols
    elif loop == 0:
    
        # Add to symtable if first pass
        if pass_num == 1:
            symtable = parse_symbol(op, rel_num, symtable)

        # Continue parsing if not empty
        if len(line) > 1:
            parsed = parse_line(pass_num, 1, line[1].strip(), rel_num, symtable, seg_id, seg_base, macros, macmode)

            rel_num = parsed[0]
            symtable = parsed[1]
            seg_id = parsed[2]
            seg_base = parsed[3]
            data = parsed[4]
            macros = parsed[5]
            macmode = parsed[6]

    # Throw error if invalid instruction
    else:
        error(7)
        exit()

    return (rel_num, symtable, seg_id, seg_base, data, macros, macmode)


# Parse opcodes
def parse_op(op, args):

    # ALU instructions
    if op in op_alu:
        return op_alu[op] + parse_args("ALU", args)

    # IMM instructions
    elif op in op_imm:
        return op_imm[op] + parse_args("IMM", args)

    # MOV instructions
    elif op in op_mov:
        return op_mov[op] + parse_args("MOV", args)

    # BRA instructions
    else:
        return op_bra[op] + parse_args("BRA", args)


# Write to output file
def file_out(bin) -> None:
    # print(bin)
    a = 1


# Parse symtable
def parse_symbol(name, val, symtable) -> list:

    # Check if valid, non-duplicate label
    if not name[0].isalpha():
        error(4)
        exit()

    if name in symtable:
        error(5)
        exit()

    # Add label to symbol table
    symtable[name] = parse_val(str(val), width)[1]

    return symtable


# Parse directives 
def parse_dir(op, args, rel_num, symtable, seg_id, seg_base, mactable, macmode) -> tuple:
    data = []

    # Parse def directives
    if op in dir_def:
        data = parse_def(op, args) 

        # rel_num offset
        rel_num += len(data)
    
    # Parse res directives
    elif op in dir_res:
        arg = parse_val(args, width)[1]

        # Calculate offset
        word_num = int(math.ceil(dir_res[op] * arg))

        # Create blank data, add to rel_num
        data = ["0"] * word_num
        rel_num += word_num

    # Parse org directive
    elif op == ".org":
        rel_num = parse_val(args, width)[1]

    # Parse equ directive
    elif op == ".equ":
        symtable = parse_equ(args, symtable)

    # Parse seg directive
    elif op == ".seg":
        parsed = parse_seg(args, rel_num, symtable, seg_id, seg_base)

        rel_num = 0
        seg_id = parsed[0]
        seg_base = parsed[1]
        symtable = parsed[2]

    # Parse macro directive
    elif op == ".macro":
        macmode = True
        

    return (rel_num, symtable, seg_id, seg_base, data, mactable, macmode)


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


# Parse seg directive
def parse_seg(args, rel_num, symtable, seg_id, seg_base) -> tuple:
    alignment = 1
    args = args.split(',')

    # No offset for first segment, by default
    if seg_id == "None":
        alignment = 0

    # Throw error if no args
    if len(args) == 0:
        error(0)
        exit()

    # Two args
    if len(args) >= 2:

        # Set alignment
        alignment = int(args[1])

    # Set id, base address, and label
    seg_id = args[0]
    seg_base = (((seg_base + rel_num) // page) + alignment) * page
    symtable = parse_symbol(args[0], seg_base // (2 ** 11), symtable)

    return (seg_id, seg_base, symtable)


# Parse equ directive
def parse_equ(args, symtable) -> list:
    args = args.split(',')

    # Throw error if less than two args
    if len(args) < 2:
        error(0)
        exit()

    # Extract arguments
    name = args[0].strip()
    arg = parse_val(args[1].strip(), width)[1]

    # Create label, and set to arg
    symtable = parse_symbol(name, arg, symtable)

    return symtable


# Parse opcode arguments
def parse_args(op, args) -> str:

    # Split and strip arguments
    args = args.split(',',1)
    for i in range(len(args)):
        args[i] = args[i].strip()
    
    # Parse ALU and MOV args
    if op == "ALU" or op == "MOV":

        # One argument
        if len(args) == 1:
            return parse_reg(args[0]) + parse_reg(args[0])
        
        # Two arguments
        else:
            return parse_reg(args[1]) + parse_reg(args[0])

    # Parse IMM args
    elif op == "IMM":

        # Two arguments
        if len(args) > 1:
            return parse_val(args[1], 8)[0] + parse_reg(args[0]) 

        # Throw error if one argument
        else:
            error(0)
            exit()

    # Parse BRA args
    else:
        return parse_val(args[0], rel_width)[0]


# Parse register names
def parse_reg(reg: str) -> str:
    if reg in op_regs:
        return op_regs[reg]
    else:
        error(1)
        exit()


# Parse numerical values
def parse_val(val: str, bits: int) -> tuple:
    val_dec = 0 
    temp_bits = bits
    mod = ""
    
    # Char
    if (val.startswith('\'') and val.endswith('\'')) and len(val) == 3:
        val_dec = ord(val[1])

    else:

        # Extract modifier
        args = val.split(".")
        val = args[0]

        # Symbol
        if val in symtable:

            # Set modifier if present
            if len(args) > 1:
                mod = args[1].lower()

            # Adjust bit width
            if mod == "hi" or mod == "lo":
                bits = width

            # Read value from symtable
            if mod == "rel":
                    val_dec = symtable[val] - rel_num
                    bits = rel_width
            else:
                val_dec = symtable[val]

        # Number
        else:

            # Convert to decimal
            try:
                val_dec = int(val,0)

            # Throw error if invalid format
            except:
                error(2)
                exit()

    # Binary string conversion, negative
    if val_dec < 0:
        val_2c = ~(val_dec + 1)
        val_bin = format(val_2c, "1=" + str(bits) + "b")

    # Binary string conversion, positive
    else:
        val_bin = format(val_dec, "0" + str(bits) + "b")

    # Parse modifiers
    if mod == "hi":
        val_bin = val_bin[0:width // 2]
        
    elif mod == "lo":
        val_bin = val_bin[width // 2 : width]

    bits = temp_bits

    # Check if too long
    if len(val_bin) > bits:
        error(3)
        exit()

    return (val_bin, val_dec)


# Error codes
def error(error_num):
    print("\n" + error_msg[error_num] + " on line " + str(line_num) +", \n\"" + full_line.strip() + "\"")


# Run main function
if __name__ == "__main__":
    main()

