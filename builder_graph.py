import networkx as nx


def build_graph(df, nodo_tipo):

    # Construye un grafo vacío
    G = nx.Graph()

    # Agrupar preservando ORDEN_PROVEEDOR
    df_grouped = df.groupby(
        ["ORDEN_NUMERO", "ORDEN_PROVEEDOR", "ORDEN_DESCRIPCION_NORM", "ORDEN_DESCRIPCION"],
        as_index=False
    ).agg({
        "ORDEN_MONTO": "sum"
    })

    orden_proveedores = {}  # orden_numero -> set de proveedores

    for _, row in df_grouped.iterrows():
        orden_num = row['ORDEN_NUMERO']
        orden = f"Orden_{orden_num}"
        proveedor = row['ORDEN_PROVEEDOR']

        item = f"Item_{row['ORDEN_DESCRIPCION_NORM']}"
        item_label = row['ORDEN_DESCRIPCION'][:80]

        if orden_num not in orden_proveedores:
            orden_proveedores[orden_num] = set()
        orden_proveedores[orden_num].add(proveedor)

        if not G.has_node(orden):
            G.add_node(
                orden,
                label=row["ORDEN_NUMERO"],
                type="orden",
                proveedor=proveedor,
                ORDEN_PROVEEDOR=proveedor,
                proveedores_set=set([proveedor])
            )
        else:
            G.nodes[orden]['proveedores_set'].add(proveedor)

            if len(G.nodes[orden]['proveedores_set']) > 1:
                # Mantener lista de todos los proveedores
                provs_lista = list(G.nodes[orden]['proveedores_set'])
                G.nodes[orden]['proveedor'] = f"MÚLTIPLE ({len(provs_lista)})"
                G.nodes[orden]['ORDEN_PROVEEDOR'] = f"MÚLTIPLE ({len(provs_lista)})"
                G.nodes[orden]['proveedores_lista'] = provs_lista
                G.nodes[orden]['es_multiple'] = True

        if not G.has_node(item):
            G.add_node(
                item,
                label=row["ORDEN_DESCRIPCION_NORM"],
                label_original=item_label,
                type="item"
            )

        if G.has_edge(orden, item):
            G[orden][item]['weight'] += row["ORDEN_MONTO"]
        else:
            G.add_edge(orden, item, weight=row["ORDEN_MONTO"])

    ordenes_con_multiples_proveedores = sum(
        1 for n in G.nodes()
        if G.nodes[n]['type'] == 'orden' and len(G.nodes[n].get('proveedores_set', set())) > 1
    )

    print(f"Grafo generado:")
    print(f"Nodos totales: {G.number_of_nodes():,}")
    print(f"Órdenes: {sum(1 for n in G.nodes() if G.nodes[n]['type'] == 'orden'):,}")
    print(f"Ítems ({nodo_tipo}): {sum(1 for n in G.nodes() if G.nodes[n]['type'] == 'item'):,}")
    print(f"Aristas: {G.number_of_edges():,}")

    if ordenes_con_multiples_proveedores > 0:
        print(f"Órdenes con múltiples proveedores: {ordenes_con_multiples_proveedores}")

        ejemplos = []
        for n in G.nodes():
            if G.nodes[n]['type'] == 'orden' and G.nodes[n].get('es_multiple', False):
                ejemplos.append((n, G.nodes[n]['proveedores_lista']))
                if len(ejemplos) >= 3:
                    break

        if ejemplos:
            print("   Ejemplos:")
            for orden, provs in ejemplos:
                print(f"    - {orden}: {', '.join(provs[:3])}{'...' if len(provs) > 3 else ''}")

    print()

    return G


def validate_graph_integrity(G):

    issues = []

    for node in G.nodes():
        node_data = G.nodes[node]

        if node_data['type'] == 'orden':
            if 'proveedor' not in node_data and 'ORDEN_PROVEEDOR' not in node_data:
                issues.append(f"Orden {node} sin información de proveedor")

            if 'proveedores_set' in node_data:
                if len(node_data['proveedores_set']) > 1 and not node_data.get('es_multiple', False):
                    issues.append(f"Orden {node} con múltiples proveedores no marcada correctamente")

    if issues:
        print(" Problemas de integridad detectados:")
        for issue in issues[:5]:  # Mostrar máximo 5 problemas
            print(f"   - {issue}")
        if len(issues) > 5:
            print(f"   ... y {len(issues) - 5} más")
    else:
        print(" Integridad del grafo verificada correctamente")

    return len(issues) == 0