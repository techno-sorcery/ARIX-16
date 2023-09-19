;blah
;test 123!
.seg data
var  .byte   "test", 0, 'c'
var2 .word   "test", 0, 'c'
     .double 239212
     .quad   494949343

     .resb   5
     .resw   5
     .resd   5
     .resq   5
     .equ    myconst,-15
     .equ    large,48203

.macro ldi16,val,reg
    ldh reg,val.hi
    ldl reg,val.lo
.end

.seg text, 2
loop
    ldi a1,30
    ldi a2,10
    nop 0
    add a1,a2
    ldi a2,myconst
    inc sp
    ldi a1,'>'
    ldh a2,large.hi
    ldl a2,large.lo
    jre loop.rel
