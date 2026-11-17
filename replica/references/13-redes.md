# 13 · Redes (Reels y captions)

Objetivo: 3 guiones de Reels + captions + ganchos para Instagram y TikTok de **tu** app clonada, publicables sin tocar la marca del original.

## Entradas
`replica/fix-plan.md` y `replica/themes.md` (qué duele a los usuarios, fase 8), `replica/brand/` (voz y paleta propias), evidencia de `recon.md`/`parity.md` (`templates/evidence.md`), `templates/reels.md`.

## Pasos

1. **Elige 3 ángulos con evidencia** (no inventados): el problema que resuelve tu flujo `must` central, una demo rápida de una función que ya pasa parity, y la objeción más repetida de las reseñas con tu fix real. Si un ángulo se apoya en un hallazgo `THIN`, descártalo y elige otro.
2. **Copia `templates/reels.md`** en `replica/launch/redes.md` y rellena los 3 guiones: hook (0-3 s) → desarrollo (3-20 s) → cierre/CTA (20-30 s), con texto en pantalla y caption por guion.
3. **Captura el material solo de tu app**: pantallas y vídeo de tu app con tus datos. Ningún plano, captura ni audio del original, ni recortado ni difuminado.
4. **Ganchos**: usa el banco de la plantilla y reescríbelo en tu voz; misma pieza puede publicarse en IG y TikTok, el caption se adapta (hashtags propios, 3-5 por publicación).
5. **Sweep del copy (obligatorio, aquí y en cada re-tocado)**:
   ```bash
   python scripts/sweep.py replica/launch/redes.md --avoid "App Original" --avoid apporiginal.com
   ```
   Sale 0 antes de programar nada. Si escribe copy nuevo más adelante (landing, captions, emails), **re-sweep**: se vuelve a ejecutar; el gate no se pasa una vez y se olvida.
6. **Claims con evidencia**: toda cifra, precio o comparación lleva su fila de `templates/evidence.md` (fuente · observación · inferencia · confianza · límites). Nada de "el más rápido", "#1", métricas de usuarios o testimonios sin fuente; los límites honestos ("esto aún no lo hace") también se pueden decir en vídeo.
7. **Tabla de control**: rellena la tabla final de la plantilla (guion · claim · evidencia · sweep 0 · fecha de publicación) antes de programar.

## Salida
`replica/launch/redes.md` con los 3 guiones completos, captions, banco de ganchos usado y la tabla de control; capturas/vídeos propios en `replica/launch/media/` (opcional).

## Checklist
- [ ] 3 guiones con hook en los primeros 3 segundos y CTA claro.
- [ ] Cada claim con evidencia y confianza; ninguno `THIN` en antena.
- [ ] Cero menciones de la marca original, su dominio ni sus colores: `sweep.py` a 0 sobre todo el copy de redes.
- [ ] Todo el material audiovisual es de tu app, con tus datos.
- [ ] Caption con primera línea que engancha (≤125 caracteres), CTA y 3-5 hashtags propios.
- [ ] Tabla de control rellena; programación decidida por el usuario.

## No hagas
Nombrar (directa o indirectamente) al original en guion, caption, hashtags, texto en pantalla o comentarios; usar capturas suyas; prometer cifras sin fuente; ni publicar sin que el usuario lo haya pedido y revisado.
