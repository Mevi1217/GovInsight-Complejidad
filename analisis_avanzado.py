from collections import defaultdict, deque
from pyvis.network import Network

# FUERZA BRUTA (Detección de Monopolios)

def detectar_monopolios(G, umbral_monto=10000):
    print("Detección de monopolios")

    item_proveedores = {}
    item_montos = {}
    item_ordenes = {}

    # FUERZA BRUTA 1:
    # Recorremos TODOS los nodos del grafo y filtramos los de tipo 'orden'.
    for orden in G.nodes():
        if G.nodes[orden]['type'] == 'orden':

            proveedor = G.nodes[orden].get('proveedor') or G.nodes[orden].get('ORDEN_PROVEEDOR')
            if not proveedor:
                continue

            # FUERZA BRUTA 2:
            # Se recorren TODOS los vecinos del nodo 'orden' para
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


#DIVIDE Y VENCERÁS (Análisis por Rangos de Monto)

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

    # Aquí se aplica la RECURSIÓN sobre cada rango
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

#BÚSQUEDAS EN GRAFOS (Análisis de Fragmentación)

def analizar_fragmentacion_red(G):
    print("Fragmentación de red (BFS/DFS) ")
    print()

    item_nodes = [n for n in G.nodes() if G.nodes[n]['type'] == 'item']

    # BFS para componentes conexas
    visitados = set()
    componentes = []

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

    for item in item_nodes:
        if item not in visitados:
            comp = bfs_componente(item)
            componentes.append(comp)

    componentes.sort(key=len, reverse=True)

    print(f"   Total de componentes: {len(componentes)}")
    print(f"   Total de ítems: {len(item_nodes)}")
    print(f"   Fragmentación: {'ALTA' if len(componentes) > 100 else 'MEDIA' if len(componentes) > 10 else 'BAJA'}\n")

    # Analizar componente principal
    if componentes:
        comp_principal = componentes[0]
        porcentaje_principal = len(comp_principal) / len(item_nodes) * 100

        print(f"   COMPONENTE PRINCIPAL:")
        print(f"     Tamaño: {len(comp_principal)} ítems ({porcentaje_principal:.1f}% del total)")
        print(f"     Interpretación: {'Red bien conectada' if porcentaje_principal > 60 else 'Red fragmentada'}")

    # Analizar componentes pequeñas
    comp_pequenas = [c for c in componentes if len(c) <= 5]
    comp_medianas = [c for c in componentes if 6 <= len(c) <= 20]
    comp_grandes = [c for c in componentes if len(c) > 20]



    # Causas de fragmentación
    print(f"Causa de fragmentación:")

    items_con_1_orden = sum(1 for item in item_nodes if G.degree(item) == 1)
    porcentaje_1_orden = items_con_1_orden / len(item_nodes) * 100

    print(f"{items_con_1_orden} ítems ({porcentaje_1_orden:.1f}%) tienen solo 1 orden")
    print(f" Causa principal: Compras únicas no recurrentes")

    if len(comp_pequenas) > 100:
        print(f"{len(comp_pequenas)} componentes pequeñas aisladas")
        print(f"Indica: Compras especializadas sin relación entre sí")

    # Identificar ítems puente 
    print(f"Items que son intermedios:")
    print(f"(Ítems que conectan muchas órdenes y otros ítems)\n")

    items_criticos = []

    # Los ítems con más órdenes son naturalmente puentes
    items_frecuentes = [(item, G.degree(item)) for item in item_nodes]
    items_frecuentes.sort(key=lambda x: x[1], reverse=True)

    # Analizar top 15 ítems más frecuentes
    for item, num_ordenes in items_frecuentes[:15]:
        if num_ordenes >= 5:  # Solo ítems con 5+ órdenes
            # Contar cuántos ítems únicos conecta a través de órdenes compartidas
            items_conectados = set()
            for orden in G.neighbors(item):
                for vecino in G.neighbors(orden):
                    if G.nodes[vecino]['type'] == 'item' and vecino != item:
                        items_conectados.add(vecino)

            if len(items_conectados) >= 5:  # Solo si conecta 5+ ítems distintos
                items_criticos.append((item, len(items_conectados), num_ordenes))

    if items_criticos:
        items_criticos.sort(key=lambda x: x[1], reverse=True)
        for item, num_conectados, num_ordenes in items_criticos[:5]:
            nombre = G.nodes[item].get('label_original', '')[:50]
            print(f"{nombre}")
            print(f"{num_ordenes} órdenes | Conecta {num_conectados} ítems distintos")




    return {
        'componentes': componentes,
        'num_componentes': len(componentes),
        'items_criticos': items_criticos,
        'fragmentacion': len(componentes) / len(item_nodes)
    }

# PROGRAMACIÓN DINÁMICA (Optimización de Presupuesto)
import math


def optimizar_compras_presupuesto_corregido(G, presupuesto_total, necesidades_criticas=None):
    print("Optimización de Presupuesto")
    print("-" * 50)

    if necesidades_criticas is None:
        necesidades_criticas = ['agua', 'alimento', 'medicina', 'salud', 'educacion',
                                'seguridad', 'emergencia', 'hospital', 'obra', 'social']

    item_nodes = [n for n in G.nodes() if G.nodes[n]['type'] == 'item']

    # 1. Preparación de datos
    items_info = []
    for item in item_nodes:
        ordenes = list(G.neighbors(item))
        if not ordenes:
            continue

        # Calculamos el costo promedio real
        costo_real = sum(G[item][orden]['weight'] for orden in ordenes) / len(ordenes)

        # El valor es la frecuencia de uso (demanda social)
        valor = len(ordenes)

        # Identifica si la descripción del ítem contiene palabras clave de necesidades críticas.
        nombre = G.nodes[item].get('label_original', G.nodes[item]['label']).lower()
        es_critico = any(nec in nombre for nec in necesidades_criticas)

        if es_critico:
            valor *= 3  # Ponderación estratégica: los ítems críticos valen triple

        # Filtrar ítems imposibles (más caros que todo el presupuesto)
        if costo_real <= presupuesto_total and costo_real > 0:
            items_info.append({
                'item_id': item,
                'nombre': G.nodes[item].get('label_original', G.nodes[item]['label']),
                'costo_real': costo_real,
                'valor': int(valor), 
                'critico': es_critico
            })

    # 2. Reducir el espacio de búsqueda
    # Ordenamos por densidad de valor (Valor / Costo) para quedarnos con los mejores candidatos
    # Esto es necesario porque el DP es lento con miles de ítems.
    items_info.sort(key=lambda x: x['valor'] / x['costo_real'], reverse=True)

    # Seleccionamos los 600 ítems más eficientes
    items_candidatos = items_info[:600]
    n = len(items_candidatos)

    # 3. Cálculo de Escala Dinámica
    # Máximo de columnas que la tabla DP puede manejar eficientemente
    MAX_CAPACIDAD_TABLA = 10000
    factor_escala = max(1, presupuesto_total / MAX_CAPACIDAD_TABLA)

    capacidad_scaled = int(presupuesto_total / factor_escala)

    print(f"   Configuración DP:")
    print(f"   • Presupuesto Real: S/ {presupuesto_total:,.2f}")
    print(f"   • Factor de Escala: 1 unidad = S/ {factor_escala:.2f}")
    print(f"   • Capacidad Tabla: {capacidad_scaled} slots")

    # Asignar costos escalados garantizando que nada cueste 0 si tiene costo real
    for item in items_candidatos:
        costo_s = int(item['costo_real'] / factor_escala)
        item['costo_scaled'] = max(1, costo_s)  # Costo mínimo 1 slot

    # 4. Ejecución del Algoritmo 
    # dp[i][w] = valor máximo usando primeros i ítems con capacidad w
    dp = [[0] * (capacidad_scaled + 1) for _ in range(n + 1)]

    #Construcción de la tabla
    for i in range(1, n + 1):
        costo = items_candidatos[i - 1]['costo_scaled']
        valor = items_candidatos[i - 1]['valor']

        for w in range(capacidad_scaled + 1):
            if costo <= w:
                dp[i][w] = max(dp[i - 1][w], dp[i - 1][w - costo] + valor)
            else:
                dp[i][w] = dp[i - 1][w]

    # 5. Reconstrucción de la Solución
    # Recupera los ítems seleccionados por la ruta óptima en la tabla DP.
    seleccionados = []
    w = capacidad_scaled
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            item = items_candidatos[i - 1]
            seleccionados.append(item)
            w -= item['costo_scaled']

    # Verifica el presupuesto con los costos reales.

    costo_total_real = sum(item['costo_real'] for item in seleccionados)

    # Si nos pasamos del presupuesto real,
    # eliminamos el ítem menos valioso hasta cumplir.
    while costo_total_real > presupuesto_total and seleccionados:
        # Ordenar por menor valor para sacrificar lo menos importante
        seleccionados.sort(key=lambda x: x['valor'])
        eliminado = seleccionados.pop(0)  # Eliminar el de menor valor
        costo_total_real -= eliminado['costo_real']

    # Reordenar por valor
    seleccionados.sort(key=lambda x: x['valor'], reverse=True)

    valor_total = sum(item['valor'] for item in seleccionados)
    criticos_cubiertos = sum(1 for item in seleccionados if item['critico'])

    # 6. Reporte de Resultados
    print(f"\n   RESULTADOS DE OPTIMIZACIÓN:")
    print(f"   Items Seleccionados: {len(seleccionados)}")
    print(f"   Costo Total Real: S/ {costo_total_real:,.2f} ({costo_total_real / presupuesto_total * 100:.1f}%)")
    print(f"   Valor Social (Score): {valor_total:,}")
    print(f"   Necesidades Críticas: {criticos_cubiertos} ítems")

    print(f"\n   TOP 10 ÍTEMS SUGERIDOS:")
    for i, item in enumerate(seleccionados[:10], 1):
        crit_mark = "[CRÍTICO]" if item['critico'] else ""
        print(f"     {i}. {item['nombre'][:40]}... | S/ {item['costo_real']:,.2f} | Score: {item['valor']} {crit_mark}")

    return seleccionados, costo_total_real, valor_total

#UFDS (Union-Find) y MST (Kruskal)
class UnionFind:
    def __init__(self, nodes):
        self.parent = {node: node for node in nodes}
        self.rank = {node: 0 for node in nodes}
        self.size = {node: 1 for node in nodes}

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False
        if self.rank[px] < self.rank[py]:
            px, py = py, px
        self.parent[py] = px
        self.size[px] += self.size[py]
        if self.rank[px] == self.rank[py]:
            self.rank[px] += 1
        return True

    def get_size(self, x):
        return self.size[self.find(x)]

    def get_components(self):
        components = defaultdict(list)
        for node in self.parent:
            root = self.find(node)
            components[root].append(node)
        return dict(components)


def encontrar_red_proveedores_esencial(G_bipartito):
    # 1. RECOLECCIÓN DE DATOS
    proveedor_items_montos = defaultdict(lambda: defaultdict(float))
    proveedor_montos_totales = defaultdict(float)
    proveedores_existentes = set()
    
    for orden in G_bipartito.nodes():
        if G_bipartito.nodes[orden]['type'] == 'orden':
            proveedor = G_bipartito.nodes[orden].get('proveedor') or G_bipartito.nodes[orden].get('ORDEN_PROVEEDOR')
            if not proveedor: continue
            
            proveedores_existentes.add(proveedor)
            items = [n for n in G_bipartito.neighbors(orden) if G_bipartito.nodes[n]['type'] == 'item']
            
            for item in items:
                monto = G_bipartito[orden][item]['weight']
                proveedor_items_montos[proveedor][item] += monto
                proveedor_montos_totales[proveedor] += monto
                
    proveedores_list = list(proveedores_existentes)
    n_proveedores = len(proveedores_list)
    
    if n_proveedores < 2:
        return [], [], {'num_proveedores': n_proveedores, 'esenciales': 0, 'peso_total': 0}

    proveedor_edges = [] 

    for i in range(n_proveedores):
        p1 = proveedores_list[i]
        for j in range(i + 1, n_proveedores):
            p2 = proveedores_list[j]
            
            items_comunes = set(proveedor_items_montos[p1].keys()) & set(proveedor_items_montos[p2].keys())
            
            if items_comunes:

                peso_conexion = sum(
                    proveedor_items_montos[p1][item] + proveedor_items_montos[p2][item]
                    for item in items_comunes
                )
                

                proveedor_edges.append((-peso_conexion, p1, p2, len(items_comunes))) 

    # CÁLCULO DEL MST (KRUSKAL)
    proveedor_edges.sort() 
    
    uf = UnionFind(proveedores_list)
    mst_edges = []
    peso_total_mst = 0
    proveedores_en_mst = set()
    
    for peso_negativo, u, v, shared_items in proveedor_edges:
        if uf.union(u, v):
            peso_real = -peso_negativo
            mst_edges.append((u, v, peso_real, shared_items))
            peso_total_mst += peso_real
            proveedores_en_mst.add(u)
            proveedores_en_mst.add(v)
            
            if len(mst_edges) >= n_proveedores - 1 and len(uf.get_components()) == 1:
                break
    
    #RESULTADOS
    num_componentes = len(uf.get_components())
    proveedores_esenciales = len(proveedores_en_mst)

    # Top proveedores por Centralidad (Grado en el MST)
    item_degree = defaultdict(int)
    for u, v, _, _ in mst_edges:
        item_degree[u] += 1
        item_degree[v] += 1
    proveedores_centrales = sorted(item_degree.items(), key=lambda x: x[1], reverse=True)

    return mst_edges, proveedores_centrales, {
            'num_proveedores': n_proveedores,
            'num_aristas_mst': len(mst_edges),
            'componentes': num_componentes,
            'peso_total': peso_total_mst,
            'proveedores_esenciales': proveedores_esenciales
        }, proveedor_montos_totales


def _generar_visualizacion_mst(top_edges, proveedores_centrales, stats_mst, proveedor_montos):

    # 1. Configuración de la red 
    net = Network(height="800px", width="100%", bgcolor="#111111", font_color="white", directed=False)
    net.barnes_hut(gravity=-4000, central_gravity=0.1, spring_length=200, spring_strength=0.04, damping=0.09)

    # Convertir proveedores_centrales a dict para acceso rápido
    # centralidad = número de conexiones en el árbol esencial
    centralidad_dict = dict(proveedores_centrales)

    # Calcular rangos para normalizar colores y tamaños
    max_monto = max(proveedor_montos.values()) if proveedor_montos else 1
    max_centralidad = max(centralidad_dict.values()) if centralidad_dict else 1

    # Conjunto de nodos que realmente están en el MST
    nodos_en_mst = set()
    for u, v, _, _ in top_edges:
        nodos_en_mst.add(u)
        nodos_en_mst.add(v)

    # 2. Agregar Nodos (Proveedores)
    for proveedor_id in nodos_en_mst:
        monto = proveedor_montos.get(proveedor_id, 0)
        centralidad = centralidad_dict.get(proveedor_id, 0)

        # Color y Tamaño
        size = 15 + (centralidad / max_centralidad) * 40


        if monto > max_monto * 0.5:  # Top players económicos
            color = "#ff4757"  
            group = "Gigante Comercial"
        elif centralidad > 2 and monto < max_monto * 0.1:  # Muy conectados pero poco monto 
            color = "#ffa502" 
            group = "Intermediario/Conector"
        else:
            color = "#1e90ff" 
            group = "Proveedor Regular"

        label = proveedor_id[:20] + "..." if len(proveedor_id) > 20 else proveedor_id

        tooltip = (
            f" <b>{proveedor_id}</b><br>"
            f"-------------------------<br>"
            f" Monto Vendido: S/ {monto:,.2f}<br>"
            f" Conexiones Clave: {centralidad}<br>"
            f" Rol: {group}"
        )

        net.add_node(
            proveedor_id,
            label=label,
            title=tooltip,
            size=size,
            color=color,
            borderWidth=2,
            borderWidthSelected=4,
            font={'size': 12, 'face': 'arial', 'color': 'white'}
        )

    #  Agregar Aristas (Relaciones)
    for u, v, peso_compartido, items_comunes in top_edges:
        width = 1 + (peso_compartido / stats_mst['peso_total']) * 20
        width = min(width, 8)  # Tope máximo

        edge_tooltip = (
            f" Conexión Fuerte<br>"
            f"Items compartidos: {items_comunes}<br>"
            f"Volumen de negocio común: S/ {peso_compartido:,.2f}"
        )

        net.add_edge(
            u, v,
            width=width,
            color="rgba(255, 255, 255, 0.3)",  
            title=edge_tooltip
        )

    net.show_buttons(filter_=['physics'])
    output_path = "static/mst_red_proveedores.html"
    net.save_graph(output_path)

def ejecutar_mst_analisis(G):
    """Ejecuta el MST, genera la visualización y reporta a la consola."""

    import sys 
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " ANÁLISIS MST - RED DE PROVEEDORES (KRUSKAL) ".center(68) + "║")
    print("╚" + "=" * 68 + "╝")

    try:
        mst_edges, proveedores_centrales, stats_mst, proveedor_montos = encontrar_red_proveedores_esencial(G)
        
        _generar_visualizacion_mst(mst_edges, proveedores_centrales, stats_mst, proveedor_montos)
        
        print("-" * 40)
        print(f"Número total de proveedores: {stats_mst['num_proveedores']}")
        print(f"Proveedores esenciales en el MST: {stats_mst['proveedores_esenciales']}")
        print(f"Peso Total del MST (Monto compartido): S/ {stats_mst['peso_total']:,.2f}")
        print(f"Componentes Conexos: {stats_mst['componentes']}")

        print("\n TOP 5 PROVEEDORES MÁS CENTRALES EN LA RED:")
        for i, (proveedor, grado) in enumerate(proveedores_centrales[:5], 1):
            monto_total = proveedor_montos.get(proveedor, 0)
            print(f" {i}. {proveedor[:40]} | Grado MST: {grado} | Monto Total: S/ {monto_total:,.2f}")
            
        print("\n ARISTAS MÁS PESADAS (MAYOR MONTO COMPARTIDO):")
        for i, (u, v, peso, shared_items) in enumerate(mst_edges[:5], 1):
            print(f" {i}. {u} <-> {v} | Ítems Comunes: {shared_items} | Peso: S/ {peso:,.2f}")
            
        
        return {
            'stats': stats_mst, 
            'centrales_top5': proveedores_centrales[:5],
            'edges_top5': mst_edges[:5]
        }
        
    except Exception as e:
        print(f"\n ERROR AL EJECUTAR MST: {e}")
        import traceback
        traceback.print_exc(file=sys.stdout)
        
        return None


def ejecutar_analisis_mejorado(G, presupuesto=100000, umbral_fraude=5000):

    resultados = {}

    # Detección de Monopolios
    try:
        monopolios = detectar_monopolios(G, umbral_monto=umbral_fraude)
        resultados['monopolios'] = monopolios
    except Exception as e:
        print(f"\n Error en detección de monopolios: {e}")
        resultados['monopolios'] = None

    # Análisis de Montos
    try:
        montos = analizar_montos_divide_conquista(G)
        resultados['montos'] = montos
    except Exception as e:
        print(f"\nError en análisis de montos: {e}")
        resultados['montos'] = None

    # Fragmentación
    try:
        fragmentacion = analizar_fragmentacion_red(G)
        resultados['fragmentacion'] = fragmentacion
    except Exception as e:
        print(f"\n Error en análisis de fragmentación: {e}")
        resultados['fragmentacion'] = None

    try:
        items, costo, valor = optimizar_compras_presupuesto_corregido(G, presupuesto)
        resultados['dp'] = {'items': items, 'costo': costo, 'valor': valor}
    except Exception as e:
        print(f"\n Error en DP: {e}")
        resultados['dp'] = None

    exitos = sum(1 for v in resultados.values() if v is not None)
    print(f"\nAlgoritmos ejecutados: {exitos}/5")

    # Análisis de Red Esencial (MST)
    try:
        mst_data = ejecutar_mst_analisis(G)
        resultados['mst'] = mst_data 
    except Exception as e:
        print(f"\n Error en análisis MST: {e}")
        resultados['mst'] = None

    exitos = sum(1 for v in resultados.values() if v is not None)
    print(f"\nTOTAL de Algoritmos ejecutados: {exitos}/5")

    return resultados


if __name__ == "__main__":
    print("Módulo de algoritmos avanzados listo para importar.")