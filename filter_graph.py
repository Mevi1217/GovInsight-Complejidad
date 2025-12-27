def calcular_interconexiones(G, item_nodes):

    interconexiones = {}

    for item in item_nodes:
        # Obtener las órdenes de este ítem
        ordenes_item = set(G.neighbors(item))

        # Contar cuántos otros ítems comparten al menos una orden
        items_conectados = set()
        for orden in ordenes_item:
            # Obtener todos los ítems de esta orden
            items_en_orden = [n for n in G.neighbors(orden) if G.nodes[n]['type'] == 'item']
            items_conectados.update(items_en_orden)

        # Excluir el ítem mismo
        items_conectados.discard(item)
        interconexiones[item] = len(items_conectados)

    return interconexiones


def filter_subgraph_interconectado(G, top_items, min_ordenes, max_ordenes_por_item, max_items):

    # Filtrar ítems por frecuencia mínima
    candidatos = [(node, degree) for node, degree in top_items if degree >= min_ordenes]

    if not candidatos:
        print("⚠ No hay ítems que cumplan el criterio mínimo")
        return G.subgraph([]).copy()

    print(f"Ítems candidatos (mínimo {min_ordenes} órdenes): {len(candidatos)}")

    # Calcular interconexiones para todos los candidatos
    candidatos_nodes = [node for node, _ in candidatos]
    interconexiones = calcular_interconexiones(G, candidatos_nodes)

    # Ordenar candidatos por interconexión 
    candidatos_ordenados = sorted(
        candidatos_nodes,
        key=lambda x: (interconexiones.get(x, 0), G.degree(x)),
        reverse=True
    )

    # Seleccionar ítems usando expansión por conexión
    items_seleccionados = set()
    ordenes_incluidas = set()

    # Comenzar con el ítem más interconectado
    if candidatos_ordenados:
        semilla = candidatos_ordenados[0]
        items_seleccionados.add(semilla)
        ordenes_semilla = list(G.neighbors(semilla))[:max_ordenes_por_item]
        ordenes_incluidas.update(ordenes_semilla)

    while len(items_seleccionados) < max_items and len(items_seleccionados) < len(candidatos_ordenados):
        mejor_candidato = None
        mejor_score = -1

        for candidato in candidatos_ordenados:
            if candidato in items_seleccionados:
                continue

            ordenes_candidato = set(G.neighbors(candidato))
            ordenes_compartidas = len(ordenes_candidato & ordenes_incluidas)

            score = ordenes_compartidas * 10 + interconexiones.get(candidato, 0)

            if score > mejor_score:
                mejor_score = score
                mejor_candidato = candidato

        if mejor_candidato is None:
            for candidato in candidatos_ordenados:
                if candidato not in items_seleccionados:
                    items_seleccionados.add(candidato)
                    ordenes_nuevas = list(G.neighbors(candidato))[:max_ordenes_por_item]
                    ordenes_incluidas.update(ordenes_nuevas)
                    break
        else:
            items_seleccionados.add(mejor_candidato)
            ordenes_nuevas = list(G.neighbors(mejor_candidato))[:max_ordenes_por_item]
            ordenes_incluidas.update(ordenes_nuevas)

    subgraph_nodes = set(items_seleccionados) | ordenes_incluidas

    # Crear el subgrafo
    H = G.subgraph(subgraph_nodes).copy()

    # Calcular estadísticas de interconexión
    nodos_ordenes = sum(1 for n in H.nodes() if H.nodes[n]['type'] == 'orden')
    nodos_items = sum(1 for n in H.nodes() if H.nodes[n]['type'] == 'item')

    # Contar órdenes compartidas 
    ordenes_compartidas = sum(1 for n in H.nodes()
                              if H.nodes[n]['type'] == 'orden' and H.degree(n) >= 2)

    print(f"\n✓ Subgrafo INTERCONECTADO creado")
    print(f"  - Total nodos: {H.number_of_nodes()}")
    print(f"  - Ítems: {nodos_items}")
    print(f"  - Órdenes: {nodos_ordenes}")
    print(f"  - Órdenes compartidas (2+ ítems): {ordenes_compartidas}")
    print(f"  - Aristas: {H.number_of_edges()}")
    print(f"  - Nivel de interconexión: {ordenes_compartidas / nodos_ordenes * 100:.1f}%")
    print()

    return H


def filter_subgraph(G, min_ordenes, max_ordenes, max_items, top_items):

    if not top_items:
        print("No hay ítems para filtrar. Regresando grafo completo.")
        return G

    candidatos = [
        (node, degree) for node, degree in top_items
        if min_ordenes <= degree <= max_ordenes
    ]

    if not candidatos:
        print("No se encontraron candidatos válidos. Usando todos los ítems.")
        candidatos = top_items

    candidatos = sorted(candidatos, key=lambda x: x[1], reverse=True)[:max_items]
    nodos_items = {node for node, _ in candidatos}


    nodos_permitidos = set(nodos_items)

    for item in nodos_items:
        nodos_permitidos.update(G.neighbors(item))


    H = G.subgraph(nodos_permitidos).copy()

    print("✓ Subgrafo creado correctamente")
    print(f"  Items: {sum(1 for n in H.nodes if H.nodes[n]['type']=='item')}")
    print(f"  Órdenes: {sum(1 for n in H.nodes if H.nodes[n]['type']=='orden')}")
    print(f"  Aristas: {H.number_of_edges()}")

    return H