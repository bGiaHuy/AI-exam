; hello.asm (Windows x64 + NASM + MinGW)

section .data
    msg db "Hello, World!", 10, 0

section .text
    extern printf
    global main

main:
    sub rsp, 40        ; shadow space theo quy uoc goi ham Windows

    lea rcx, [rel msg] ; tham so thu nhat cho printf
    call printf

    add rsp, 40

    xor eax, eax       ; return 0
    ret