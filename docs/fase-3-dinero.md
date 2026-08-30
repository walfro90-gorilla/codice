# Fase 3 — Dinero

Estado: **presupuesto federal cargado** (30 de agosto de 2026). Serie 2024–2026 del Presupuesto de Egresos de la Federación, agregada por ramo y entidad, conectada a la estructura de la Fase 1.

## Qué contiene

| Año | Filas del archivo original | Total aprobado |
|---|---|---|
| 2024 | 149,510 | 10.41 billones de pesos |
| 2025 | 151,647 | 10.80 billones de pesos |
| 2026 | 129,945 | 11.75 billones de pesos |

51 ramos presupuestarios, de los cuales 41 están vinculados a un nodo de la estructura. 2,766 asignaciones (año × ramo × entidad).

## Nunca el número solo

La métrica que pide el proyecto es **gasto por habitante**, y aquí no se publica sin lo que la hace interpretable. Las advertencias metodológicas no viven en este documento: viven en la tabla `metric_caveat`, viajan en el mismo `SELECT` que la cifra y se renderizan pegadas a ella. Un consumidor del API o de la interfaz no puede obtener el número sin obtener su advertencia.

La advertencia que más importa, y la razón de que exista el mecanismo:

> El PEF asigna el gasto a la entidad donde está domiciliada la unidad responsable, no donde se ejerce. Cerca de la mitad del gasto con entidad asignada se registra en la Ciudad de México por el domicilio de las oficinas centrales.

Sin ella, "Ciudad de México: 531,699 pesos por habitante" contra "Puebla: 30,206" invita a una conclusión falsa. El dato es correcto; la lectura ingenua no.

## El dinero sigue a la estructura

El ramo presupuestario es la clasificación administrativa con la que el PEF se organiza, así que es el puente natural entre el dinero y los órganos:

```sql
SELECT n.name, sum(b.amount_mxn)
FROM budget_allocation b JOIN ramo r ON r.id = b.ramo_id JOIN node n ON n.id = r.node_id
WHERE b.fiscal_year = 2026 GROUP BY n.name ORDER BY 2 DESC;
-- IMSS 1.59 billones · Pemex 708 mil millones · Bienestar 674 mil millones
```

**Qué ramo corresponde a qué órgano es una afirmación de Códice, no de la fuente.** Por eso vive curada en `data/ramos.yaml`, admite valor nulo y lleva nota. Diez ramos quedan deliberadamente sin vincular: deuda pública, participaciones, aportaciones federales y previsiones no son el gasto de un órgano, y forzarlos a uno diría algo falso sobre quién ejerce ese dinero.

## La extinción de un órgano, visible en el dinero

Como cada asignación lleva año, la serie muestra lo que un corte del presente escondería:

| Órgano | 2024 | 2025 | 2026 |
|---|---|---|---|
| IFT | 1,680 mdp | 500 mdp | — |
| INAI | 1,097 mdp | 500 mdp | — |
| COFECE | 688 mdp | 200 mdp | — |
| Comisión Reguladora de Energía | 286 mdp | 200 mdp | — |

Los ramos de estos órganos siguen existiendo en los años en que ellos existieron, y están vinculados a sus nodos extintos de la Fase 1. Esa es la razón de que el modelo temporal sea transversal (R9).

## Decisiones de volumen

El PEF publicado es detalle por partida: unas 130 mil filas **por año**. La base canónica guarda el agregado que responde la pregunta del proyecto —cuánto por ramo, por entidad, por año— porque conservar el detalle contable no aporta a esa pregunta y revienta el free tier justo en esta fase, como advierte el `CLAUDE.md`. El detalle completo queda en el snapshot crudo, íntegro y con hash, listo para reprocesarse o publicarse como Parquet estático cuando una consulta analítica lo exija (ADR-012).

## Verificación

La suma cargada se compara contra la suma directa de la columna del archivo original, y el cargador **se niega a completar** si difieren en más de un centavo. En las tres anualidades la diferencia es exactamente cero.

Ninguna celda quedó sin leer: el parser distingue el cero contable (`-`, campo vacío) de un valor que no supo interpretar, y reporta el conteo del segundo caso en vez de convertirlo a cero en silencio. Un presupuesto que pierde dinero al parsearse es peor que no tener presupuesto.

```bash
cd ingestion && python3 -c "from pathlib import Path; from codice_ingestion.pef import run; run(Path('snapshots'), Path('parsed'), years=[2024,2025,2026])"
cd ../normalization && .venv/bin/python -m codice_normalization budget ../data ../ingestion
```

## Cuenta Pública: lo aprobado frente a lo ejercido

La Cuenta Pública cierra el ciclo que el PEF abre. Ambas fuentes cargan en la misma tabla, distinguidas por etapa:

| Año | Aprobado | Modificado | Devengado | Pagado | Ejercido |
|---|---|---|---|---|---|
| 2024 | 10.41 | 10.56 | 10.56 | 10.51 | 10.55 |
| 2025 | 10.80 | 11.18 | 11.28 | 11.09 | 11.27 |

*Billones de pesos.* 2022 y 2023 están cargados pero la fuente no publica columna de ejercido para esos años; se registran las cuatro etapas que sí publica y ninguna más (R6). El ejercicio en curso no tiene cifra ejercida: la Cuenta Pública se publica al cierre.

**Dos figuras, ninguna conclusión.** El sistema muestra aprobado y ejercido lado a lado y la diferencia entre ambos, que es un hecho. No calcula porcentajes de cumplimiento ni califica la ejecución de nadie (R5, R2): el presupuesto puede modificarse legalmente durante el año, y gastar de más o de menos no es por sí mismo irregularidad ni ahorro. Eso viaja como advertencia junto a la cifra.

### Validación cruzada entre fuentes

El PEF y la Cuenta Pública publican, en archivos distintos, la misma cifra aprobada de un año cerrado. Los dos parsers coinciden **al peso**:

| Año | PEF | Cuenta Pública |
|---|---|---|
| 2024 | 10,406,689,047,769 | 10,406,689,047,769 |
| 2025 | 10,795,085,118,581 | 10,795,085,118,581 |

Dos archivos independientes leídos por dos rutas distintas dando el mismo número es la mejor evidencia disponible de que ninguno de los dos se está leyendo mal.

### Los nombres de columna cambian cada año

La Cuenta Pública no publica el mismo esquema dos años seguidos: 2024 escribe `MONTO_EJERCIDO`, 2025 escribe `" Ejercido_Bruto "` con espacios alrededor y renombra el ramo a `R`, y 2022–2023 no traen columna de ejercido. El archivo de 2022 además viene exportado desde Excel y **padeado hasta el límite de la hoja**: 828,067 filas completamente vacías después de las 220,508 con datos.

El parser resuelve cada encabezado contra una lista de variantes conocidas, salta las filas vacías **contándolas** y falla ruidosamente si no encuentra columna de monto. Nada de esto se descubrió leyendo documentación: se descubrió porque el snapshot crudo permite reprocesar sin volver a la fuente (R8).

## Huecos conocidos (R6)

- **Contrataciones**: ninguna fuente federal admite hoy acceso automatizado. Ver [hueco-contrataciones.md](hueco-contrataciones.md) para qué se probó, qué respondió cada una y cuáles son las vías institucionales. El cruce estrella del proyecto queda bloqueado en su primer eslabón.
- **Obra Pública Abierta**: identificada, no ingerida.
- **Ejercido de 2022 y 2023**: la fuente no publica esa columna para esos años. Se cargan las cuatro etapas que sí publica.
- **Presupuestos estatales y municipales**: no incluidos. El Ramo 33 y las participaciones muestran cuánto se transfiere, no en qué lo gastan las entidades.
- **Sin deflactar**: las comparaciones entre años son en pesos nominales. Convertirlas a pesos constantes exige el INPC del INEGI, aún no ingerido; mientras tanto la advertencia lo dice explícitamente.
- **Años 2020–2023**: publicados en la fuente y no descargados todavía; el ingestor los soporta pasando la lista de años.
