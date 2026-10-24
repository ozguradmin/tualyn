#!/usr/bin/env bash
# Kıpır v1: tüm baskı parçalarını STL'e döker ve önizleme görselleri üretir.
# Gerekenler: openscad (2021.01+). Görseller için ekransız sunucuda xvfb-run.
# Kullanım:  ./build.sh            (STL + PNG)
#            ./build.sh stl        (sadece STL)
set -euo pipefail
cd "$(dirname "$0")"

PARTS=(taban ust_kat boyun kafa_ray cene_sol cene_sag teker_kapak sensor_tutucu kulak_sol kulak_sag)
mkdir -p stl img

OSC=(openscad)
if [ -z "${DISPLAY:-}" ] && command -v xvfb-run >/dev/null; then
  OSC=(xvfb-run -a openscad)
fi

for p in "${PARTS[@]}"; do
  echo ">> $p.stl"
  openscad -q -D "part=\"$p\"" -o "stl/kipir_$p.stl" kipir.scad
done

python3 stl_ikili.py stl/*.stl >/dev/null   # ASCII -> ikili STL (~5 kat küçük)

# Baskı yönü ve profil bilgisiyle 3MF (stüdyolar, özellikle Bambu kullananlar sever)
if command -v prusa-slicer >/dev/null; then
  mkdir -p 3mf
  PS=(prusa-slicer)
  if [ -z "${DISPLAY:-}" ] && command -v xvfb-run >/dev/null; then PS=(xvfb-run -a prusa-slicer); fi
  for p in "${PARTS[@]}"; do
    "${PS[@]}" --export-3mf --load slicer/pla_020_20pct.ini --center 128,128 \
      -o "3mf/kipir_$p.3mf" "stl/kipir_$p.stl" >/dev/null
  done
fi

[ "${1:-}" = "stl" ] && exit 0

for p in "${PARTS[@]}"; do
  "${OSC[@]}" -q -D "part=\"$p\"" --viewall --autocenter --imgsize=800,600 \
    --colorscheme=Tomorrow --camera=0,0,0,55,0,25,0 -o "img/$p.png" kipir.scad
done

"${OSC[@]}" -q -D 'part="assembly"' --viewall --autocenter --imgsize=1400,1050 \
  --colorscheme=Tomorrow --camera=0,0,0,65,0,30,0 -o img/montaj_on.png kipir.scad
"${OSC[@]}" -q -D 'part="assembly"' --viewall --autocenter --imgsize=1400,1050 \
  --colorscheme=Tomorrow --camera=0,0,0,65,0,210,0 -o img/montaj_arka.png kipir.scad
"${OSC[@]}" -q -D 'part="assembly"' --viewall --autocenter --imgsize=1400,1050 \
  --colorscheme=Tomorrow --camera=0,0,0,90,0,0,0 -o img/montaj_yan.png kipir.scad
"${OSC[@]}" -q -D 'part="assembly"' --viewall --autocenter --imgsize=1400,1050 \
  --colorscheme=Tomorrow --camera=0,0,0,160,0,30,0 -o img/montaj_alt.png kipir.scad
echo "tamam"
