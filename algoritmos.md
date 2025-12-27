## 1. FUERZA BRUTA

### Ubicación: analisis_avanzado.py - Función detectar_monopolios()

def detectar_monopolios(G, umbral_monto=10000):
    print("Detección de monopolios")

    item_proveedores = {}
    item_montos = {}
    item_ordenes = {}

    # --------------------------------------------------------------------
    # FUERZA BRUTA 1:
    # Recorremos TODOS los nodos del grafo y filtramos los de tipo 'orden'.
    # No existe poda, no se salta nada; es un barrido completo.
    # --------------------------------------------------------------------
    for orden in G.nodes():
        if G.nodes[orden]['type'] == 'orden':

            proveedor = G.nodes[orden].get('proveedor') or G.nodes[orden].get('ORDEN_PROVEEDOR')
            if not proveedor:
                continue

            # ------------------------------------------------------------
            # FUERZA BRUTA 2:
            # Se recorren TODOS los vecinos del nodo 'orden' para
            # encontrar ítems. Esto no tiene optimización ni poda.
            # ------------------------------------------------------------
            items = [n for n in G.neighbors(orden) if G.nodes[n]['type'] == 'item']

            for item in items:
                if item not in item_proveedores:
                    item_proveedores[item] = set()
                    item_montos[item] = 0
                    item_ordenes[item] = []

                item_proveedores[item].add(proveedor)

                monto = G[orden][item]['weight']
                item_montos[item] += monto
                item_ordenes[item].append((orden, proveedor, monto))

    print(f"Analizando {len(item_proveedores)} ítems con información de proveedor...")
    print(f"Umbral de riesgo: S/ {umbral_monto:,.2f}\n")

    casos_monopolio = []

    def evaluar_riesgo(item, proveedores, monto_total):
        num_proveedores = len(proveedores)

        if num_proveedores > 3:
            return None, 0

        if monto_total < umbral_monto / 2:
            return None, 0

        # Clasificación directa sin exploración combinatoria.
        if num_proveedores == 1:
            if monto_total >= umbral_monto * 5:
                return 'MONOPOLIO_CRÍTICO', 10
            elif monto_total >= umbral_monto:
                return 'MONOPOLIO', 7
            else:
                return 'MONOPOLIO_MENOR', 5

        elif num_proveedores == 2:
            if monto_total >= umbral_monto * 5:
                return 'DUOPOLIO_CRÍTICO', 6
            elif monto_total >= umbral_monto:
                return 'DUOPOLIO', 4

        elif num_proveedores == 3:
            if monto_total >= umbral_monto * 10:
                return 'OLIGOPOLIO_CRÍTICO', 3
            elif monto_total >= umbral_monto * 3:
                return 'OLIGOPOLIO', 2

        return None, 0

    # --------------------------------------------------------------------
    # FUERZA BRUTA 3:
    # Se evalúan TODOS los ítems detectados.
    # No se realiza poda previa para descartar ítems pequeños.
    # No hay backtracking; es un único recorrido lineal.
    # --------------------------------------------------------------------
    for item in item_proveedores:
        proveedores = item_proveedores[item]
        monto_total = item_montos[item]

        tipo, severidad = evaluar_riesgo(item, proveedores, monto_total)

        if tipo:
            nombre_item = G.nodes[item].get('label_original', G.nodes[item]['label'])
            num_ordenes = len(item_ordenes[item])

            caso = {
                'tipo': tipo,
                'severidad': severidad,
                'item': nombre_item,
                'num_proveedores': len(proveedores),
                'proveedores': list(proveedores),
                'monto_total': monto_total,
                'num_ordenes': num_ordenes,
                'precio_promedio': monto_total / num_ordenes if num_ordenes > 0 else 0
            }

            casos_monopolio.append(caso)

    # Ordenamiento: también es fuerza bruta sobre la lista generada
    casos_monopolio.sort(key=lambda x: (x['severidad'], x['monto_total']), reverse=True)

    monopolios_totales = len([c for c in casos_monopolio if c['num_proveedores'] == 1])
    duopolios = len([c for c in casos_monopolio if c['num_proveedores'] == 2])
    oligopolios = len([c for c in casos_monopolio if c['num_proveedores'] == 3])

    print(f"Análisis de monopolios:")
    print(f"  Total de casos detectados: {len(casos_monopolio)}")
    print(f"  • Monopolios (1 proveedor): {monopolios_totales}")
    print(f"  • Duopolios (2 proveedores): {duopolios}")
    print(f"  • Oligopolios (3 proveedores): {oligopolios}")

    if not casos_monopolio:
        print("\n No se detectaron monopolios significativos")
        print("   El sistema tiene buena diversificación de proveedores")
        return casos_monopolio

    return casos_monopolio

 ### Propósito:
- Detectar posibles monopolios en la red de proveedores mediante el análisis de todos los ítems y las órdenes asociadas.

- Explorar todos los ítems del grafo (barrido completo, fuerza bruta).

- Aplicar filtros simples basados en umbrales de montos para descartar ítems de bajo impacto.

- Clasificar el nivel de concentración del mercado según el número de proveedores y el monto total:

- Monopolio

- Duopolio

- Oligopolio



## 2. QuickSORT - Ubicación: analyzer.py

def quicksort(lista):
    if len(lista) <= 1:
        return lista
    else:
        pivote = lista[len(lista) // 2]
        menores = [x for x in lista if x[1] > pivote[1]]
        iguales = [x for x in lista if x[1] == pivote[1]]
        mayores = [x for x in lista if x[1] < pivote[1]]
        return quicksort(menores) + iguales + quicksort(mayores)

### Propósito:

- Ordenar ítems por frecuencia/monto
- Usado en get_top_items_by_orders() y get_top_items_by_monto()
- Genera rankings de productos más importantes
- Base para filtrado de subgrafos


## 3. Divide y Vencerás - Ubicación: analisis_avanzado.py

def analizar_montos_divide_conquista(G, profundidad=0, items_list=None, nivel_nombre="RAÍZ"):

    if profundidad == 0:
        print("Analisis de rangos de montos (Divide y Vencerás Recursivo) ")
        print()

        # Calcular montos por ítem
        items_list = []
        for item in G.nodes():
            if G.nodes[item]['type'] != 'item':
                continue

            ordenes = list(G.neighbors(item))
            if not ordenes:
                continue

            monto_total = sum(G[item][orden]['weight'] for orden in ordenes)
            monto_promedio = monto_total / len(ordenes)

            items_list.append({
                'node': item,
                'nombre': G.nodes[item].get('label_original', '')[:60],
                'num_ordenes': len(ordenes),
                'monto_total': monto_total,
                'monto_promedio': monto_promedio,
                'monto_max': max(G[item][orden]['weight'] for orden in ordenes),
                'monto_min': min(G[item][orden]['weight'] for orden in ordenes)
            })

        items_list.sort(key=lambda x: x['monto_total'])

    n = len(items_list)

    # Caso base
    if n <= 10 or profundidad >= 3:
        return {
            'items': items_list,
            'nivel': nivel_nombre,
            'profundidad': profundidad
        }

    # Definir rangos significativos
    montos = [item['monto_total'] for item in items_list]

    # Encontrar puntos de corte significativos
    rangos = {
        'MICRO': [item for item in items_list if item['monto_total'] < 1000],
        'PEQUEÑAS': [item for item in items_list if 1000 <= item['monto_total'] < 10000],
        'MEDIANAS': [item for item in items_list if 10000 <= item['monto_total'] < 50000],
        'GRANDES': [item for item in items_list if 50000 <= item['monto_total'] < 200000],
        'MEGA': [item for item in items_list if item['monto_total'] >= 200000]
    }

    if profundidad == 0:
        print(f"\n Rangos de monto:")
        print(f"Total e productos: {n}\n")

        for nombre_rango, items_rango in rangos.items():
            if not items_rango:
                continue

            montos_rango = [item['monto_total'] for item in items_rango]
            ordenes_rango = [item['num_ordenes'] for item in items_rango]

            print(f"   {nombre_rango}:")
            print(f"     Cantidad: {len(items_rango)} ítems ({len(items_rango)/n*100:.1f}%)")
            print(f"     Monto total: S/ {sum(montos_rango):,.2f}")
            print(f"     Rango: S/ {min(montos_rango):,.2f} - S/ {max(montos_rango):,.2f}")
            print(f"     Promedio: S/ {sum(montos_rango)/len(items_rango):,.2f}")

            # Top 3 de cada rango
            top_items = sorted(items_rango, key=lambda x: x['monto_total'], reverse=True)[:3]
            print(f"     Top 3:")
            for item in top_items:
                print(f"       • {item['nombre'][:50]}: S/ {item['monto_total']:,.2f}")
            print()

    # --- Aquí se aplica la RECURSIÓN sobre cada rango (Divide y Vencerás real) ---
    resultado = {}
    for nombre_rango, items_rango in rangos.items():
        if not items_rango:
            continue
        resultado[nombre_rango] = analizar_montos_divide_conquista(
            G,
            profundidad=profundidad + 1,
            items_list=items_rango,
            nivel_nombre=nombre_rango
        )

    return resultado


### Propósito:

- Segmentar el dataset de productos en rangos de monto
- División estratégica: MICRO → PEQUEÑAS → MEDIANAS → GRANDES → MEGA
- Análisis jerárquico de la distribución de gastos
- Clasificación automática de productos por impacto económico
- Identifica patrones de gasto (ej: 80% productos micro, 20% mega)
- Ayuda a priorizar auditorías (enfocarse en rangos GRANDES/MEGA)


## 4. BFS - Ubicación: analisis_avanzado.py

    def bfs_componente(inicio):
        componente = set()
        queue = deque([inicio])
        visitados.add(inicio)
        componente.add(inicio)

        while queue:
            nodo = queue.popleft()
            for orden in G.neighbors(nodo):
                for vecino in G.neighbors(orden):
                    if G.nodes[vecino]['type'] == 'item' and vecino not in visitados:
                        visitados.add(vecino)
                        componente.add(vecino)
                        queue.append(vecino)
        return componente

### Propósito:

- Encontrar componentes conexas en el grafo bipartito
- Medir fragmentación de la red de compras
- Detecta si hay islas de productos desconectadas
- Identifica ítems puente que conectan componentes

## UFDS (Union-Find Disjoint Set) - Ubicación: analisis_avanzado.py

class UnionFind:
    def __init__(self, nodes):
        self.parent = {node: node for node in nodes}
        self.rank = {node: 0 for node in nodes}
        self.size = {node: 1 for node in nodes}
    
    def find(self, x):
        # PATH COMPRESSION
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False  # Ya están en el mismo conjunto
        
        # UNION BY RANK
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        self.size[px] += self.size[py]
        
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True

### Propósito:

- Mantener conjuntos disjuntos de proveedores durante MST
- Path Compression: O(α(n)) amortizado
- Union by Rank: balanceo de árboles

## 5 MST - KRUSKAL - Ubicación: analisis_avanzado.py


def encontrar_red_proveedores_esencial(G_bipartito):
    # 1. CONSTRUIR GRAFO PROYECTADO DE PROVEEDORES
    proveedor_edges = []
    for i in range(n_proveedores):
        p1 = proveedores_list[i]
        for j in range(i + 1, n_proveedores):
            p2 = proveedores_list[j]
            items_comunes = set(proveedor_items_montos[p1].keys()) & 
                           set(proveedor_items_montos[p2].keys())
            
            if items_comunes:
                peso_conexion = sum(
                    proveedor_items_montos[p1][item] + 
                    proveedor_items_montos[p2][item]
                    for item in items_comunes
                )
                proveedor_edges.append((-peso_conexion, p1, p2, len(items_comunes)))
    
    # 2. KRUSKAL: ORDENAR ARISTAS POR PESO (MÁXIMO)
    proveedor_edges.sort()  # Negativo para MST máximo
    
    # 3. CONSTRUIR MST CON UFDS
    uf = UnionFind(proveedores_list)
    mst_edges = []
    
    for peso_negativo, u, v, shared_items in proveedor_edges:
        if uf.union(u, v):  # Si no crea ciclo
            peso_real = -peso_negativo
            mst_edges.append((u, v, peso_real, shared_items))
            
            # OPTIMIZACIÓN: parar cuando hay árbol completo
            if len(mst_edges) >= n_proveedores - 1:
                break
    
    return mst_edges

### Propósito:

- Encontrar red esencial de proveedores
- Maximizar peso (montos compartidos) → Maximum Spanning Tree
- Identificar proveedores más interconectados