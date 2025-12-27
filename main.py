from analyzer import (
    get_top_items_by_orders,
    get_top_items_by_monto,
    get_orders_per_item_distribution,
    analizar_interconexiones
)

from data_loader import load_data, clean_data, print_statistics
from builder_graph import build_graph
from filter_graph import filter_subgraph
from graphic import create_network, add_nodes, add_edges, generate_legend_html, save_html

from analisis_avanzado import ejecutar_analisis_mejorado


FILE_PATH = "ordenes_compra_servicio.csv"
FILTRO_TIPO = None

NODO_TIPO = (
    "Producto/Servicio" if FILTRO_TIPO is None
    else "Producto" if FILTRO_TIPO == 1
    else "Servicio"
)

MIN_ORDENES_ITEM = 2
MAX_ORDENES_POR_ITEM = 75
MAX_ITEMS_TOTAL = 250

PRESUPUESTO_ANALISIS = 100000
UMBRAL_FRAUDE = 5000

OUTPUT_FILE = "static/graphs/grafo_compras_interactivo.html"

def ejecutar_flujo_completo(filepath=FILE_PATH):


    print("SISTEMA DE ANÁLISIS DE ÓRDENES DE COMPRA - VERSIÓN FINAL".center(70))
    print(f"Archivo: {filepath}")
    print()

    try:
        df = load_data(filepath)
        df = clean_data(df, filtro_tipo=FILTRO_TIPO)
        print_statistics(df, NODO_TIPO)
    except Exception as e:
        print(f"Error en carga de datos: {e}")
        return None, None


    try:
        G = build_graph(df, NODO_TIPO)

        # agregar proveedor a cada orden
        for _, row in df.iterrows():
            key = f"Orden_{row['ORDEN_NUMERO']}"
            if G.has_node(key):
                proveedor = row.get("ORDEN_PROVEEDOR", "DESCONOCIDO")
                G.nodes[key]["proveedor"] = proveedor
                G.nodes[key]["ORDEN_PROVEEDOR"] = proveedor

    except Exception as e:
        print(f"Error en construcción del grafo: {e}")
        return None, None


    try:
        get_orders_or_item = get_orders_per_item_distribution(G)
        inter = analizar_interconexiones(G, NODO_TIPO)
        top_items = get_top_items_by_orders(G, NODO_TIPO)
        total_montos = get_top_items_by_monto(G, NODO_TIPO)
    except Exception as e:
        print(f" Error en análisis básico: {e}")
        top_items = []


    try:
        H = filter_subgraph(
            G,
            MIN_ORDENES_ITEM,
            MAX_ORDENES_POR_ITEM,
            MAX_ITEMS_TOTAL,
            top_items
        )

        net = create_network()
        add_nodes(net, H, NODO_TIPO)
        add_edges(net, H)

        nodos_ordenes = sum(1 for n in H if H.nodes[n]['type'] == 'orden')
        nodos_items = sum(1 for n in H if H.nodes[n]['type'] == 'item')

        legend_html = generate_legend_html(
            NODO_TIPO,
            nodos_items,
            nodos_ordenes,
            H.number_of_edges()
        )

        save_html(net, legend_html, OUTPUT_FILE)

        print("\n" + "=" * 70)
        print("VISUALIZACIÓN GENERADA".center(70))
        print(f"Archivo: {OUTPUT_FILE}")
        print(f"{NODO_TIPO}s: {nodos_items} | Órdenes: {nodos_ordenes} | Aristas: {H.number_of_edges()}")

    except Exception as e:
        print(f"Error en visualización PyVis: {e}")

    # ANÁLISIS AVANZADO

    print("ANÁLISIS AVANZADO".center(70))

    try:
        resultados = ejecutar_analisis_mejorado(
            G,
            presupuesto=PRESUPUESTO_ANALISIS,
            umbral_fraude=UMBRAL_FRAUDE
        )

        if resultados.get("monopolios"):
            print(f"  ✓ Monopolios detectados: {len(resultados['monopolios'])}")

        if resultados.get("fragmentacion"):
            print(f"  ✓ Fragmentación: {resultados['fragmentacion']['num_componentes']} componentes")

    except Exception as e:
        print(f" Error en análisis avanzado: {e}")


    return df, G

if __name__ == "__main__":
    ejecutar_flujo_completo()
