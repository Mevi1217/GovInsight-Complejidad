import pandas as pd
import warnings
import re
import unicodedata

warnings.filterwarnings('ignore')

# 1. CONSTANTES DE LIMPIEZA
# Palabras que indican que lo que sigue es irrelevante para identificar el producto
PALABRAS_CORTE = [
    " para ", " en el ", " en la ", " del ", " de la ",
    " con la ", " segun ", " según ", " correspondiente ",
    " solicitado ", " meta ", " componente ", " obra:",
    " proyecto:", " actividad:", " - ", " incluye ",
    " inlcuye ",
    " con ",
    ":"
]

# Mapeo de sinónimos para agrupar productos idénticos con nombres distintos
SINONIMOS = {
    "petroleo": "diesel",
    "diesel": "diesel",
    "gasohol": "gasolina",
    "gasolina": "gasolina",
    "papel bond": "papel bond",
    "hojas bond": "papel bond",
    "tinta": "tinta de impresion",
    "toner": "toner",
    "cemento": "cemento",
    "ladrillo": "ladrillo",
    "agua de mesa": "agua de mesa",
    "agua mineral": "agua de mesa",
    "agua para consumo": "agua de mesa",
    "bebidas": "agua y bebidas",
    "gaseosa": "agua y bebidas",
    "lapicero": "boligrafo",
    "boligrafo": "boligrafo",
    "bloqueador": "protector solar",
    "soat": "seguro vehicular soat",
    "triplay": "triplay",
    "computadora": "computadora",
    "laptop": "computadora"
}


def quitar_tildes(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def normalize_products(text):
    """
    Normaliza descripciones complejas de compras estatales a categorías estándar.
    Ej: "ADQ. DE DIESEL B5 S50 PARA LA OBRA X" -> "diesel"
    """
    if not isinstance(text, str):
        return "desconocido"

    # A. Limpieza básica
    text = text.lower().strip()
    text = quitar_tildes(text)

    # B. ELIMINAR PREFIJOS ADMINISTRATIVOS
    # Borra: "adquisicion de", "servicio de", "compra de", "suministro de"
    text = re.sub(r"^(adqui\w+|adq\.|adq|contrat\w+|compra|suministro)\s*(de)?\s*", "", text)

    # Mantener "servicio" si es explícito, pero limpiarlo
    if text.startswith("servicio"):
        text = re.sub(r"^(servicio)\s*(de)?\s*", "servicio ", text)

        # C. CORTE AGRESIVO DE CONTEXTO
    # Si encuentra " para la obra...", borra todo lo que sigue.
    for corte in PALABRAS_CORTE:
        if corte in text:
            text = text.split(corte)[0]

    # D. LIMPIEZA DE ESPECIFICACIONES TÉCNICAS (Ruido numérico)
    text = re.sub(r"\bx\s*\d+.*", "", text)  # Borra "x 20 litros", "x 400g"
    # Borra unidades técnicas: 80g, 42.5kg, 20l, 500ml, etc.
    text = re.sub(r"\b\d+(\.\d+)?\s*(gr|g|kg|ml|l|gal|hp|mm|cm|in|watts|w)\b", "", text)
    text = re.sub(r"\btamaño\s*a\d", "", text)  # Borra "tamaño a4", "a3"
    text = re.sub(r"[^\w\s]", "", text)  # Borra caracteres especiales sobrantes

    # E. REGLAS CATEGÓRICAS (Agrupación forzada)
    # Si contiene estas palabras clave, forzamos el nombre de la categoría
    if "utiles" in text and ("escritorio" in text or "oficina" in text):
        return "utiles de escritorio"
    if "limpieza" in text and ("material" in text or "insumo" in text or "utiles" in text or "aseo" in text):
        return "materiales de limpieza"
    if "proteccion" in text and ("personal" in text or "epp" in text or "seguridad" in text):
        return "equipos de proteccion personal epp"
    if "vestuario" in text or "indumentaria" in text or "uniforme" in text or "camisa" in text or "polo" in text:
        return "vestuario institucional"
    if "alquiler" in text and ("camioneta" in text or "vehiculo" in text or "minivan" in text):
        return "alquiler de camioneta"
    if "energia electrica" in text or "suministro de energia" in text:
        return "servicio de energia electrica"
    if "seguridad" in text and ("temporal" in text or "vigilancia" in text):
        return "servicio de seguridad y vigilancia"
    if "consultoria" in text:
        return "servicio de consultoria"

    # F. AGRUPACIÓN SEMÁNTICA (Sinónimos)
    for clave, valor_estandar in SINONIMOS.items():
        # Busca la palabra clave como palabra completa
        if re.search(r"\b" + re.escape(clave) + r"\b", text):
            # Excepción: No convertir "camioneta diesel" en solo "diesel"
            if "camioneta" not in text and "alquiler" not in text:
                return valor_estandar

    # G. Limpieza final de espacios dobles
    text = re.sub(r"\s+", " ", text).strip()

    return text


def load_data(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8', sep=';')
        print("Archivo CSV cargado exitosamente con delimitador ';'")
        return df
    except Exception as e:
        print(f" Intento con ';' falló: {e}")
        return None


def clean_data(df, filtro_tipo=None):
    if df is None:
        return None

    original_len = len(df)

    print(f"Columnas encontradas: {list(df.columns)}")
    print()

    # Eliminar filas vacías clave
    df = df.dropna(subset=["ORDEN_NUMERO", "ORDEN_DESCRIPCION"])
    print(f"Registros eliminados (sin ORDEN_NUMERO o ORDEN_DESCRIPCION): {original_len - len(df)}")

    # Filtro opcional por tipo (Producto/Servicio)
    if filtro_tipo is not None:
        antes_filtro = len(df)
        if isinstance(filtro_tipo, list):
            df = df[df['ORDEN_TIPO'].isin(filtro_tipo)]
            tipo_str = f"tipos {filtro_tipo}"
        else:
            df = df[df['ORDEN_TIPO'] == filtro_tipo]
            tipo_str = f"tipo {filtro_tipo} ({'Productos' if filtro_tipo == 1 else 'Servicios'})"

        print(f"✓ Filtrado por {tipo_str}: {len(df)} registros (excluidos: {antes_filtro - len(df)})")

    # Limpieza de textos básicos
    df["ORDEN_NUMERO"] = df["ORDEN_NUMERO"].astype(str).str.strip()
    df["ORDEN_DESCRIPCION"] = df["ORDEN_DESCRIPCION"].astype(str).str.strip()

    # ID Único temporal (aunque puede haber duplicados si la orden tiene varios ítems)
    df["ITEM_ID"] = df["ORDEN_NUMERO"] + "_" + df["ORDEN_DESCRIPCION"]

    # --- NORMALIZACIÓN AVANZADA ---
    print("Aplicando normalización avanzada de productos...")
    df["ORDEN_DESCRIPCION_NORM"] = df["ORDEN_DESCRIPCION"].apply(normalize_products)

    # Limpiar columna ORDEN_MONTO (manejo robusto de S/, comas y espacios)
    if df["ORDEN_MONTO"].dtype == 'object':
        df["ORDEN_MONTO"] = (df["ORDEN_MONTO"]
                             .astype(str)
                             .str.replace("S/", "", regex=False)
                             .str.replace("S/ ", "", regex=False)
                             .str.replace(",", "", regex=False)  # Quitar comas de miles
                             .str.strip())

    df["ORDEN_MONTO"] = pd.to_numeric(df["ORDEN_MONTO"], errors='coerce').fillna(0)

    # Filtrar órdenes con monto positivo (eliminar errores o anulaciones)
    df = df[df["ORDEN_MONTO"] > 0]
    print(f"✓ Registros válidos para análisis: {len(df):,}")

    # Mostrar distribución por tipo si existe la columna
    if 'ORDEN_TIPO' in df.columns:
        print("\nDistribución por tipo:")
        for tipo in sorted(df['ORDEN_TIPO'].unique()):
            count = len(df[df['ORDEN_TIPO'] == tipo])
            tipo_nombre = "Productos" if tipo == 1 else f"Tipo {tipo}"
            print(f"  - {tipo_nombre}: {count:,} registros")
    print()

    return df


def print_statistics(df, nodo_tipo):
    if df is None: return

    print("Datos de ordenes e items de compra:")
    print()
    print(f"Número de órdenes únicas: {df['ORDEN_NUMERO'].nunique():,}")
    print(f"Número de ítems únicos: {df['ORDEN_DESCRIPCION_NORM'].nunique():,}")
    print(f"Monto total: S/ {df['ORDEN_MONTO'].sum():,.2f}")
    print(f"Monto promedio por ítem: S/ {df['ORDEN_MONTO'].mean():,.2f}")
    print(f"Monto mínimo: S/ {df['ORDEN_MONTO'].min():,.2f}")
    print(f"Monto máximo: S/ {df['ORDEN_MONTO'].max():,.2f}")
    print()