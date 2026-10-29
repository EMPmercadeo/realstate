#!/bin/bash
cd "$(dirname "$0")/.."
for v in hospital comedor terraza gris aerea casa calle salon_b recepcion; do
  python3 blender/render.py $v 40 1400 2>&1 | grep -v Warning | tail -1
done
echo ALLDONE
