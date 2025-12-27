# GovInsight: Sistema de Análisis de Contrataciones Públicas 

**GovInsight** es una solución tecnológica avanzada diseñada para auditar, visualizar y detectar anomalías en las contrataciones del Estado Peruano. Utilizando **Teoría de Grafos** y algoritmos de alta complejidad, el sistema revela patrones ocultos de corrupción, colusión y fraccionamiento que son invisibles para los métodos de auditoría tradicionales.

---

##  Contexto y Problemática

En 2023, la corrupción e inconducta funcional generaron un perjuicio económico de más de **S/ 24 000 millones** en el Perú. El volumen masivo de datos de compras públicas hace imposible un análisis manual efectivo.

**GovInsight** aborda este problema transformando registros tabulares en una **arquitectura de red (grafo)**, permitiendo a los auditores:
* Identificar monopolios y oligopolios.
* Detectar fragmentación de compras (fraccionamiento).
* Optimizar el presupuesto público mediante simulaciones matemáticas.

---

##  Características Principales

* **Grafo Bipartito Interactivo:** Visualización de conexiones entre Órdenes de Compra y Productos/Servicios.
* **Detección de "Red Flags":** Identificación automática de montos sospechosos y concentración de proveedores.
* **Optimización de Gasto:** Sugerencias de compras óptimas bajo restricciones presupuestales.
* **Reportes Avanzados:** Rankings de proveedores y productos más solicitados.

---

##  Algoritmos Implementados

Este proyecto se distingue por la aplicación rigurosa de estructuras de datos y algoritmos fundamentales para resolver problemas de negocio críticos:

| Técnica | Algoritmo | Aplicación en GovInsight |
| :--- | :--- | :--- |
| **Fuerza Bruta** | Barrido Exhaustivo | **Detección de Monopolios:** Escaneo total de relaciones proveedor-ítem para asegurar cero falsos negativos en auditoría. |
| **Divide & Conquer** | Segmentación Recursiva | **Análisis de Montos (Pareto):** División del dataset en categorías (MEGA, GRANDE, MICRO) para enfocar la auditoría en el 2% crítico. |
| **Búsqueda en Grafos** | BFS (Breadth-First Search) | **Análisis de Fragmentación:** Detección de componentes conexas para identificar compras aisladas o ineficientes. |
| **Grafos / Greedy** | Kruskal + UFDS (Union-Find) | **Red Esencial de Proveedores (MST):** Generación del "esqueleto" del mercado eliminando ruido visual y detectando *hubs* de abastecimiento. |
| **Prog. Dinámica** | Knapsack (Mochila 0/1) | **Optimización Presupuestal:** Maximización del valor social de las compras sin exceder el presupuesto asignado ($W$). |
| **Ordenamiento** | QuickSort | **Rankings:** Generación veloz de reportes Top-N items y proveedores para el dashboard ($O(n \log n)$). |

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.10+
* **Procesamiento de Datos:** Pandas
* **Grafos y Redes:** NetworkX
* **Visualización:** PyVis (HTML/JS interactivo)
* **Fuente de Datos:** [Datos Abiertos Perú](https://www.datosabiertos.gob.pe)

---

##  Estructura del Proyecto

```text
GovInsight/
├── templates/
│   └── index.html
├── static/
│   ├── graphs/                      # Salida de grafos HTML generados
│   └── css/                         # Estilos para reportes
├── analyzer.py                      # Lógica de análisis estadístico
├── builder_graph.py                 # Construcción del grafo NetworkX
├── filter_graph.py                  # Filtrado de subgrafos para visualización
├── graphic.py                       # Generación visual con PyVis
├── analisis_avanzado.py             # Algoritmos complejos (MST, Knapsack, etc.)
├── data_loader.py                   # Carga y limpieza de datos
├── ordenes_compra_servicio.csv      # Dataset fuente
├── main.py                          # Punto de entrada (Ejecución del flujo)
└── README.md
