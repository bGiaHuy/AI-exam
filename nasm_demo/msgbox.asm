; msgbox.asm (Windows x64 GUI Popup Window via MessageBoxA)

default rel

section .data
    caption db "Thong bao tu NASM", 0
    message db "Chao ban! Day la cua so popup tao boi NASM Assembly x64.", 0

section .text
    extern MessageBoxA
    extern ExitProcess
    global main

main:
    sub rsp, 40             ; Shadow space + 16-byte alignment

    xor ecx, ecx            ; hWnd = NULL (0)
    lea rdx, [message]      ; lpText
    lea r8, [caption]       ; lpCaption
    xor r9d, r9d            ; uType = MB_OK (0)
    call MessageBoxA

    xor ecx, ecx            ; Exit code = 0
    call ExitProcess