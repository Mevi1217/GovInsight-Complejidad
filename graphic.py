from pyvis.network import Network


def create_network():
    """Crea el objeto de red configurado para visualización"""
    net = Network(
        height="900px",
        width="100%",
        notebook=False,
        cdn_resources="in_line",
        bgcolor="#121212",
        font_color="white",
        heading="Red de Órdenes de Compra - Ítems y Órdenes"
    )

    # Configuración visual y física del grafo
    net.set_options("""
    {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "font": {"size": 14, "color": "white"},
        "shadow": {"enabled": true, "size": 10}
      },
      "edges": {
        "color": {"inherit": false},
        "smooth": {"type": "continuous"},
        "shadow": {"enabled": true}
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -25000,
          "centralGravity": 0.3,
          "springLength": 160,
          "springConstant": 0.04,
          "damping": 0.09,
          "avoidOverlap": 0.6
        },
        "minVelocity": 0.75,
        "stabilization": {"iterations": 250, "fit": true}
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 120,
        "navigationButtons": true,
        "keyboard": {"enabled": true},
        "dragNodes": true,
        "dragView": true,
        "zoomView": true
      }
    }
    """)
    return net


def add_nodes(net, H, node_type):
    """Añade los nodos al grafo con sus propiedades y tooltips"""
    item_montos = {}

    # Calcular el monto total de compras por ítem
    for node in H.nodes():
        if H.nodes[node]['type'] == 'item':
            item_montos[node] = sum(H[node][neighbor]['weight'] for neighbor in H.neighbors(node))

    for node in H.nodes():
        data = H.nodes[node]
        degree = H.degree(node)

        if data['type'] == 'item':
            total_monto = item_montos.get(node, 0)
            avg_monto = total_monto / degree if degree > 0 else 0

            # Usar label_original si existe, sino usar label
            display_label = data.get('label_original', data['label'])[:50]

            tooltip = f"""
            <b>{node_type}:</b> {data.get('label_original', data['label'])}<br>
            <b>Órdenes conectadas:</b> {degree}<br>
            <b>Monto total comprado:</b> S/ {total_monto:,.2f}<br>
            <b>Promedio por orden:</b> S/ {avg_monto:,.2f}
            """

            net.add_node(
                node,
                label=display_label,
                title=tooltip,
                size=15 + degree * 2,
                color="#00d4a5",  
                shape="box",
                borderWidth=2
            )
        else:  # Nodo tipo 'orden'
            total_monto_orden = sum(H[node][neighbor]['weight'] for neighbor in H.neighbors(node))
            tooltip = f"""
            <b>Orden N°:</b> {data['label']}<br>
            <b>Ítems en orden:</b> {degree}<br>
            <b>Monto total:</b> S/ {total_monto_orden:,.2f}
            """

            net.add_node(
                node,
                label='',
                title=tooltip,
                size=10 + degree,
                color="#1e90ff", 
                shape="dot",
                borderWidth=1
            )


def add_edges(net, H):
    """Añade las aristas del grafo con grosor y color según monto"""
    if not H.edges:
        return 

    max_weight = max(d['weight'] for _, _, d in H.edges(data=True))

    for u, v, data in H.edges(data=True):
        weight = data['weight']

        # Colores según rango de monto (ajustados a montos en soles)
        edge_color = (
            '#ff6b6b' if weight > 5000 else  # Rojo para montos > S/ 5,000
            '#ffe66d' if weight > 1000 else  # Amarillo para montos S/ 1,000 - S/ 5,000
            '#95e1d3'  # Verde claro para montos < S/ 1,000
        )

        width = 1 + (weight / max_weight) * 4
        tooltip = f"<b>Monto de compra:</b> S/ {weight:,.2f}"

        net.add_edge(u, v, title=tooltip, color=edge_color, width=width)


def generate_legend_html(node_type, item_nodes, orden_nodes, edges_count):
    """Genera el HTML para la leyenda del grafo"""
    return f"""
<div style="
    position: fixed;
    top: 70px;
    right: 25px;
    background: rgba(25,25,25,0.95);
    padding: 25px;
    border-radius: 16px;
    border: 1px solid #444;
    font-family: Arial, sans-serif;
    color: white;
    z-index: 1000;
    width: 360px;
    box-shadow: 0 0 15px rgba(0,0,0,0.5);
">
    <h2 style="margin: 0 0 16px 0; color: #00d4a5; font-size: 22px;">Leyenda de la Red</h2>

    <p style="margin: 10px 0 12px 0; font-size: 16px;"><b>Nodos:</b></p>
    <div style="display: flex; flex-direction: column; gap: 10px; font-size: 15px;">
        <div><span style="display:inline-block;width:20px;height:20px;background:#00d4a5;border-radius:4px;margin-right:12px;"></span>{node_type}s</div>
        <div><span style="display:inline-block;width:20px;height:20px;background:#1e90ff;border-radius:50%;margin-right:12px;"></span>Órdenes de Compra</div>
    </div>

    <p style="margin: 16px 0 12px 0; font-size: 16px;"><b>Conexiones (Montos):</b></p>
    <div style="display:flex;flex-direction:column;gap:10px;font-size:15px;">
        <div><span style="display:inline-block;width:35px;height:6px;background:#ff6b6b;margin-right:12px;"></span>Mayor a S/ 5,000</div>
        <div><span style="display:inline-block;width:35px;height:6px;background:#ffe66d;margin-right:12px;"></span>S/ 1,000 - S/ 5,000</div>
        <div><span style="display:inline-block;width:35px;height:6px;background:#95e1d3;margin-right:12px;"></span>Menor a S/ 1,000</div>
    </div>

    <hr style="border-color:#555;margin:16px 0;">
    <p style="font-size:15px; line-height:1.8;">
        <b>{node_type}s:</b> {item_nodes}<br>
        <b>Órdenes:</b> {orden_nodes}<br>
        <b>Conexiones:</b> {edges_count}
    </p>

    <p style="font-size:14px; color:#bbb; margin-top:12px; line-height:1.6;">
        Usa el mouse para arrastrar nodos.<br>
        Zoom con la rueda del ratón.<br>
        Click para ver detalles.
    </p>
</div>
"""


def save_html(net, legend_html, output_file):
    """Guarda el archivo HTML incluyendo la leyenda"""
    html = net.generate_html()

    html = html.replace(
        '<div id="mynetwork"',
        '<div id="mynetwork" style="width:100vw; height:90vh; margin:0; padding:0;"'
    )

    html_final = html.replace("</body>", f"{legend_html}</body>")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_final)

    print(f"✓ Archivo de visualización guardado en: {output_file}")