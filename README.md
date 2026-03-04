# ProyectoCalculo - Curvas de Nivel

Este proyecto tiene dos aplicaciones en Python con interfaz grafica para estimar areas a partir de puntos tomados sobre una imagen.

- `parte1.py`: area entre dos curvas tipo funcion (`f(x)` y `g(x)`).
- `parte2.py`: area entre dos curvas cerradas (`C1` exterior y `C2` interior).

## Explicacion general del codigo

### Parte 1 (`parte1.py`)

- `preparar_nodos_unicos(...)`: ordena nodos y fusiona `x` repetidas.
- `construir_spline_natural(...)`: crea interpolante spline cubico natural en un tramo.
- `construir_interpolante_por_trozos_spline(...)`: arma una funcion por tramos usando divisiones (maximo 3 subintervalos por curva).
- `area_entre_curvas_por_subintervalos(...)`: suma el area por cada subintervalo comun entre `f` y `g`.
- `simpson(...)`: integra numericamente con Simpson compuesta.
- `area_entre_curvas(...)`: calcula `\int_a^b |f(x)-g(x)| dx`.
- `AppParte1`: maneja toda la UI (carga de imagen, limites con clicks, nodos/divisiones, dibujo y calculo).

### Parte 2 (`parte2.py`)

- `evaluar_lagrange(...)` y `derivada_lagrange(...)`: interpolacion y derivada en parametro `t`.
- `area_integral_linea(...)`: aplica formula de Green con integracion de linea:
  - construye parametrizacion local por ventanas,
  - integra `x(t)*y'(t) - y(t)*x'(t)` con Simpson.
- `shoelace(...)`: area poligonal por formula del cordon.
- `AppParte2`: UI de nodos para curvas cerradas, metodos y visualizacion.

## Unidades

- **Parte 1** trabaja directamente en pixeles:
  - nodos y divisiones se toman en `(px, py)`,
  - el resultado de area se reporta en `px^2`.
- **Parte 2** tambien trabaja directamente en pixeles:
  - nodos se toman en `(px, py)`,
  - el resultado de area se reporta en `px^2`.

## Guia de uso de la UI - Parte 1

1. Abrir `parte1.py`.
2. Pulsar **Cargar imagen**.
3. Antes de poner nodos, en modo **Fijar limites en imagen**, marcar en la imagen las lineas:
   - `a` (vertical izquierda),
   - `b` (vertical derecha),
   - `c` (horizontal inferior),
   - `d` (horizontal superior).
4. Elegir curva activa (`f` o `g`).
5. (Opcional) En modo **Colocar divisiones de tramo**, agregar hasta 2 divisiones por curva para definir subintervalos (cada curva puede tener divisiones distintas).
6. En modo **Colocar nodos**, hacer clicks sobre cada curva. Se requieren al menos 2 nodos por cada tramo definido para esa curva.
7. Pulsar **CALCULAR AREA**.
8. (Opcional) Pulsar **Ver graficas** para revisar interpolacion y zona integrada.

Nota:

- Las coordenadas mostradas al mover el mouse estan en pixeles.
- El resultado se reporta en `px^2`.
- El area total se calcula como suma por subintervalos comunes entre `f` y `g`.

## Guia de uso de la UI - Parte 2

1. Abrir `parte2.py`.
2. Pulsar **Cargar imagen**.
3. Antes de poner nodos, en modo **Fijar limites en imagen**, marcar `a,b,c,d` como referencia visual.
4. Seleccionar curva activa:
   - `C1 exterior (azul)`,
   - `C2 interior (rojo)`.
5. En modo **Colocar nodos**, marcar nodos alrededor de cada curva cerrada.
6. Elegir metodo:
   - **Lagrange por trozos**
   - **Shoelace (poligonal)**
7. Pulsar **CALCULAR AREA**.
8. Leer:
   - `Area C1`,
   - `Area C2`,
   - `Area entre curvas = |Area C1 - Area C2|`.
9. (Opcional) **Ver graficas** para inspeccion visual.

Notas:

- Se necesitan al menos 3 nodos por curva cerrada.
- Conviene mantener orden consistente al marcar nodos.
- El resultado se reporta en `px^2`.
