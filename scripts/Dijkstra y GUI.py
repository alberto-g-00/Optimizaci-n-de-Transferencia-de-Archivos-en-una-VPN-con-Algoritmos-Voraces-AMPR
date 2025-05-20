import sys
import os
import time
import socket
import json
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import heapq

# Configuración de red
PUERTO_RECEPTOR = 5051
BUFFER_SIZE = 4096

#Ejecutar nodos.py en segundo plano
subprocess.Popen(["python", "nodos.py"])

# Definir los datos de la red (IPs y nombres)
nodos = {
    '100.101.1.1': 'Marco',
    '100.101.1.2': 'Poncho', 
    '100.101.1.3': 'Alberto',
    '100.101.1.4': 'Raúl'
}

# Grafo de latencias (ms)
grafo_latencia = {
    '100.101.1.1': {'100.101.1.2': 109, '100.101.1.3': 199, '100.101.1.4': 75},
    '100.101.1.2': {'100.101.1.1': 78, '100.101.1.3': 78, '100.101.1.4': 275},
    '100.101.1.3': {'100.101.1.1': 56, '100.101.1.2': 117, '100.101.1.4': 174},
    '100.101.1.4': {'100.101.1.1': 115, '100.101.1.2': 115, '100.101.1.3': 205}
}

# Grafo de ancho de banda (Mbps) - para referencia
grafo_ancho_banda = {
    '100.101.1.1': {'100.101.1.2': 23.2, '100.101.1.3': 23.1, '100.101.1.4': 26.2},
    '100.101.1.2': {'100.101.1.1': 80.0, '100.101.1.3': 3.95, '100.101.1.4': 11.3},
    '100.101.1.3': {'100.101.1.1': 22.0, '100.101.1.2': 2.08, '100.101.1.4': 21.7},
    '100.101.1.4': {'100.101.1.1': 83.1, '100.101.1.2': 4.58, '100.101.1.3': 6.46}
}

# Implementación del algoritmo de Dijkstra
def dijkstra(grafo, inicio, fin, use_latency=True):
    """
    Implementación del algoritmo de Dijkstra para encontrar la ruta más corta.
    
    Args:
        grafo: Diccionario de diccionarios con pesos (latencia o ancho de banda)
        inicio: Nodo inicial
        fin: Nodo final
        use_latency: Si True, minimiza latencia; si False, maximiza ancho de banda
        
    Returns:
        Distancia total y lista de nodos que forman la ruta
    """
    # Para ancho de banda, invertimos el problema para maximizar
    if not use_latency:
        # Crear una copia del grafo con valores inversos para maximizar ancho de banda
        grafo_invertido = {}
        for u in grafo:
            grafo_invertido[u] = {}
            for v, peso in grafo[u].items():
                # Usamos el inverso del ancho de banda
                grafo_invertido[u][v] = 1.0 / peso if peso > 0 else float('inf')
        grafo = grafo_invertido
    
    # Inicializar
    distancias = {nodo: float('inf') for nodo in grafo}
    distancias[inicio] = 0
    visitados = set()
    padres = {nodo: None for nodo in grafo}
    cola_prioridad = [(0, inicio)]
    
    while cola_prioridad:
        # Obtener el nodo de menor distancia
        distancia_actual, nodo_actual = heapq.heappop(cola_prioridad)
        
        # Si llegamos al destino, terminamos
        if nodo_actual == fin:
            break
            
        # Si ya visitamos el nodo, continuamos
        if nodo_actual in visitados:
            continue
            
        # Marcar como visitado
        visitados.add(nodo_actual)
        
        # Explorar vecinos
        for vecino, peso in grafo[nodo_actual].items():
            # Si el vecino no ha sido visitado
            if vecino not in visitados:
                nueva_distancia = distancia_actual + peso
                # Si encontramos un camino más corto
                if nueva_distancia < distancias[vecino]:
                    distancias[vecino] = nueva_distancia
                    padres[vecino] = nodo_actual
                    heapq.heappush(cola_prioridad, (nueva_distancia, vecino))
    
    # Reconstruir el camino
    ruta = []
    nodo_actual = fin
    while nodo_actual is not None:
        ruta.append(nodo_actual)
        nodo_actual = padres[nodo_actual]
    ruta.reverse()
    
    # Si no hay ruta
    if not ruta or ruta[0] != inicio:
        return float('inf'), []
    
    # Calcular el valor real (latencia total o ancho de banda mínimo)
    if use_latency:
        valor_total = distancias[fin]
    else:
        # Para ancho de banda, calculamos el cuello de botella (mínimo ancho de banda en la ruta)
        grafo_original = grafo_ancho_banda
        ancho_minimo = float('inf')
        for i in range(len(ruta) - 1):
            ancho = grafo_original[ruta[i]][ruta[i+1]]
            ancho_minimo = min(ancho_minimo, ancho)
        valor_total = ancho_minimo
    
    return valor_total, ruta

# Función para enviar un archivo a través de un nodo intermediario
def enviar_archivo_por_ruta(archivo, ip_origen, ruta, progress_var=None, status_label=None):
    """
    Envía un archivo siguiendo una ruta específica.
    
    Args:
        archivo: Ruta del archivo a enviar
        ip_origen: IP del nodo origen
        ruta: Lista de IPs que forman la ruta
        progress_var: Variable de tkinter para actualizar progreso
        status_label: Label de tkinter para actualizar estado
    
    Returns:
        Tiempo de transferencia en segundos
    """
    if len(ruta) < 2:
        if status_label:
            status_label.config(text="Error: La ruta debe tener al menos origen y destino")
        return 0
    
    ip_destino = ruta[-1]
    
    # Si es una transferencia directa (solo origen y destino)
    if len(ruta) == 2:
        inicio = time.time()
        
        try:
            if status_label:
                status_label.config(text=f"Enviando archivo directamente a {nodos[ip_destino]}...")
            
            # Crear una conexión directa al receptor
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip_destino, PUERTO_RECEPTOR))
                
                # Obtener tamaño del archivo
                tamano = os.path.getsize(archivo)
                
                # Crear metadatos
                metadata = json.dumps({
                    'nombre': os.path.basename(archivo),
                    'tamano': tamano
                }).encode()
                
                # Enviar longitud del JSON (10 bytes)
                s.sendall(f"{len(metadata):<10}".encode())
                
                # Enviar metadatos
                s.sendall(metadata)
                
                # Enviar archivo
                bytes_enviados = 0
                with open(archivo, 'rb') as f:
                    while True:
                        chunk = f.read(BUFFER_SIZE)
                        if not chunk:
                            break
                        s.sendall(chunk)
                        bytes_enviados += len(chunk)
                        
                        # Actualizar barra de progreso
                        if progress_var:
                            progress_var.set(bytes_enviados / tamano * 100)
                            status_label.config(text=f"Enviando: {bytes_enviados}/{tamano} bytes ({bytes_enviados/tamano*100:.1f}%)")
                            status_label.update()
                
            fin = time.time()
            tiempo_total = fin - inicio
            
            if status_label:
                status_label.config(text=f"Archivo enviado correctamente a {nodos[ip_destino]} en {tiempo_total:.2f} segundos")
            
            return tiempo_total
            
        except Exception as e:
            if status_label:
                status_label.config(text=f"Error al enviar archivo: {e}")
            return 0
    
    # Si la transferencia requiere nodos intermedios
    else:
        inicio = time.time()
        
        try:
            if status_label:
                status_label.config(text=f"Enviando archivo a {nodos[ip_destino]} a través de la ruta: {' -> '.join([nodos[ip] for ip in ruta])}")
            
            # Usar el script nodos.py para enviar al primer nodo de la ruta
            ip_primer_nodo = ruta[1]  # El siguiente después del origen
            
            # Comando para ejecutar el script nodos.py
            comando = ["python", "nodos.py", ip_primer_nodo, ip_destino, archivo]
            
            # Ejecutar el comando
            proceso = subprocess.Popen(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            salida, error = proceso.communicate()
            
            if proceso.returncode != 0:
                raise Exception(f"Error en el script nodos.py: {error.decode()}")
            
            fin = time.time()
            tiempo_total = fin - inicio
            
            if status_label:
                status_label.config(text=f"Archivo enviado correctamente a {nodos[ip_destino]} en {tiempo_total:.2f} segundos")
            
            return tiempo_total
            
        except Exception as e:
            if status_label:
                status_label.config(text=f"Error al enviar archivo: {e}")
            return 0

# Interfaz gráfica
class FileTransferGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Optimizador de Transferencia de Archivos")
        self.root.geometry("800x700")
        
        # Obtener IP local
        self.ip_local = self.detectar_ip_local()
        if not self.ip_local:
            messagebox.showerror("Error", "No se pudo detectar la IP local en la red VPN")
            self.root.destroy()
            return
        
        # Variables
        self.archivo_seleccionado = None
        self.ip_destino = tk.StringVar()
        self.usar_latencia = tk.BooleanVar(value=True)
        self.ruta_optima = []
        self.progreso = tk.DoubleVar()
        
        # Frame principal
        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superior (selección de archivo y destino)
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=10)
        
        # Etiqueta de nodo local
        ttk.Label(top_frame, text=f"Nodo local: {nodos[self.ip_local]} ({self.ip_local})").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Selección de archivo
        ttk.Label(top_frame, text="Archivo a transferir:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.archivo_label = ttk.Label(top_frame, text="Ningún archivo seleccionado")
        self.archivo_label.grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Button(top_frame, text="Seleccionar", command=self.seleccionar_archivo).grid(row=1, column=2, padx=5)
        
        # Selección de destino
        ttk.Label(top_frame, text="Nodo destino:").grid(row=2, column=0, sticky=tk.W, pady=5)
        destinos = [f"{nodos[ip]} ({ip})" for ip in nodos if ip != self.ip_local]
        destino_combo = ttk.Combobox(top_frame, textvariable=self.ip_destino, values=destinos, state="readonly")
        destino_combo.grid(row=2, column=1, sticky=tk.W+tk.E, pady=5)
        destino_combo.set(destinos[0] if destinos else "")
        
        # Opciones de optimización
        ttk.Label(top_frame, text="Optimizar por:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Radiobutton(top_frame, text="Latencia (más rápido)", variable=self.usar_latencia, value=True).grid(row=3, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(top_frame, text="Ancho de banda (mayor capacidad)", variable=self.usar_latencia, value=False).grid(row=4, column=1, sticky=tk.W, pady=2)
        
        # Botón para calcular ruta
        ttk.Button(top_frame, text="Calcular Ruta Óptima", command=self.calcular_ruta).grid(row=5, column=0, columnspan=3, pady=10)
        
        # Frame para visualización de la ruta
        self.ruta_frame = ttk.LabelFrame(main_frame, text="Ruta Calculada", padding=10)
        self.ruta_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Información de la ruta
        self.info_ruta = ttk.Label(self.ruta_frame, text="Calcule una ruta para mostrar la información")
        self.info_ruta.pack(anchor=tk.W, pady=5)
        
        # Canvas para el grafo
        self.fig = plt.Figure(figsize=(7, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, self.ruta_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Frame para transferencia de archivos
        self.transfer_frame = ttk.LabelFrame(main_frame, text="Transferencia de Archivos", padding=10)
        self.transfer_frame.pack(fill=tk.X, pady=10)
        
        # Botones de transferencia
        button_frame = ttk.Frame(self.transfer_frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="Transferir por Ruta Óptima", command=self.transferir_optima).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Transferir Directamente", command=self.transferir_directa).pack(side=tk.LEFT, padx=5)
        
        # Barra de progreso
        self.progress = ttk.Progressbar(self.transfer_frame, variable=self.progreso, maximum=100)
        self.progress.pack(fill=tk.X, pady=5)
        
        # Estado de la transferencia
        self.status_label = ttk.Label(self.transfer_frame, text="Listo para transferir")
        self.status_label.pack(anchor=tk.W, pady=5)
        
        # Frame para resultados
        self.results_frame = ttk.LabelFrame(main_frame, text="Resultados Comparativos", padding=10)
        self.results_frame.pack(fill=tk.X, pady=10)
        
        # Tabla de resultados
        self.tree = ttk.Treeview(self.results_frame, columns=("ruta", "tiempo", "diferencia"), show="headings")
        self.tree.heading("ruta", text="Ruta")
        self.tree.heading("tiempo", text="Tiempo (s)")
        self.tree.heading("diferencia", text="Diferencia (%)")
        self.tree.column("ruta", width=400)
        self.tree.column("tiempo", width=150)
        self.tree.column("diferencia", width=150)
        self.tree.pack(fill=tk.X, pady=5)
    
    def detectar_ip_local(self):
        """Detecta la IP local del nodo en la red VPN"""
        for ip in nodos.keys():
            try:
                # Intentar hacer un socket con la IP para ver si es local
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.bind((ip, 0))
                s.close()
                return ip
            except:
                continue
                
        # Si no podemos detectar, intentar con socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            # Verificar si la IP está en nuestros nodos
            if ip in nodos:
                return ip
        except:
            pass
            
        # Mostrar diálogo para selección manual
        ip_dialog = tk.Toplevel(self.root)
        ip_dialog.title("Seleccionar IP")
        ip_dialog.geometry("300x200")
        ip_dialog.transient(self.root)
        
        selected_ip = tk.StringVar()
        
        ttk.Label(ip_dialog, text="Seleccione su IP en la red VPN:").pack(pady=10)
        
        for ip, nombre in nodos.items():
            ttk.Radiobutton(ip_dialog, text=f"{nombre} ({ip})", variable=selected_ip, value=ip).pack(anchor=tk.W, padx=20)
        
        def confirm_ip():
            ip_dialog.destroy()
        
        ttk.Button(ip_dialog, text="Confirmar", command=confirm_ip).pack(pady=10)
        
        self.root.wait_window(ip_dialog)
        return selected_ip.get()
    
    def seleccionar_archivo(self):
        """Abre un diálogo para seleccionar un archivo"""
        archivo = filedialog.askopenfilename()
        if archivo:
            self.archivo_seleccionado = archivo
            nombre_archivo = os.path.basename(archivo)
            tamano = os.path.getsize(archivo)
            tamano_str = self.formatear_tamano(tamano)
            self.archivo_label.config(text=f"{nombre_archivo} ({tamano_str})")
    
    def formatear_tamano(self, tamano):
        """Formatea el tamaño en bytes a una representación más legible"""
        for unidad in ['B', 'KB', 'MB', 'GB']:
            if tamano < 1024.0:
                return f"{tamano:.2f} {unidad}"
            tamano /= 1024.0
        return f"{tamano:.2f} TB"
    
    def obtener_ip_destino(self):
        """Extrae la IP del texto seleccionado en el ComboBox"""
        texto = self.ip_destino.get()
        import re
        # Extraer la IP entre paréntesis
        match = re.search(r'\(([^)]+)\)', texto)
        if match:
            return match.group(1)
        return None
    
    def calcular_ruta(self):
        """Calcula la ruta óptima entre el origen y el destino"""
        if not self.archivo_seleccionado:
            messagebox.showwarning("Advertencia", "Seleccione un archivo primero")
            return
        
        ip_destino = self.obtener_ip_destino()
        if not ip_destino:
            messagebox.showwarning("Advertencia", "Seleccione un nodo destino válido")
            return
        
        # Grafo a usar según la optimización seleccionada
        grafo_usado = grafo_latencia if self.usar_latencia.get() else grafo_ancho_banda
        
        # Calcular ruta con Dijkstra
        valor, ruta = dijkstra(grafo_usado, self.ip_local, ip_destino, self.usar_latencia.get())
        
        # Mostrar información de la ruta
        if not ruta:
            self.info_ruta.config(text="No se pudo encontrar una ruta")
            return
        
        self.ruta_optima = ruta
        
        # Mostrar información
        if self.usar_latencia.get():
            self.info_ruta.config(
                text=f"Ruta óptima: {' -> '.join([nodos[ip] for ip in ruta])}\n"
                f"Latencia total: {valor} ms"
            )
        else:
            self.info_ruta.config(
                text=f"Ruta óptima: {' -> '.join([nodos[ip] for ip in ruta])}\n"
                f"Ancho de banda mínimo: {valor} Mbps"
            )
        
        # Visualizar la ruta en el grafo
        self.visualizar_ruta(ruta)
    
    def visualizar_ruta(self, ruta):
        """Visualiza la ruta calculada en un grafo"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        # Crear grafo con NetworkX
        G = nx.DiGraph()
        
        # Agregar todos los nodos
        for ip, nombre in nodos.items():
            G.add_node(ip, label=f"{nombre}\n({ip})")
        
        # Agregar todas las aristas con sus pesos
        grafo_usado = grafo_latencia if self.usar_latencia.get() else grafo_ancho_banda
        for u in grafo_usado:
            for v, peso in grafo_usado[u].items():
                G.add_edge(u, v, weight=peso)
        
        # Posiciones de los nodos
        pos = nx.circular_layout(G)
        
        # Dibujar nodos
        nx.draw_networkx_nodes(G, pos, node_color="lightblue", 
                              node_size=2000, alpha=0.8, ax=ax)
        
        # Dibujar aristas normales
        nx.draw_networkx_edges(G, pos, edge_color="gray", alpha=0.5, ax=ax)
        
        # Dibujar aristas de la ruta óptima
        ruta_aristas = [(ruta[i], ruta[i+1]) for i in range(len(ruta)-1)]
        nx.draw_networkx_edges(G, pos, edgelist=ruta_aristas, 
                              edge_color="red", width=3, ax=ax)
        
        # Etiquetas de nodos
        labels = {node: data['label'] for node, data in G.nodes(data=True)}
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=9, ax=ax)
        
        # Etiquetas de aristas (solo para la ruta óptima)
        edge_labels = {}
        for i in range(len(ruta)-1):
            u, v = ruta[i], ruta[i+1]
            weight = grafo_usado[u][v]
            unit = "ms" if self.usar_latencia.get() else "Mbps"
            edge_labels[(u, v)] = f"{weight} {unit}"
        
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, ax=ax)
        
        ax.set_title("Ruta Óptima para Transferencia de Archivos")
        ax.axis('off')
        
        self.canvas.draw()
    
    def transferir_optima(self):
        """Inicia la transferencia del archivo por la ruta óptima"""
        if not self.archivo_seleccionado:
            messagebox.showwarning("Advertencia", "Seleccione un archivo primero")
            return
            
        if not self.ruta_optima:
            messagebox.showwarning("Advertencia", "Calcule una ruta óptima primero")
            return
        
        # Resetear progreso
        self.progreso.set(0)
        
        # Iniciar transferencia en un hilo separado
        threading.Thread(
            target=self._transferir_y_actualizar, 
            args=(self.archivo_seleccionado, self.ip_local, self.ruta_optima, True)
        ).start()
    
    def transferir_directa(self):
        """Inicia la transferencia directa del archivo al destino"""
        if not self.archivo_seleccionado:
            messagebox.showwarning("Advertencia", "Seleccione un archivo primero")
            return
            
        ip_destino = self.obtener_ip_destino()
        if not ip_destino:
            messagebox.showwarning("Advertencia", "Seleccione un nodo destino válido")
            return
        
        # Resetear progreso
        self.progreso.set(0)
        
        # Ruta directa (origen -> destino)
        ruta_directa = [self.ip_local, ip_destino]
        
        # Iniciar transferencia en un hilo separado
        threading.Thread(
            target=self._transferir_y_actualizar, 
            args=(self.archivo_seleccionado, self.ip_local, ruta_directa, False)
        ).start()
    
    def _transferir_y_actualizar(self, archivo, ip_origen, ruta, es_optima):
        """Transfiere el archivo y actualiza la interfaz"""
        tipo_ruta = "óptima" if es_optima else "directa"
        nombre_archivo = os.path.basename(archivo)
        
        self.status_label.config(text=f"Iniciando transferencia {tipo_ruta} de {nombre_archivo}...")
        
        # Realizar la transferencia
        tiempo = enviar_archivo_por_ruta(
            archivo, ip_origen, ruta, 
            progress_var=self.progreso, 
            status_label=self.status_label
        )
        
        if tiempo > 0:
            # Descripción de la ruta
            descripcion_ruta = f"{' -> '.join([nodos[ip] for ip in ruta])}"
            
            # Agregar resultado a la tabla
            self.tree.insert("", "end", values=(
                f"{'Óptima' if es_optima else 'Directa'}: {descripcion_ruta}",
                f"{tiempo:.2f}",
                ""
            ))
            
            # Calcular diferencia si tenemos ambas mediciones
            items = self.tree.get_children()
            if len(items) >= 2:
                # Obtener tiempos
                tiempos = []
                for item in items:
                    valores = self.tree.item(item, "values")
                    tiempos.append(float(valores[1]))
                
                # Calcular porcentajes
                for i, item in enumerate(items):
                    valores = list(self.tree.item(item, "values"))
                    # Diferencia porcentual respecto al otro tiempo
                    otro_tiempo = tiempos[1-i]  # El otro tiempo en la lista
                    diferencia = (otro_tiempo - tiempos[i]) / otro_tiempo * 100
                    
                    # Actualizar valor
                    valores[2] = f"{diferencia:.2f}% {'menor' if diferencia > 0 else 'mayor'}"
                    self.tree.item(item, values=valores)
                    
            messagebox.showinfo("Transferencia Completada", 
                               f"Archivo {nombre_archivo} transferido exitosamente por ruta {tipo_ruta} en {tiempo:.2f} segundos")

# Función principal
def main():
    root = tk.Tk()
    app = FileTransferGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()