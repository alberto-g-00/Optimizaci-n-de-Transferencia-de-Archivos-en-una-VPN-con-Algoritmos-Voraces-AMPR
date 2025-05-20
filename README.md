# Optimización-de-Transferencia-de-Archivos-en-una-VPN-con-Algoritmos-Voraces-AMPR
En este algoritmo se creó una VPN la cual servirá para transferencia de archivos, se implementará el algoritmo de Dijkstra para optimizar la transferencia de archivos y el algoritmo de Kruskal para diseñar una topología de red eficiente.

A continuación se muestra cómo replicar el proyecto:

Primero, necesitas descargar tailscale para tu sistema operativo en los dispositivos que usarás:
https://tailscale.com/download

Una vez descargado, necesitas crear una cuenta en tailscale, e iniciar sesión en todos tus dispositivos con esta misma cuenta. 
La app te dirigirá a un explorador con una lista de los dispositivos que tienes conectados a la VPN, por lo que debes asignarles direcciones IP estáticas

Después se debe descargar la carpeta scripts, y colocarla en el lugar de tu preferencia, y esta carpeta se usará en un futuro.

Descargar y usar iPerf3 
1. Descarga 
Ingresa al siguiente enlace: 
👉 https://files.budman.pw/ 
Luego, selecciona la versión más reciente de iPerf3 disponible para tu sistema operativo. 
2. Preparación 
o Mueve el archivo ZIP que descargaste a tu carpeta.
o Descomprime el archivo ZIP. 
3. Acceso rápido a la terminal 
o Dentro de la carpeta descomprimida, entra a la subcarpeta donde esté el ejecutable. 
o Haz clic en la barra de direcciones del explorador de archivos, escribe cmd y presiona Enter para abrir la terminal directamente en esa ubicación. 
4. Ejecución 
o Si vas a actuar como servidor, ejecuta el siguiente comando: 
iperf3 -s 
o Si vas a actuar como cliente (para medir la latencia con el servidor), usa el siguiente comando (cambia la IP por la del servidor real): 
iperf3 -c 100.101.1.3

Para enviar archivos:
Una vez tienes esto listo, te vas a la carpeta scripts, donde, en la ruta (Explorador de archivos) escribes cmd y le das click a enter, una vez tienes el cmd abierto escribe:
python nodos.py 100.101.1.4(IP del servidor) 100.101.1.3(IP receptor) archivo.pdf(Nombre y formato dek archivo)
ENviado el archivo debes obtener el mensaje de si el archivo se envió y recibió en la computadora que funciona como servidor

Para recibir archivos:
Una vez tienes esto listo, te vas a la carpeta scripts, donde, en la ruta (Explorador de archivos) escribes cmd y le das click a enter, una vez tienes el cmd abierto escribe:
python receptor.py 
Debes obtener un mensaje de: [Receptor] Esperando archivos en el puerto X...
