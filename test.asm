; This is a test
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

var:    .byte   "test",'c'
        .equ    var1,'c'

        .seg    data,16
        mov     r1,r2
