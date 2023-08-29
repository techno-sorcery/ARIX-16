; This is a test
        ldi 0xFA, a0
menu    ldi 0x1, a1
        add a0, a1      ; More comments!
        jre menu
