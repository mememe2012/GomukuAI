@echo off
cls

python -m nuitka ^
    GomokuAI.py ^
    --enable-plugin=upx ^
    --upx-binary=--best ^
    --standalone ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=icon/icon.ico ^
    --output-dir=../exe ^
    --windows-company-name=mememe2012 ^
    --windows-uac-admin ^
    --windows-product-name=GomokuAI^
    --windows-file-version=0.0.1.0^
    --windows-product-version=0.0.1.0 ^
    --plugin-enable=tk-inter ^
    --jobs=8 ^
    --zig
    
pause