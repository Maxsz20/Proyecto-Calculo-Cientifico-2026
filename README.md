# Proyecto de Calculo Cientifico - Guia de uso

Este README contiene solo instrucciones de uso y consideraciones practicas de la aplicacion.

## Área entre dos curvas (funciones) - appFunciones.py

### Uso
1. Ejecutar `appFunciones.py`.
2. Cargar una imagen.
3. En modo **Fijar limites en imagen**, definir primero:
   - `a` (limite izquierdo),
   - `b` (limite derecho),
   - `c` (limite inferior),
   - `d` (limite superior).
4. Seleccionar la curva activa (`f` o `g`)
5. Si se desea, agregar divisiones de tramo
6. Colocar nodos sobre las curvas
7. Calcular area
8. Opcional: ver graficas

### Consideraciones
- Primero se deben definir los limites (`a, b, c, d`) dando click sobre la imagen y luego colocar nodos o divisiones
- Las divisiones son opcionales
- Si se colocan divisiones, deben marcarse sobre la curva correspondiente
- El area entre curvas se calcula solo donde ambas curvas quedan definidas por sus nodos (rango comun): desde el primer punto en x compartido hasta el ultimo punto en x compartido
- El resultado de area se muestra en `px^2`

## Área entre curvas cerradas (Relaciones) - appRelaciones.py

### Uso
1. Ejecutar `appRelaciones.py`
2. Cargar una imagen.
3. En modo **Fijar limites en imagen**, definir primero `a, b, c, d`
4. Seleccionar curva activa (`C1` o `C2`)
5. Colocar nodos sobre cada curva cerrada
6. Elegir metodo de calculo
7. Calcular area
8. Opcional: ver graficas

### Consideraciones
- Antes de colocar nodos, primero se deben fijar los limites en la imagen a modo de click
- El resultado de area se muestra en `px^2`
