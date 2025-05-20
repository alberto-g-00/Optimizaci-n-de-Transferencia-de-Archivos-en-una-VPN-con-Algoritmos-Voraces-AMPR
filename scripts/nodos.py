import socket
import json
import sys
import os

BUFFER_SIZE = 4096
PUERTO_NODO_PRINCIPAL = 5050

def enviar_archivo(ip_nodo_principal, ip_destino, nombre_archivo):
    if not os.path.exists(nombre_archivo):
        print(f"[ERROR] El archivo '{nombre_archivo}' no existe.")
        return

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip_nodo_principal, PUERTO_NODO_PRINCIPAL))

            # Crear metadatos
            metadata = json.dumps({
                'nombre': nombre_archivo,
                'destino': ip_destino
            }).encode()

            # Enviar longitud del JSON (10 bytes)
            s.sendall(f"{len(metadata):<10}".encode())

            # Enviar metadatos
            s.sendall(metadata)

            # Enviar archivo
            with open(nombre_archivo, 'rb') as f:
                while True:
                    chunk = f.read(BUFFER_SIZE)
                    if not chunk:
                        break
                    s.sendall(chunk)

            print("[Cliente] Archivo enviado correctamente al nodo principal")

    except Exception as e:
        print(f"[ERROR] No se pudo enviar el archivo: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python nodos.py <ip_nodo_principal> <ip_destino_final> <archivo>")
    else:
        ip_nodo = sys.argv[1]
        ip_destino = sys.argv[2]
        archivo = sys.argv[3]
        enviar_archivo(ip_nodo, ip_destino, archivo)
