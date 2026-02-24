import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
from datetime import datetime
import sqlite3
import subprocess
import sys
import os
class AppPrincipal:
   def __init__(self, root):
       self.root = root
       self.root.title("MONITOR PRINCIPAL - Alumbrado Público")
       self.root.geometry("950x500")
       self.arduino = None
       self.proceso_respaldo = None
       self.setup_db()
       self.iniciar_servicio_respaldo()
       self.create_widgets()
       self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
       self.leer_serial()
   def setup_db(self):
       """Crea la base de datos compartida"""
       conn = sqlite3.connect("sistema_alumbrado.db")
       cursor = conn.cursor()
       # Tabla para comunicación en tiempo real
       cursor.execute('''CREATE TABLE IF NOT EXISTS estado_actual (
                           poste TEXT PRIMARY KEY, estado_led TEXT,
                           luz_ldr INTEGER, validacion TEXT, fecha_hora TEXT)''')
       conn.commit()
       conn.close()
   def iniciar_servicio_respaldo(self):
       """Lanza el script de segundo plano automáticamente"""
       try:
           script = "backup_service.py"
           if os.path.exists(script):
               self.proceso_respaldo = subprocess.Popen([sys.executable, script])
               print(">>> backup_service iniciado.")
       except Exception as e:
           print(f">>> Error al lanzar respaldo: {e}")
   def obtener_puertos_detallados(self):
       """Obtiene el puerto y el nombre del dispositivo conectado"""
       puertos = serial.tools.list_ports.comports()
       # Formato: 'COM5 (Arduino Uno)'
       return [f"{p.device} ({p.description})" for p in puertos]
   def actualizar_puertos(self):
       lista = self.obtener_puertos_detallados()
       self.combo_puertos['values'] = lista
       if lista: self.combo_puertos.current(0)
   def create_widgets(self):
       frame = tk.LabelFrame(self.root, text="Conexión de Hardware", padx=10, pady=5)
       frame.pack(fill="x", padx=10, pady=5)
       tk.Label(frame, text="Puerto Detectado:").pack(side=tk.LEFT)
       self.combo_puertos = ttk.Combobox(frame, width=50, state="readonly")
       self.combo_puertos.pack(side=tk.LEFT, padx=5)
       self.actualizar_puertos()
       tk.Button(frame, text="🔄", command=self.actualizar_puertos).pack(side=tk.LEFT, padx=2)
       tk.Button(frame, text="Conectar", command=self.conectar, bg="#d1e7ff").pack(side=tk.LEFT, padx=5)
       self.lbl_solar = tk.Label(frame, text="Luz Solar: --%", font=("Arial", 10, "bold"))
       self.lbl_solar.pack(side=tk.RIGHT, padx=10)
       self.tree = ttk.Treeview(self.root, columns=("P", "E", "L", "H", "V"), show='headings')
       columnas = [("P", "Poste"), ("E", "Estado LED"), ("L", "Luz LDR %"), ("H", "Hora PC"), ("V", "Validación")]
       for id_col, nombre in columnas:
           self.tree.heading(id_col, text=nombre)
           self.tree.column(id_col, anchor="center", width=120)
       self.tree.column("V", width=280)
       self.tree.pack(fill="both", expand=True, padx=10, pady=10)
   def conectar(self):
       seleccion = self.combo_puertos.get()
       if not seleccion: return
       # Extraer solo el puerto (ej: 'COM5') antes del primer espacio
       puerto_real = seleccion.split(" ")[0]
       try:
           self.arduino = serial.Serial(puerto_real, 9600, timeout=0.1)
           messagebox.showinfo("Éxito", f"Conectado a: {seleccion}")
       except Exception as e:
           messagebox.showerror("Error", f"No se pudo abrir el puerto {puerto_real}")
   def leer_serial(self):
       if self.arduino and self.arduino.in_waiting > 0:
           try:
               linea = self.arduino.readline().decode('utf-8', errors='ignore').strip()
               if "Luz Solar:" in linea: self.lbl_solar.config(text=linea)
               if "Poste #" in linea:
                   partes = linea.split('|')
                   n_p = partes[0].strip()
                   est = partes[1].split(':')[1].strip()
                   luz = int(partes[2].split(':')[1].replace('%','').strip())
                   hora = datetime.now().hour
                   val = "OPERACIÓN OK"
                   if est == "ON" and luz < 10: val = "FALLA: LED Fundido"
                   elif (hora >= 18 or hora < 6) and est == "OFF": val = "FALLA: Debería estar ON"
                   elif (6 <= hora < 18) and est == "ON": val = "FALLA: Debería estar OFF"
                   if "#1" in n_p:
                       for i in self.tree.get_children(): self.tree.delete(i)
                   self.tree.insert("", "end", values=(n_p, est, f"{luz}%", datetime.now().strftime("%H:%M:%S"), val))
                   # Guardar/Actualizar en BD
                   conn = sqlite3.connect("sistema_alumbrado.db")
                   conn.execute("INSERT OR REPLACE INTO estado_actual VALUES (?,?,?,?,?)",
                                (n_p, est, luz, val, datetime.now().strftime("%H:%M:%S")))
                   conn.commit()
                   conn.close()
           except: pass
       self.root.after(100, self.leer_serial)
   def on_closing(self):
       if self.proceso_respaldo: self.proceso_respaldo.terminate()
       if self.arduino: self.arduino.close()
       self.root.destroy()
if __name__ == "__main__":
   root = tk.Tk()
   app = AppPrincipal(root)
   root.mainloop()