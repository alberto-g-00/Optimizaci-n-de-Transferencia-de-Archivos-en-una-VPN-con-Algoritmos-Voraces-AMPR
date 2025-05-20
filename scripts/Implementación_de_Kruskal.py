import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import heapq

# Definir los datos de la red
nodos = {
    '100.101.1.1': 'Marco',
    '100.101.1.2': 'Poncho',
    '100.101.1.3': 'Alberto',
    '100.101.1.4': 'Raúl'
}

# Crear el grafo de ancho de banda (Mbps)
# como queremos maximizar el ancho de banda, usaremos el valor negativo
# para que al ordenar de menor a mayor, obtengamos los anchos de banda mayores primero
grafo_ancho_banda = {
    '100.101.1.1': {'100.101.1.2': 23.2, '100.101.1.3': 23.1, '100.101.1.4': 26.2},
    '100.101.1.2': {'100.101.1.1': 80.0, '100.101.1.3': 3.95, '100.101.1.4': 11.3},
    '100.101.1.3': {'100.101.1.1': 22.0, '100.101.1.2': 2.08, '100.101.1.4': 21.7},
    '100.101.1.4': {'100.101.1.1': 83.1, '100.101.1.2': 4.58, '100.101.1.3': 6.46}
}

# Tabla de latencias (ms) para referencia
grafo_latencia = {
    '100.101.1.1': {'100.101.1.2': 109, '100.101.1.3': 199, '100.101.1.4': 75},
    '100.101.1.2': {'100.101.1.1': 78, '100.101.1.3': 78, '100.101.1.4': 275},
    '100.101.1.3': {'100.101.1.1': 56, '100.101.1.2': 117, '100.101.1.4': 174},
    '100.101.1.4': {'100.101.1.1': 115, '100.101.1.2': 115, '100.101.1.3': 205}
}

# Función de Kruskal para encontrar el árbol de expansión máxima (maximizando ancho de banda)
def kruskal_max_bandwidth(grafo):
    """
    Implementación del algoritmo de Kruskal para encontrar el árbol de expansión máxima.
    Maximiza el ancho de banda total.
    
    Args:
        grafo: Diccionario de diccionarios con los anchos de banda
        
    Returns:
        Un conjunto de aristas que forman el MST
    """
    # Convertir el grafo en una lista de aristas (u, v, ancho_banda)
    aristas = []
    for u in grafo:
        for v, ancho_banda in grafo[u].items():
            # Solo incluimos una arista por cada par de nodos (la de mayor ancho de banda)
            # Verificamos si ya existe la arista inversa con mayor ancho de banda
            existe_inversa = False
            for idx, (u_existente, v_existente, banda_existente) in enumerate(aristas):
                if (u_existente == v and v_existente == u):
                    existe_inversa = True
                    if ancho_banda > banda_existente:
                        aristas[idx] = (u, v, ancho_banda)
                    break
            
            if not existe_inversa:
                aristas.append((u, v, ancho_banda))
    
    # Ordenar aristas por ancho de banda (de mayor a menor)
    aristas.sort(key=lambda x: x[2], reverse=True)
    
    # Conjunto de nodos
    nodos_set = set(grafo.keys())
    
    # Inicializar estructura para Union-Find
    padre = {nodo: nodo for nodo in nodos_set}
    rango = {nodo: 0 for nodo in nodos_set}
    
    # Función para encontrar el representante (líder) de un conjunto
    def encontrar(nodo):
        if padre[nodo] != nodo:
            padre[nodo] = encontrar(padre[nodo])  # Compresión de ruta
        return padre[nodo]
    
    # Función para unir dos conjuntos
    def unir(u, v):
        raiz_u = encontrar(u)
        raiz_v = encontrar(v)
        
        if raiz_u != raiz_v:
            # Union by rank para mantener el árbol balanceado
            if rango[raiz_u] < rango[raiz_v]:
                padre[raiz_u] = raiz_v
            else:
                padre[raiz_v] = raiz_u
                if rango[raiz_u] == rango[raiz_v]:
                    rango[raiz_u] += 1
    
    # MST (Maximum Spanning Tree)
    mst = []
    
    # Algoritmo de Kruskal (adaptado para maximizar)
    for u, v, ancho_banda in aristas:
        if encontrar(u) != encontrar(v):  # Si no forman un ciclo
            unir(u, v)
            mst.append((u, v, ancho_banda))
            
            # Detener cuando tengamos n-1 aristas (MST completo)
            if len(mst) == len(nodos_set) - 1:
                break
                
    return mst

# Función para visualizar el grafo original y el MST
def visualizar_grafos(grafo_original, mst, nodos_nombres):
    # Crear grafo original con NetworkX
    G_original = nx.Graph()
    
    # Agregar nodos con etiquetas
    for ip, nombre in nodos_nombres.items():
        G_original.add_node(ip, label=f"{nombre}\n{ip}")
    
    # Agregar aristas del grafo original (solo la de mayor ancho de banda entre cada par)
    aristas_procesadas = set()
    for u in grafo_original:
        for v, ancho_banda in grafo_original[u].items():
            # Verificar si ya procesamos esta arista
            if (u, v) not in aristas_procesadas and (v, u) not in aristas_procesadas:
                # Comparar con la arista inversa y tomar la de mayor ancho de banda
                ancho_banda_inverso = grafo_original.get(v, {}).get(u, 0)
                if ancho_banda >= ancho_banda_inverso:
                    G_original.add_edge(u, v, weight=ancho_banda, bandwidth=f"{ancho_banda} Mbps")
                else:
                    G_original.add_edge(v, u, weight=ancho_banda_inverso, bandwidth=f"{ancho_banda_inverso} Mbps")
                aristas_procesadas.add((u, v))
    
    # Crear grafo MST con NetworkX
    G_mst = nx.Graph()
    
    # Agregar nodos con etiquetas
    for ip, nombre in nodos_nombres.items():
        G_mst.add_node(ip, label=f"{nombre}\n{ip}")
    
    # Agregar aristas del MST
    for u, v, ancho_banda in mst:
        G_mst.add_edge(u, v, weight=ancho_banda, bandwidth=f"{ancho_banda} Mbps")
    
    # Posiciones de los nodos (layout circular para mejor visualización)
    pos = nx.circular_layout(G_original)
    
    # Configurar tamaño de la figura
    plt.figure(figsize=(15, 7))
    
    # Visualizar grafo original
    plt.subplot(1, 2, 1)
    
    # Dibujar nodos
    nx.draw_networkx_nodes(G_original, pos, node_color="lightblue", 
                          node_size=2500, alpha=0.8)
    
    # Dibujar aristas con grosor proporcional al ancho de banda
    for (u, v, data) in G_original.edges(data=True):
        nx.draw_networkx_edges(G_original, pos, edgelist=[(u, v)], 
                              width=data['weight']/10, alpha=0.7)
    
    # Etiquetas de nodos
    node_labels = {node: data['label'] for node, data in G_original.nodes(data=True)}
    nx.draw_networkx_labels(G_original, pos, labels=node_labels, font_size=10)
    
    # Etiquetas de aristas
    edge_labels = {(u, v): data['bandwidth'] for u, v, data in G_original.edges(data=True)}
    nx.draw_networkx_edge_labels(G_original, pos, edge_labels=edge_labels, font_size=8)
    
    plt.title("Topología Original (Ancho de Banda)")
    plt.axis('off')
    
    # Visualizar MST
    plt.subplot(1, 2, 2)
    
    # Dibujar nodos
    nx.draw_networkx_nodes(G_mst, pos, node_color="lightgreen", 
                          node_size=2500, alpha=0.8)
    
    # Dibujar aristas con grosor proporcional al ancho de banda
    for (u, v, data) in G_mst.edges(data=True):
        nx.draw_networkx_edges(G_mst, pos, edgelist=[(u, v)], 
                              width=data['weight']/10, alpha=0.7, edge_color='red')
    
    # Etiquetas de nodos
    nx.draw_networkx_labels(G_mst, pos, labels=node_labels, font_size=10)
    
    # Etiquetas de aristas
    edge_labels = {(u, v): data['bandwidth'] for u, v, data in G_mst.edges(data=True)}
    nx.draw_networkx_edge_labels(G_mst, pos, edge_labels=edge_labels, font_size=8)
    
    plt.title("Árbol de Expansión Mínima (MST)")
    plt.axis('off')
    
    plt.tight_layout()
    plt.savefig("topologia_comparacion_ancho_banda.png", dpi=300, bbox_inches='tight')
    plt.show()
    
    return G_original, G_mst

# Ejecutar el algoritmo de Kruskal para maximizar el ancho de banda
mst = kruskal_max_bandwidth(grafo_ancho_banda)

# Mostrar resultado
print("Árbol de Expansión Mínima (MST) - Minimizar Ancho de Banda:")
total_ancho_banda = 0
for u, v, ancho_banda in mst:
    print(f"Conexión: {nodos[u]} ({u}) -- {nodos[v]} ({v}), Ancho de Banda: {ancho_banda} Mbps")
    total_ancho_banda += ancho_banda
print(f"Ancho de banda total del MST: {total_ancho_banda} Mbps")

# Visualizar los grafos
G_original, G_mst = visualizar_grafos(grafo_ancho_banda, mst, nodos)

# Análisis de eficiencia
# Para el grafo original, sumamos el ancho de banda máximo entre cada par de nodos
ancho_banda_original = 0
aristas_procesadas = set()
for u in grafo_ancho_banda:
    for v, ancho_banda in grafo_ancho_banda[u].items():
        if (u, v) not in aristas_procesadas and (v, u) not in aristas_procesadas:
            ancho_banda_inverso = grafo_ancho_banda.get(v, {}).get(u, 0)
            ancho_banda_original += max(ancho_banda, ancho_banda_inverso)
            aristas_procesadas.add((u, v))

# Porcentaje de eficiencia
porcentaje_eficiencia = (total_ancho_banda / ancho_banda_original) * 100

print(f"\nAnálisis de Eficiencia:")
print(f"Ancho de banda total de todas las conexiones originales: {ancho_banda_original} Mbps")
print(f"Ancho de banda total del MST: {total_ancho_banda} Mbps")
print(f"Eficiencia del MST: {porcentaje_eficiencia:.2f}% del ancho de banda original")
print(f"Reducción de conexiones: {len(grafo_ancho_banda) * (len(grafo_ancho_banda) - 1) // 2 - len(mst)} conexiones eliminadas")

# Generar tabla comparativa entre topología original y MST
tabla_comparativa = []
for nodo_origen in nodos:
    for nodo_destino in nodos:
        if nodo_origen != nodo_destino:
            # Verificar si esta conexión existe en el MST
            esta_en_mst = False
            for u, v, _ in mst:
                if (u == nodo_origen and v == nodo_destino) or (u == nodo_destino and v == nodo_origen):
                    esta_en_mst = True
                    break
            
            # Agregar a la tabla
            tabla_comparativa.append({
                'Origen': nodos[nodo_origen],
                'IP Origen': nodo_origen,
                'Destino': nodos[nodo_destino],
                'IP Destino': nodo_destino,
                'Ancho de Banda (Mbps)': grafo_ancho_banda[nodo_origen][nodo_destino],
                'Latencia (ms)': grafo_latencia[nodo_origen][nodo_destino],
                'En MST': 'Sí' if esta_en_mst else 'No'
            })

# Convertir a DataFrame y mostrar
df_comparativo = pd.DataFrame(tabla_comparativa)
print("\nTabla Comparativa:")
print(df_comparativo)

# Guardar tabla como CSV
df_comparativo.to_csv('comparativa_topologia.csv', index=False)
print("Tabla comparativa guardada como 'comparativa_topologia.csv'")