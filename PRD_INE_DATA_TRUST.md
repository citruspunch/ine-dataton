# PRD: INE Data Trust, validación técnica del prototipo

**Nombre de trabajo:** INE Data Trust. No implica certificación, aprobación ni adopción por el INE.
**Categoría:** 2, Tecnológica y ciencias de datos, Datatón INE 2026.
**Versión:** 1.0, documento de producto y pitch. No describe código implementado.
**Fecha:** 23 de noviembre de 2026.

---

## 1. Decisión

**GO condicionado a INE Data Trust recortado.** El producto valida agregados oficiales ya publicados, con tres familias P0, una ficha, un recibo y un gate humano. No calcula cifras nuevas, no corrige, no publica en CKAN y no certifica.

La apuesta es deliberada: proteger funcionalidad y aplicabilidad institucional antes que amplitud. La rúbrica da 25 puntos a funcionalidad y 20 a aplicabilidad, que desempata. Un prototipo pequeño que se demuestra completo rinde más que una ambición a medio terminar.

**Condiciones de GO:** tres P0 demostrables; críticas evaluadas y aprobadas; licencia comprobada; advertencias justificadas; gate humano; demo sin red en segunda máquina; ninguna promesa de certificación, adopción o rendimiento no medido.

**Si una P0 falla:** se reduce el alcance y se declara la cobertura. No se pivota a Canasta o DINESE el 25 de noviembre. Un cambio tardío de producto es más riesgoso que un alcance pequeño bien explicado.

---

## 2. Contexto oficial y rúbrica

### 2.1 Reglas que condicionan el producto

| Tema | Regla oficial | Implicación |
|---|---|---|
| Categoría, equipo y exposición | Categoría 2; 3 a 4 integrantes; 7 minutos y 3 de preguntas; PDF y video de 2 a 3 minutos | Herramienta funcional, no infografía; guion breve y video de respaldo |
| Fechas | Apertura 23, desarrollo 24 y 25, entrega 26 a las 09:00, final 27 | No hay espacio para una segunda arquitectura |
| Repositorio y desarrollo | Repo Git desde el día 1, acceso para el jurado, desarrollo durante el evento, historial como evidencia; descalificación por proyecto previo | No reutilizar trabajo previo sin aclarar elegibilidad; no alterar historial |
| README y datos | Problema y usuarios, arquitectura, instalación, dependencias, datos INE y fecha de descarga, limitaciones, licencias, IA, pagos y nube | El README es parte del producto; fuente y fecha visibles |
| Seguridad | Secreto estadístico; no identificar personas, hogares o empresas; sin credenciales | Solo agregados publicados y fixtures sintéticos |
| Propiedad intelectual | Licencia institucional no exclusiva, gratuita, perpetua e irrevocable; autoría y licencias de terceros conservadas | Código MIT; los datos conservan su licencia |

La Nota Conceptual indica 09:00 sin zona horaria. Se opera como hora de Guatemala y se confirma con la organización.

### 2.2 Rúbrica: seis criterios, fórmula y tradeoff

| Criterio | Peso | Qué demuestra | Evidencia observable de éxito | Puntos por nivel |
|---|---:|---|---|---:|
| Funcionalidad y estabilidad | 25 | La herramienta funciona, cumple lo que propone y no falla en demo | Tres P0 con casos positivos y negativos; demo offline; tests reproducibles | 5 |
| Aplicabilidad institucional | 20 | Responde a una necesidad real y es adoptable | Revisor de publicaciones; procedimiento 18 del manual de Informática; piloto en sombra | 4 |
| Calidad técnica | 20 | Código, arquitectura, reproducibilidad y documentación | Separación revisión y snapshot; reglas versionadas; segunda máquina; perfiles declarativos | 4 |
| Innovación | 15 | Originalidad del enfoque o del uso de tecnología | Recibo de evidencia, gate humano y bloqueo de comparación, no un dashboard | 3 |
| Rigor en el uso de datos | 10 | Interpretación correcta de indicadores y metadatos | Bloqueo IPC, fuentes, base, periodo, unidad, límites y lenguaje sin sobreafirmar | 2 |
| Presentación y usabilidad | 10 | Claridad, experiencia y facilidad de uso | Demo de 7 minutos; ficha legible; prueba con 2 a 3 personas externas | 2 |
| **Total** | **100** | | | **20** |

Fórmula con ponderaciones en puntos:

```
Total = suma(peso_del_criterio * nota_del_criterio / 5)
```

Comprobaciones: todos 3 dan 60; todos 4 dan 80; todos 5 dan 100. Una caída de un nivel en funcionalidad cuesta 5 puntos; una subida de un nivel en innovación gana 3. La diferencia es 2. Aplicabilidad vale 4 por nivel y define el empate. No se publica un total estimado ni se promete 96 o ganar.

---

## 3. Evidencia base y límites

### 3.1 Tabla única de evidencia

| Evidencia | Estado | Fuente | Uso |
|---|---|---|---|
| Reglas del evento, rúbrica, repo desde el día 1, desarrollo durante el evento y descalificación | Oficial | Nota Conceptual, pp. 2 a 6; repo y desarrollo p. 5; descalificación p. 6 | Alcance y elegibilidad |
| IPC: `ipc_emprepu_es25.xlsx`, `Hoja2`, filas 503 y 504, descargado 23/11/2026 (UTC). F503 100,513540673814; F504 101,017579223309; E503 101,702855111367; G504 0,5014633313243735%. `((F504/E503) - 1) × 100` da -0,67380201598825%; `((F504/F503) - 1) × 100` da 0,501463331324387%. SHA-256 `d0101e366ee6d6bb02345db64b8c725c0a4c65ee85aa800d751d41b8381664d4`, 68.016 bytes. | Verificado directamente | XLSX oficial en `https://datos.ine.gob.gt/dataset/4243818d-b479-4bc1-aae6-2735e2b51265/resource/6b2cb40a-188c-47c9-9288-ba11c40b5910/download/ipc_emprepu_es25.xlsx`; boletín oficial `https://www.ine.gob.gt/sistema/uploads/2025/02/17/20250217134535ulH0ZxgvNe7JAdGEk3G7GzRiFrDmXFWf.pdf`, pp. 5 y 37 | P0.3 y demo |
| IPC: las fichas de 2024 y 2025-2026 declaran `cc-by` | Verificado en metadatos | `package_show` de ambos conjuntos CKAN | Licencia y atribución |
| Duplicado: `resource_show` de `5d304a4c-f7e4-473e-8b89-9078fe3dbf9e` (Divorcios) y `f529942a-c3bb-4de9-818f-8ac67c70d47a` (Matrimonios) corrobora etiqueta, tamaño y URL; muestras locales de 6.554.874 bytes y SHA-256 `cd5c94f572ab9ed3e718892fcb0d1ee85087ca4271555292394ecd35d412d3d8` | Verificado localmente; bytes remotos no | `resource_show`; `discovery_ine/samples/continuas_alimentaria/`; `discovery_ine/research/continuas_alimentaria/HALLAZGOS.md:87-90`; `verified_urls.json:598-608` | Solo fixture sintético; no demo con microdatos |
| Canasta Viva: 20,17% de hogares bajo CBA y Q1.148,9 millones/mes de brecha; 20 códigos ENIGH `0118` a `0138` sin `0133`, 82,1% del peso del departamento de Guatemala | Reproducido localmente; simulación | `discovery_ine/research/canasta_base/feasibility_summary.json`; `discovery_ine/tools/feasibility_affordability.py`; `discovery_ine/INVENTARIO_DATOS_INE.md:285,445-446`; metodología ENCOVI | Comparación, no producto |
| DINESE: 312.923 a 645.431 registros (+106,26%); 340 pares departamento-municipio en muestras | Reproducido localmente; cambio observado de registros | `discovery_ine/research/dinese/HALLAZGOS.md`; muestras DINESE | Comparación; no insumo |
| +21: 16 pares históricos `102` a `117` frente a `0123` a `0138`; 2.091.689 personas censadas en 2018 de 14.901.286 (14,04%); proyección 2018 de esos 16 pares: 2.253.553 | Reproducido localmente; alias y crosswalk | `discovery_ine/research/censos_geo/crosswalk_codigos.csv`; `HALLAZGOS.md:47-55`; diccionario de proyecciones | Backlog; no demo |
| HBA: 28.183.196 frente a 14.091.597 toneladas en una hoja de 83 filas y 18 grupos | Reproducido localmente; diferencia artificial al combinar niveles | `discovery_ine/research/continuas_alimentaria/HALLAZGOS.md` | Backlog; no demo |
| Catálogo CKAN: 105 conjuntos y 876 recursos; 50 CC BY, 22 ODC BY, 33 sin licencia declarada | Verificado en catálogo | `package_search` y metadatos CKAN; `discovery_ine/INVENTARIO_DATOS_INE.md` | Denominadores y gate de licencias |
| Procedimiento 18: recepción, verificación de formato y publicación; pp. impresas 106 a 109 | Verificado en PDF; vigencia 2026 pendiente | Manual de procesos de la Dirección de Informática del INE, `https://www.ine.gob.gt/sistema/uploads/2022/11/04/20221104213159eHmz6DmFKboNQ5Y3OlqNkbi9izmXULaP.pdf` | Punto de integración del recibo |
| Ley y Reglamento del INE, arts. 25 y 26: confidencialidad y responsabilidad; no hay k=5 legal automático | Verificado en PDF descargado | `https://www.ine.gob.gt/ine/wp-content/uploads/2022/01/Ley_Reglamento_INE_dic21.pdf` | Límite legal y privacidad |
| Referencias externas: SingStat MCP como ejemplo de acceso; INEGI Sistema de Difusión de Metadatos como referencia de metadatos; GSBPM 5.2, 5.3, 6.2, 6.3 y 7; SDK de MCP para Python con stdio y respuestas estructuradas | Referencia conceptual, no aval | `https://www.singstat.gov.sg/data-tools-services/singstat-mcp`; `https://www.inegi.org.mx/app/sdm/`; `https://unece.github.io/GSBPM-5.2/`; documentación del SDK de MCP para Python | Diseño y encaje; no conformidad formal |

### 3.2 Límites que el pitch debe respetar

- 105 conjuntos y 876 recursos son denominadores, no una tasa de disponibilidad. 50 + 22 + 33 = 105. En el registro local, 3 recursos SharePoint devolvían HTML pese a HTTP 200 y uno devolvió 403 en una comprobación puntual. No se reejecutaron los 876 y no hay 100% de formatos ni de disponibilidad.
- El hash prueba igualdad de bytes del par observado. No prueba autoría, origen, licencia, causalidad ni calidad.
- +21 no son personas perjudicadas. Son personas censadas en 2018; la proyección es otra cifra. Faltan nombres, departamento, vigencia y correspondencia bidireccional. No se aplica una corrección global ni se afirma que los códigos oficiales sean erróneos.
- Canasta Viva es una simulación, no una tasa de pobreza. La ENCOVI oficial usa agregado de consumo, no un titular modelado. La ENIGH no es representativa a nivel municipal y los códigos no canónicos no son error probado sin diccionario.
- DINESE es un cambio observado de registros, no crecimiento de empresas ni causa de cobertura demostrada solo por conteo. No hay panel de empresas ni CIIU a 4 dígitos.
- HBA 28.183.196 frente a 14.091.597 toneladas es una diferencia artificial al combinar niveles. No es una acusación.
- La frase de diapositiva sobre validación con automatización de licencia libre es una referencia del usuario, no una fuente verificada. No se usa como aval en el pitch.

---

## 4. Comparación de opciones

| Opción | Problema y usuarios | Viabilidad | Aplicabilidad institucional | Riesgo de interpretación | Demo | Lectura |
|---|---|---|---|---|---|---|
| Canasta Viva | Ingreso, CBA e IPC; alto impacto público | Media o baja: deflación, ponderadores, SAE, representatividad municipal | Media | Alto: simulación, no pobreza; IPC no actualiza ingreso observado | Mapa y ficha de hogar, fácil de sobreinterpretar | Buena idea para otro contexto; no es la apuesta de menor riesgo |
| INE Data Trust | Revisor de publicaciones; periodista o analista que necesita fuente, base y periodo | Alta si se recorta a tres P0 y UI simple | Alta: control antes de difundir; procedimiento 18 documentado en 2022 | Medio: se controla con estados, fixtures y gate | Menos vistosa, pero concreta: se bloquea, se muestra ficha, queda recibo | **Recomendada** |
| Data Trust + MCP | Igual, más cliente local de lectura | Media: integración y pruebas | Alta si el INE valora acceso programático; no es requisito | Medio: riesgo técnico y de alcance | Demostración técnica breve; no reemplaza el caso IPC | P1 condicionado, no MVP |
| DINESE Territorial | Vitalidad empresarial municipal | Media: sin CIIU a 4 dígitos, sin ID de empresa, salto de registros | Media o alta para difusión | Alto: el salto se puede leer como crecimiento | Muy visual, con serie difícil de defender | Alternativa solo si falla Data Trust y hay evidencia alternativa |

**Recomendación:** Data Trust recortado. La necesidad es concreta, la evidencia se puede demostrar y el gate humano evita el riesgo de certificar. Canasta tiene mejor relato ciudadano y más riesgo metodológico. DINESE tiene mejor imagen y más riesgo longitudinal. MCP aporta si el núcleo ya funciona; no antes.

---

## 5. Producto: problema, usuarios y límites

**Problema y usuarios:** un agregado candidato puede parecer correcto y no ser comparable con su versión oficial por base, periodo, unidad, esquema, identidad o licencia. El usuario primario es un técnico de publicaciones que lo revisa al lado de la ficha oficial; el secundario es un periodista o analista que necesita fuente, base, periodo y una negativa clara cuando se le pide comparar bases distintas.

**Propuesta, no objetivos y lenguaje:** validar un agregado contra su ficha, ver reglas, cobertura y advertencias, y exportar un recibo reproducible. No certifica, no corrige, no publica en CKAN, no procesa microdatos, no ofrece SQL o URL libre, no produce un score de 0 a 100 y no es un chatbot ni un monitor. Se dice "Validación técnica del prototipo", "Habilitado para consulta en el prototipo", "No comparable directamente", "Requiere revisión del productor" y "No evaluado"; no se dice "certificado", "aprobado por el INE" ni "dato confiable" como veredicto.

---

## 6. Alcance del MVP

### 6.1 Principios

Solo agregados oficiales publicados y fixtures sintéticos rotulados; lista cerrada, sin URL libre, SQL, carga de archivos ni agregación libre; sin red después de preparar el snapshot; estado, severidad y cobertura, sin puntaje productivo; sin corrección automática; cierre por defecto si falta evidencia o permiso. La única base real necesaria es el XLSX oficial de IPC; esquema e identidad usan fixtures.

### 6.2 P0.1 Contrato de esquema, tipo, grano y fechas

Valida columnas requeridas, tipos, granularidad, rango de fechas, periodo, unidad y base contra un contrato declarado. El alcance es un CSV sintético y un XLSX sintético de una hoja y encabezado conocido; no se requiere un segundo recurso real.

`falla` si falta una columna, el tipo no parsea, el grano se duplica, la fecha es inválida, el periodo se mezcla o la hoja no es la declarada (con `expected_sheet` y `observed_sheets`); `advertencia` si la diferencia no impide el uso; `no_evaluado` solo si el archivo es ilegible o falta el contrato, no ante una discrepancia clara.

### 6.3 P0.2 Identidad por SHA-256

Detecta dos recursos con el mismo SHA-256 y identidad semántica incompatible: dataset, título, periodo, base, unidad o grano distintos. Por defecto es `falla` y "requiere revisión"; una reutilización intencional solo pasa a `advertencia` con política documentada, dueño, fecha, motivo y gate humano. El hash prueba igualdad de bytes del par observado, no autoría, origen ni calidad. El caso real de divorcios y matrimonios es microdato y no se muestra; la demo usa un fixture sintético con los mismos bytes y etiquetas distintas.

### 6.4 P0.3 Comparabilidad del IPC

Valida mismo indicador, unidad, cobertura y serie, base y método compatibles. No exige "mismo periodo" para comparar meses diferentes ni "misma base" sin más; para una variación mes a mes, los periodos deben ser solicitados y contiguos. El cambio de base es un hecho metodológico, no un error.

Caso real: `ipc_emprepu_es25.xlsx`, `Hoja2`. F503 y F504 son el par comparable de la misma serie F, diciembre 2024 y enero 2025; G504 es la variación mensual publicada, +0,50%, y se muestra desde G504, no se calcula como función de difusión. La fórmula inválida `(F504/E503 - 1) × 100 = -0,67%` se bloquea y no se muestra en la ficha de consulta. No se construye un empalme propio: si se cruzan bases, se usa la serie empalmada oficial. No se aproxima pobreza ni se usa el IPC para actualizar ingreso nominal observado.

### 6.5 P1 MCP

MCP es una capa de lectura local, no un producto aparte. Una herramienta tipada sobre el snapshot reducido y el mismo contrato de la ficha y el JSON. Sin escritura, sin consulta remota, sin chat, sin IA y sin acceso a la carpeta de revisión.

Decisión el 25 de noviembre a las 12:00: solo si las P0 están verdes, la demo offline funciona y queda tiempo. Si no, se retira sin afectar la entrega. No es requisito.

### 6.6 Fuera del MVP

REST o FastAPI; monitor exhaustivo de CKAN; integración o publicación; dashboard o score complejo; microdatos, PNC, defunciones, ENIGH a nivel de hogar o DINESE a nivel de registro; URL libre, SQL genérico o agregación libre; +21, HBA, salto DINESE y ranking CKAN; promesas de 2 segundos. Piloto y formatos extra no son requisitos de aceptación.

---

## 7. Arquitectura, gate y recibo

### 7.1 Dos almacenes separados

```
review_store/                      public_snapshot/
  candidatos                         solo agregados permitidos
  fixtures                           licencia verificada
  recibos privados                   gate humano: visto bueno local
  decisiones                         ficha, JSON y MCP de lectura
        \__________________________/
              gate humano
```

`review_store/` es local y privado. Contiene candidatos, fixtures, recibos privados y bitácora de decisiones. `public_snapshot/` es reducido y solo recibe agregados permitidos después de la confirmación humana. La ficha pública y el JSON comparten el mismo contrato de lectura; MCP, si existe, lee ese snapshot y nunca el motor, la carpeta de revisión ni los candidatos. No hay credenciales ni escritura externa.

### 7.2 Componentes

Componentes: preparación de snapshot con lista cerrada, URL, fecha UTC, bytes, SHA-256 y perfil; motor de reglas declarativas versionadas con ID, severidad, cobertura y mensaje; almacén local de revisión y snapshot reducido; generador de ficha y recibo; CLI para validar y exportar; UI simple para revisar y consultar; adaptador MCP P1 de solo lectura.

### 7.3 Gate humano

El gate exige todas las reglas críticas evaluadas y en `ok`, licencia comprobada, toda advertencia justificada con dueño y motivo, y constancia local del visto bueno del productor y del revisor de publicaciones, sin prometer firma criptográfica ni autenticación. El [procedimiento 18](https://www.ine.gob.gt/sistema/uploads/2022/11/04/20221104213159eHmz6DmFKboNQ5Y3OlqNkbi9izmXULaP.pdf), pasos 4 a 6, documenta que producción revisa y aprueba, el técnico auxiliar verifica formato y publica; el recibo se adjunta al ticket de forma propuesta y su vigencia debe verificarse. La decisión se liga a un digest:

```
decision_basis_digest = SHA-256(canonical(
  hashes de archivos + versión de perfil + versión de reglas + hallazgos
))
```

Si cambia un archivo, el perfil, la versión de reglas o un hallazgo, el digest cambia y la decisión se invalida. Los timestamps de ejecución y de decisión no entran en el digest. La bitácora de decisiones es separada y guarda fecha, responsable y motivo.

### 7.4 Estados

| Estado | Condición | Texto visible |
|---|---|---|
| `borrador` | Snapshot o ficha incompletos | "Borrador, no consultable" |
| `no_habilitado` | Falla crítica o crítica no evaluada | "No habilitado para consulta" |
| `en_revision` | Sin fallas críticas; advertencias o gate pendiente | "En revisión" |
| `habilitado_para_consulta` | Críticas evaluadas y aprobadas, licencia y gate | "Habilitado para consulta en el prototipo" |
| `cerrado` | Licencia, permiso o evidencia insuficiente | "Cerrado por defecto" |

No existe "aprobado por el INE". La habilitación es del prototipo.

### 7.5 Recibo

El recibo separa payload técnico y bitácora:

```
technical_payload: snapshot_id, source_id/resource_id, period/base/unit,
source_url/downloaded_at_utc, sha256, profile_version, rules_version,
findings[], coverage, state
decision_log: decided_at_utc, operator, rationale, gate_decision
```

El digest de validación se calcula sobre datos, contrato, perfil, reglas y hallazgos. No se auto-hashea el recibo completo con el campo de hash incluido. Los timestamps de ejecución y decisión quedan fuera del digest técnico. Dos ejecuciones del mismo snapshot y reglas producen el mismo digest técnico.

---

## 8. Datos, fixtures, licencias y privacidad

### 8.1 Lista cerrada

Lista cerrada: XLSX oficial de empalme del IPC por República, `ipc_emprepu_es25.xlsx`, `Hoja2`, filas 503 y 504; CSV sintético y XLSX sintético de una hoja para contrato; fixture de duplicado con identidad incompatible y fixture con excepción documentada.

No se incluye un segundo recurso real. Si hay recorte, se conserva el XLSX oficial de IPC; nunca se sustituye el único dataset INE por fixtures.

### 8.2 Licencias

El código usa MIT, igual que `LICENSE`; esa licencia no cubre datos. Las fichas de IPC 2024 y 2025-2026 declaran `cc-by`: se atribuye al INE y se respetan versión y términos. La licencia no se extiende a otros productos. Si falta licencia, el recurso se cierra o se revisa permiso; no se asume redistribución. Antes de prometer offline real, se confirma que el snapshot se puede distribuir o se prepara localmente.

### 8.3 Privacidad

Solo agregados publicados. No se muestran microdatos, filas de divorcios o matrimonios ni datos de PNC o defunciones. No se suben archivos a servicios públicos, no se aceptan consultas libres y los logs no guardan contenido sensible. n<5 solo se considera en una actividad posterior sobre sintéticos; es un supuesto configurable, no una norma legal. No se afirma que el prototipo garantice secreto estadístico: los subtotales y distintos cortes pueden permitir inferencias.

---

## 9. Requisitos y aceptación

| ID | Requisito | Aceptación medible |
|---|---|---|
| FR-01 | Separar revisión privada y snapshot público | MCP y ficha pública no pueden leer `review_store/`; el snapshot solo contiene la lista permitida |
| FR-02 | Contrato CSV y XLSX | CSV sintético positivo pasa; columna faltante, tipo incorrecto, grano duplicado o fecha inválida fallan |
| FR-03 | Hoja inesperada | XLSX con hoja distinta a la declarada falla con `expected_sheet` y `observed_sheets`; no se confunde con `no_evaluado` |
| FR-04 | Identidad SHA-256 | Mismos bytes con identidad incompatible fallan; excepción documentada pasa a advertencia con gate |
| FR-05 | Comparabilidad IPC | F503 y F504 pasan; G504 se muestra como +0,50%; F504/E503 falla con `(F504/E503 - 1) × 100`; no se muestra el número inválido en ficha pública |
| FR-06 | Estados y severidad | Falla, advertencia y no evaluado son visibles; crítica no evaluada bloquea |
| FR-07 | Gate y digest | Sin críticas aprobadas, licencia y advertencias justificadas no hay habilitación; cambio de archivo, perfil o reglas invalida la decisión |
| FR-08 | Ficha y recibo | Ficha con fuente, recurso, periodo, base, unidad, URL, fecha UTC, hash, perfil y reglas; digest técnico repetible sin timestamps y bitácora separada |
| FR-09 | CLI y UI | Lista cerrada, ficha, estados y exportación; sin login, URL libre ni SQL |
| FR-10 | Fixtures | Cada fixture se rotula como sintético y declara el caso que demuestra |
| FR-11 | Licencia y privacidad | Sin licencia no se habilita; sin microdatos, PII ni logs sensibles |
| FR-12 | MCP P1 | Una herramienta de lectura, mismo contrato que ficha y JSON; sin escritura ni acceso a revisión |
| FR-13 | Mantenibilidad y rendimiento | Un segundo perfil declarativo o test por configuración sin tocar el motor; tiempo y memoria medidos, sin promesa de 2 segundos |

Casos críticos: CSV correcto `ok`; columna faltante o grano duplicado `falla`; hoja inesperada `falla`; hash incompatible `falla`; excepción documentada `advertencia`; IPC F503 y F504 `ok` y G504 +0,50%; F504/E503 `falla` y -0,67% solo en revisión; crítica no evaluada `no_habilitado`; licencia ausente `cerrado`; cambio de digest invalida la decisión; dos ejecuciones dan el mismo digest; offline da el mismo resultado; MCP no accede a revisión ni muta.

### 9.1 Usabilidad, piloto y mantenibilidad

**Usabilidad:** 2 a 3 personas fuera del desarrollo, cinco tareas: ubicar fuente y fecha, identificar base y periodo, decidir comparabilidad, exportar recibo y explicar "no evaluado". Criterio: mayoría de participantes completa sin ayuda. Si no se ejecuta, se declara "prueba no ejecutada" y no se reportan resultados.

**Piloto en sombra:** 1 producto, 2 ciclos. Comparación emparejada manual contra herramienta, con las mismas tareas y criterios. No se confía solo en una encuesta. Se mide tiempo de revisión, comparaciones inválidas bloqueadas, falsos positivos y reglas no evaluadas. Es posterior al evento y no requisito de entrega.

**Mantenibilidad:** se demuestra con dos perfiles o identidades declarativas, o con un test que ajuste perfil y columna por configuración sin cambiar el motor. No se agrega una función nueva.

---

## 10. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Evidencia o licencia insuficiente | Alto | Cerrar el recurso; revisar permiso; no convertir un límite en hecho |
| Alcance excesivo | Alto | Tres P0, lista cerrada, sin monitor |
| El cambio de base IPC se presenta como error | Alto | Lenguaje metodológico; bloquear; no empalmar |
| El producto se percibe como certificador o se sobreafirma adopción | Alto | "Validación técnica", gate humano, piloto en sombra; sin inventar resultados |
| MCP consume tiempo | Medio | P1 con deadline 25 a las 12:00; se retira sin afectar P0 |
| La demo depende de red | Alto | Snapshot offline, segunda máquina y video |
| Un falso positivo erosiona la confianza | Medio | Severidad, evidencia y revisión humana |
| n<5 se presenta como garantía legal | Alto | Supuesto configurable; declarar riesgo de inferencia |

---

## 11. Plan, división de trabajo y gates

| Fecha | Trabajo | Salida |
|---|---|---|
| 23 de noviembre | Repo, alcance, lista cerrada, fixtures, contrato CSV | Esqueleto y P0.1 en fixtures |
| 24 de noviembre | P0.2, P0.3, motor, UI mínima, recibo, tests | Tres P0 demostrables |
| 25 de noviembre, 12:00 | Decisión MCP | P1 sí o no, sin tocar P0 |
| 25 de noviembre, 18:00 | Congelamiento | Solo correcciones |
| 26 de noviembre, 09:00 | Entrega | Repo, PDF y video |
| 27 de noviembre | Presentación | 7 minutos y 3 de preguntas |

| Rol | Responsabilidad |
|---|---|
| Producto y evidencia | Alcance, gate, pitch, README, relación con mentores |
| Motor y reglas | Reglas declarativas, recibo, tests, determinismo |
| UI y demo | Ficha, CLI, video, guion, usabilidad |
| Datos y QA, si hay cuarta persona | Snapshot, licencias, segunda máquina, riesgos |

Con tres personas, datos y QA se reparten entre producto y UI. Nadie acumula la aprobación y la validación en la misma persona.

**Gates de recorte:** si el 23 no hay repo, manifiesto y contrato, se reduce la UI a CLI y ficha exportable. Si el 24 no hay tres P0, se retira MCP y se reduce la UI. Si el 25 a las 12:00 no hay offline en segunda máquina, se congela el alcance y se graba el video con lo que funcione.

---

## 12. Pitch de 7 minutos, Q&A y entrega

### 12.1 Guion

**0:00 a 0:50. Abrir con el bloqueo IPC.**
"Este es el XLSX oficial de empalme del INE. En la pantalla de revisión, si mezclo F504 con E503, el resultado es -0,67%. Ese número no es oficial: es una comparación inválida entre bases. La regla la bloquea y la ficha de consulta no lo muestra. La fila correcta es F503 y F504, y la variación publicada está en G504: +0,50%. El prototipo no calcula un empalme nuevo."

**0:50 a 1:40. Usuario y promesa.**
"El usuario es un revisor técnico de publicaciones. Tiene un agregado candidato al lado de la ficha oficial. Necesita saber si el contrato se cumple, si la comparación es válida y qué falta. No le damos un score. Le damos estado, severidad, cobertura y un recibo. No certifica, no corrige y no publica."

**1:40 a 2:40. Ficha y recibo.**
"La ficha muestra fuente, base, periodo, unidad, hash y fecha UTC. El recibo separa payload técnico y bitácora. El digest no incluye timestamps de ejecución ni de decisión. Si cambia el archivo, el perfil o las reglas, la decisión se invalida."

**2:40 a 3:30. Fixture breve de contrato.**
"Este CSV sintético tiene una columna faltante y grano duplicado. La regla falla, la ficha muestra el campo y el valor observado, y el estado queda no habilitado. No se corrige el archivo."

**3:30 a 4:20. Identidad.**
"Estos dos fixtures tienen el mismo SHA-256 y etiquetas distintas. El hash prueba igualdad de bytes, no autoría. La regla pide revisión. La excepción documentada pasa a advertencia y sigue por el gate humano."

**4:20 a 5:20. Gate y separación.**
"La revisión vive en una carpeta privada con candidatos y fixtures. El snapshot público solo recibe agregados permitidos después de la confirmación humana. La ficha y el JSON leen el mismo contrato. MCP es P1: solo se muestra si está probado y, si existe, lee el snapshot público, nunca la carpeta de revisión."

**5:20 a 6:20. Arquitectura y reproducibilidad.**
"Todo corre local, sin red después de preparar el snapshot. Python, reglas declarativas y UI simple. Sin API, sin base separada, sin consulta libre. La demo se reproduce sin red en el equipo de demo; la segunda máquina es un criterio de aceptación y solo se afirma si se probó. El video es el respaldo. MCP y segunda máquina no se presumen."

**6:20 a 7:00. Límites y pregunta.**
"No somos un certificador, un publicador ni un dashboard. Buscamos un piloto en sombra con un revisor de publicaciones para medir tiempo y comparaciones inválidas evitadas. ¿Qué producto y qué flujo deberíamos probar primero?"

### 12.2 Q&A breve

| Pregunta | Respuesta |
|---|---|
| ¿Certifica datos o corrige cifras? | No. Validación técnica con gate humano; marca y bloquea, no corrige ni publica. |
| ¿Por qué no un score? | Un score oculta cobertura y severidad. Mostramos estado, severidad y cobertura. |
| ¿Qué pasa si una regla no se evaluó? | Si es crítica, no se habilita. |
| ¿De dónde salen los datos? | Del XLSX oficial de IPC y fixtures sintéticos, con URL, fecha UTC, hash, ficha y licencia CC BY con atribución. |
| ¿MCP es un chatbot? | MCP es una propuesta P1, no un chatbot: si se implementa, sería una herramienta de lectura local, sin IA y sin acceso a revisión. |
| ¿Por qué no Canasta o DINESE? | Canasta es simulación, no pobreza; DINESE tiene un salto de registros que no se explica solo por el conteo. |
| ¿Cómo se adopta? | Como recibo adjunto al ticket de publicación, según el procedimiento 18, con piloto en sombra. |

### 12.3 Lista de entrega

- Repo Git nuevo, acceso para el jurado, historial intacto.
- README con problema, usuarios, arquitectura, instalación, dependencias, datos y fecha, limitaciones, licencias, IA, pagos y nube; sin credenciales ni datos personales.
- LICENSE MIT y avisos de terceros.
- Snapshot con lista cerrada y manifiesto UTC, bytes, SHA-256 y perfil.
- Tres P0, fixtures rotulados, ficha y recibo.
- Gate y bitácora de decisiones.
- Tests positivos, negativos, determinismo, offline, rendimiento medido y MCP P1 si aplica.
- PDF, video de 2 a 3 minutos, guion y Q&A.

---

## 13. Mentoría y fuentes

### 13.1 Preguntas

1. ¿Cuál es el flujo real de revisión y quién decide antes de difundir?
2. ¿Qué producto y qué publicación conviene para el piloto en sombra?
3. ¿El procedimiento 18 sigue vigente? ¿Quién es el dueño actual y el Técnico Auxiliar?
4. ¿Quién es el productor del IPC y qué perfil revisa la ficha?
5. ¿La serie empalmada oficial a nivel República, división o región cubre el uso previsto?
6. ¿Qué política existe para recursos duplicados de forma intencional?
7. ¿Un cliente MCP local y de solo lectura sería útil o distrae?
8. ¿Qué métrica de éxito tendría el piloto: tiempo, comparaciones bloqueadas, claridad?

### 13.2 Fuentes

- Nota Conceptual Datatón INE 2026, pp. 2 a 6. Repo y desarrollo p. 5; descalificación p. 6.
- XLSX de empalme del IPC: `https://datos.ine.gob.gt/dataset/4243818d-b479-4bc1-aae6-2735e2b51265/resource/6b2cb40a-188c-47c9-9288-ba11c40b5910/download/ipc_emprepu_es25.xlsx`.
- Boletín del IPC de enero de 2025, PDF descargado, pp. 5 y 37.
- CKAN, IPC 2024 y 2025-2026; `package_show` con licencia `cc-by`.
- `discovery_ine/research/canasta_base/feasibility_summary.json`; `discovery_ine/tools/feasibility_affordability.py`; `discovery_ine/INVENTARIO_DATOS_INE.md:285,445-446`.
- `discovery_ine/research/continuas_alimentaria/HALLAZGOS.md:87-90`; `verified_urls.json:598-608`; muestras locales.
- `discovery_ine/research/censos_geo/crosswalk_codigos.csv`; `HALLAZGOS.md:47-55`.
- `discovery_ine/research/dinese/HALLAZGOS.md`; `discovery_ine/research/continuas_alimentaria/HALLAZGOS.md`.
- Manual de procesos de la Dirección de Informática del INE: `https://www.ine.gob.gt/sistema/uploads/2022/11/04/20221104213159eHmz6DmFKboNQ5Y3OlqNkbi9izmXULaP.pdf`, procedimiento 18, pp. 106 a 109.
- Ley y Reglamento del INE: `https://www.ine.gob.gt/ine/wp-content/uploads/2022/01/Ley_Reglamento_INE_dic21.pdf`, arts. 25 y 26.
- Metodología ENCOVI: `https://www.ine.gob.gt/wp-content/uploads/2024/09/2.-Metodologia-de-medicion-de-pobreza-en-GT.pdf`.
- SingStat MCP: `https://www.singstat.gov.sg/data-tools-services/singstat-mcp`.
- INEGI Sistema de Difusión de Metadatos: `https://www.inegi.org.mx/app/sdm/`.
- GSBPM 5.2: `https://unece.github.io/GSBPM-5.2/`.
- SDK de MCP para Python: `https://github.com/modelcontextprotocol/python-sdk`.
