def quicksort(lista):

    if len(lista) <= 1:
        return lista
    else:
        pivote = lista[len(lista) // 2]
        menores = [x for x in lista if x[1] > pivote[1]]
        iguales = [x for x in lista if x[1] == pivote[1]]
        mayores = [x for x in lista if x[1] < pivote[1]]
        return quicksort(menores) + iguales + quicksort(mayores)


def get_top_items_by_orders(G, nodo_tipo):

    item_nodes = [n for n in G.nodes() if G.nodes[n]['type'] == 'item']

    # Cuenta cuántas órdenes tiene cada ítem (degree = número de conexiones)
    item_degrees = [(n, G.degree(n)) for n in item_nodes]

    # Ordena de mayor a menor usando QuickSort
    top_items = quicksort(item_degrees)

    # Imprime los top 10
    print(f"\nTop 10 {nodo_tipo}s con más órdenes:")
    for i, (node, degree) in enumerate(top_items[:10], 1):
        item_name = G.nodes[node].get('label_original', G.nodes[node]['label'])
        print(f"  {i}. {item_name[:70]}: {degree} órdenes")

    return top_items


def get_top_items_by_monto(G, nodo_tipo):

    item_nodes = [n for n in G.nodes() if G.nodes[n]['type'] == 'item']
    item_montos = {}

    # Suma el monto total de cada ítem
    for n in item_nodes:
        total_monto = sum(G[n][neighbor]['weight'] for neighbor in G.neighbors(n))
        item_montos[n] = total_monto

    # Ordena por monto total
    top_montos = quicksort(list(item_montos.items()))[:10]

    # Imprime los top 10
    print(f"\nTop 10 {nodo_tipo}s por monto total de compras:")
    for i, (node, monto) in enumerate(top_montos, 1):
        item_name = G.nodes[node].get('label_original', G.nodes[node]['label'])
        print(f"  {i}. {item_name[:70]}: S/ {monto:,.2f}")
    print()

    return top_montos


def get_orders_per_item_distribution(G):
    """
    Analiza la distribución de órdenes por ítem
    """
    item_nodes = [n for n in G.nodes() if G.nodes[n]['type'] == 'item']
    orders_count = [G.degree(n) for n in item_nodes]

    print("\nDistribución de órdenes por ítem:")
    print(f"  - Ítems con 1 orden: {sum(1 for c in orders_count if c == 1)}")
    print(f"  - Ítems con 2-5 órdenes: {sum(1 for c in orders_count if 2 <= c <= 5)}")
    print(f"  - Ítems con 6-10 órdenes: {sum(1 for c in orders_count if 6 <= c <= 10)}")
    print(f"  - Ítems con 11-20 órdenes: {sum(1 for c in orders_count if 11 <= c <= 20)}")
    print(f"  - Ítems con más de 20 órdenes: {sum(1 for c in orders_count if c > 20)}")
    print()


def analizar_interconexiones(G, nodo_tipo):

    print("Análisis de interconexiones entre ítems:")
    print()

    item_nodes = [n for n in G.nodes() if G.nodes[n]['type'] == 'item']
    orden_nodes = [n for n in G.nodes() if G.nodes[n]['type'] == 'orden']

    # Analizar órdenes compartidas
    ordenes_con_multiples_items = []
    for orden in orden_nodes:
        items_en_orden = [n for n in G.neighbors(orden) if G.nodes[n]['type'] == 'item']
        if len(items_en_orden) >= 2:
            ordenes_con_multiples_items.append((orden, len(items_en_orden)))

    # Ordenar por número de ítems
    ordenes_con_multiples_items.sort(key=lambda x: x[1], reverse=True)

    print(f"Total de órdenes: {len(orden_nodes)}")
    print(f"Órdenes con múltiples ítems: {len(ordenes_con_multiples_items)}")
    print(f"Porcentaje de interconexión: {len(ordenes_con_multiples_items) / len(orden_nodes) * 100:.1f}%")


    # Calcular interconexión por ítem
    item_interconexiones = {}
    for item in item_nodes:
        ordenes_item = set(G.neighbors(item))
        items_conectados = set()
        for orden in ordenes_item:
            items_en_orden = [n for n in G.neighbors(orden)
                              if G.nodes[n]['type'] == 'item' and n != item]
            items_conectados.update(items_en_orden)
        item_interconexiones[item] = len(items_conectados)

    # Top ítems más interconectados
    top_interconectados = sorted(item_interconexiones.items(),
                                 key=lambda x: x[1], reverse=True)[:10]

    print(f"\nTop 10 {nodo_tipo}s más interconectados (comparten órdenes con más ítems):")
    for i, (node, num_conexiones) in enumerate(top_interconectados, 1):
        item_name = G.nodes[node].get('label_original', G.nodes[node]['label'])
        print(f"  {i}. {item_name[:60]}: conectado con {num_conexiones} otros ítems")

    print()


def buscar_item_y_estadisticas(G, nombre_item):
    """
    Busca un ítem en el grafo por nombre normalizado o parcial 
    y calcula sus estadísticas clave.
    """
    
    # Normalizar el nombre de búsqueda
    from data_loader import normalize_products 
    nombre_normalizado = normalize_products(nombre_item)
    
    item_encontrado = None
    item_node_id = None
    
    #  Búsqueda por descripción original y normalizada
    for node in G.nodes():
        if G.nodes[node]['type'] == 'item':
            # Buscar por nombre original 
            if nombre_item.lower() in G.nodes[node].get('label_original', '').lower():
                item_node_id = node
                item_encontrado = G.nodes[node]
                break
            # Buscar por nombre normalizado 
            elif nombre_normalizado == G.nodes[node]['label']:
                item_node_id = node
                item_encontrado = G.nodes[node]
                break

    if not item_encontrado:
        return None

    # Calcular estadísticas
    ordenes = list(G.neighbors(item_node_id))
    num_ordenes = len(ordenes)
    
    montos = [G[item_node_id][orden]['weight'] for orden in ordenes]
    monto_total = sum(montos)
    monto_promedio = monto_total / num_ordenes if num_ordenes > 0 else 0
    
    # Proveedores únicos
    proveedores = set()
    for orden in ordenes:
        proveedor = G.nodes[orden].get('proveedor') or G.nodes[orden].get('ORDEN_PROVEEDOR')
        if proveedor and 'MÚLTIPLE' not in proveedor:
            proveedores.add(proveedor)
            
    num_proveedores = len(proveedores)
    
    # Análisis de monopolio 
    if num_proveedores == 1 and monto_total > 5000: 
         analisis_proveedor = "Riesgo de Monopolio (1 proveedor)"
    elif num_proveedores == 2 and monto_total > 10000:
         analisis_proveedor = "Riesgo de Duopolio (2 proveedores)"
    else:
         analisis_proveedor = f"Diversificación BAJA ({num_proveedores} proveedores)"

    return {
        'nombre_original': item_encontrado.get('label_original'),
        'num_ordenes': num_ordenes,
        'monto_total': monto_total,
        'monto_promedio': monto_promedio,
        'num_proveedores': num_proveedores,
        'proveedores': list(proveedores),
        'analisis_proveedor': analisis_proveedor,
        'ordenes_ejemplo': [G.nodes[o].get('label') for o in ordenes[:5]]
    }

def formatear_resultado_busqueda(resultado):

    if not resultado:
        return ""
        
    output_lines = []
    
    output_lines.append("=" * 80)
    output_lines.append(f" ANÁLISIS DETALLADO DEL ÍTEM: {resultado['nombre_original']}".center(80))
    output_lines.append("=" * 80)
    
    # Usando iconos de texto para claridad sin emojis
    output_lines.append(f" [Órdenes] Número de órdenes: {resultado['num_ordenes']:,}")
    output_lines.append(f" [Monto] Monto Total de Compra: S/ {resultado['monto_total']:,.2f}")
    output_lines.append(f" [Promedio] Monto Promedio por Orden: S/ {resultado['monto_promedio']:,.2f}")
    output_lines.append(f" [Proveedores] Proveedores Únicos: {resultado['num_proveedores']}")
    output_lines.append(f" [Riesgo] Evaluación: {resultado['analisis_proveedor']}")
    
    output_lines.append("\n Top 5 Proveedores:")
    for i, prov in enumerate(resultado['proveedores'][:5], 1):
        output_lines.append(f"    {i}. {prov}")
        
    output_lines.append("\n Órdenes de Ejemplo (Números):")
    for orden in resultado['ordenes_ejemplo']:
        output_lines.append(f"    • {orden}")

    return "\n".join(output_lines)