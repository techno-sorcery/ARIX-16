; This is a tes.seg directivet
        ; ldi 0xA, a0
        ; sub a1,a2
; menu
    ; ldi 't', a1
    ; add a0, a1      ; More comments!

    ; org  0xF

; test  
    ; jre 0x3FF
    ; jre menu

; mytext  db "test!", 'c', 0xFE, 123
        ; dw "test!", 'c', 0xFE, 123

; var     resw    5
; var2    resb    5
        ; equ 5 var2

.seg data
var  .byte   "test", 0, 'c'
var2 .word   "test", 0, 'c'
     .double 239212
     .quad   494949343

     .resb   5
     .resw   5
     .resd   5
     .resq   5
     .equ    10, myconst

.seg text, 2

add 
