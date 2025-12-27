from flask import Flask, render_template, redirect, url_for, request
import sys
from main import ejecutar_flujo_completo
from analyzer import (
    get_top_items_by_orders,
    get_top_items_by_monto,
    get_orders_per_item_distribution,
    analizar_interconexiones
)
from filter_graph import filter_subgraph
from graphic import create_network, add_nodes, add_edges, generate_legend_html, save_html

app = Flask(__name__)


class OutputCapture:
    def __init__(self):
        self.content = ""
    def write(self, s):
        self.content += s
    def flush(self):
        pass

df_global = None
G_global = None
top_items_global = None

@app.route("/")
def index():
    return render_template("index.html")

def ensure_data_loaded():
    global df_global, G_global, top_items_global
    if G_global is None or df_global is None:
        capture = OutputCapture()
        sys.stdout = capture
        df_global, G_global = ejecutar_flujo_completo()
        sys.stdout = sys.__stdout__
        # Calcular top items para filtrar subgrafo si es necesario
        item_nodes = [n for n in G_global.nodes() if G_global.nodes[n]['type'] == 'item']
        top_items_global = [(n, G_global.degree(n)) for n in item_nodes]
        top_items_global.sort(key=lambda x: x[1], reverse=True)

@app.route("/estadisticas")
def estadisticas():
    ensure_data_loaded()
    capture = OutputCapture()
    sys.stdout = capture
    from data_loader import print_statistics
    print("="*80)
    print(" ESTADÍSTICAS BÁSICAS".center(80))
    print("="*80)
    print_statistics(df_global, "Producto/Servicio")
    from analyzer import get_orders_per_item_distribution
    get_orders_per_item_distribution(G_global)
    sys.stdout = sys.__stdout__
    return capture.content

@app.route("/top-ordenes")
def top_ordenes():
    ensure_data_loaded()
    capture = OutputCapture()
    sys.stdout = capture
    get_top_items_by_orders(G_global, "Producto/Servicio")
    sys.stdout = sys.__stdout__
    return capture.content

@app.route("/top-montos")
def top_montos():
    ensure_data_loaded()
    capture = OutputCapture()
    sys.stdout = capture
    get_top_items_by_monto(G_global, "Producto/Servicio")
    sys.stdout = sys.__stdout__
    return capture.content

@app.route("/interconexiones")
def interconexiones():
    ensure_data_loaded()
    capture = OutputCapture()
    sys.stdout = capture
    analizar_interconexiones(G_global, "Producto/Servicio")
    sys.stdout = sys.__stdout__
    return capture.content

@app.route("/monopolios")
def monopolios():
    ensure_data_loaded()
    capture = OutputCapture()
    sys.stdout = capture
    from analisis_avanzado import detectar_monopolios
    resultados = detectar_monopolios(G_global, umbral_monto=5000)
    if resultados:
        for i, caso in enumerate(resultados[:10], 1):
            print(f"{i}. Item: {caso['item']} - Proveedores: {caso['num_proveedores']} - Monto: {caso['monto_total']}")
    sys.stdout = sys.__stdout__
    return capture.content

@app.route("/fragmentacion")
def fragmentacion():
    ensure_data_loaded()
    capture = OutputCapture()
    sys.stdout = capture
    from analisis_avanzado import analizar_fragmentacion_red
    analizar_fragmentacion_red(G_global)
    sys.stdout = sys.__stdout__
    return capture.content

@app.route("/optimizar")
def optimizar():
    ensure_data_loaded()
    capture = OutputCapture()
    sys.stdout = capture
    from analisis_avanzado import optimizar_compras_presupuesto_corregido
    optimizar_compras_presupuesto_corregido(G_global, presupuesto_total=100000)
    sys.stdout = sys.__stdout__
    return capture.content

@app.route("/rangos-montos")
def rangos_montos():
    ensure_data_loaded()
    capture = OutputCapture()
    sys.stdout = capture

    try:
        print("=" * 80)
        print(" ANÁLISIS DE RANGOS DE MONTOS (DIVIDE Y CONQUISTA)".center(80))
        print("=" * 80)

        from analisis_avanzado import analizar_montos_divide_conquista
        analizar_montos_divide_conquista(G_global)

    except Exception as e:
        print(f"\n ERROR AL EJECUTAR ANÁLISIS DE RANGOS DE MONTOS: {e}")
        import traceback
        traceback.print_exc(file=sys.stdout)

    sys.stdout = sys.__stdout__
    return capture.content

@app.route("/mst")
def mst():
    ensure_data_loaded()
    capture = OutputCapture()
    sys.stdout = capture
    try:
        from analisis_avanzado import ejecutar_mst_analisis
        ejecutar_mst_analisis(G_global)
    except Exception as e:
        print(f"Error ejecutando MST: {e}")
    sys.stdout = sys.__stdout__
    return capture.content

@app.route("/visualizar-mst")
def visualizar_mst():
    """Abre el grafo MST generado en otra pestaña"""
    return redirect(url_for('static', filename='mst_red_proveedores.html'), code=302)

@app.route("/generar-grafo")
def generar_grafo():
    """Abre grafo generado en otra pestaña"""

    return redirect("/static/graphs/grafo_compras_interactivo.html", code=302)

@app.route("/buscador", methods=["GET", "POST"])
def buscador_producto():
    ensure_data_loaded()
    
    if request.method == "POST":
        nombre_item = request.form.get("nombre_item")
        
        if nombre_item:
            from analyzer import buscar_item_y_estadisticas, formatear_resultado_busqueda
            
            # Ejecutar la lógica de negocio 
            resultado_bruto = buscar_item_y_estadisticas(G_global, nombre_item)
            
            if resultado_bruto:
                #Formatear la salida 
                output_formateado = formatear_resultado_busqueda(resultado_bruto)
                
                
                return render_template("buscador.html", resultado=output_formateado)
            else:
                return render_template("buscador.html", error=f"Ítem '{nombre_item}' no encontrado.")
                
    return render_template("buscador.html")


if __name__ == "__main__":
    app.run(debug=True)
