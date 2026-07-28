#!/bin/bash
echo "Limpando..."
rm -rf data/ UNPACK_default.iso/

echo "Extraindo ISO..."
ps2iso.exe unpack default.iso
mv UNPACK_default.iso data

echo "Compilando C..."
ee-gcc -D_EE -G0 -O2 -c src/hello.c -o hello.o

echo "Linkando..."
armips.exe linker.asm

echo "Gerando ISO..."
ps2iso.exe pack data/METADATA.json

echo "Pronto! ISO gerada em data/OUTPUT.iso"
