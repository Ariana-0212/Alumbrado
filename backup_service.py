import tkinter as tk
from tkinter import messagebox, filedialog
import sqlite3
import csv
from datetime import datetime
class BackupService:
   def __init__(self, root):
       self.root = root
       self.root.title("BACKEND - backup_service")
       self.root.geometry("350x150")
       self.horas_objetivo = [18, 21, 0, 3, 6]
       self.ultima_hora_ejecutada = -1
       tk.Label(root, text="Servicio de Almacenamiento", fg="#2c3e50", font=("Arial", 10, "bold")).pack(pady=10)
       self.lbl_status = tk.Label(root, text="Vigilando horarios de guardado...")
       self.lbl_status.pack()
       self.verificar_y_guardar()
   def verificar_y_guardar(self):
       ahora = datetime.now()

       if ahora.hour in self.horas_objetivo and ahora.hour != self.ultima_hora_ejecutada:
           self.ejecutar_persistencia(ahora.hour)
           self.ultima_hora_ejecutada = ahora.hour
       self.root.after(30000, self.verificar_y_guardar)
   def ejecutar_persistencia(self, hora_actual):
       try:
           conn = sqlite3.connect("sistema_alumbrado.db")
           cursor = conn.cursor()
           # Obtener datos del estado actual
           cursor.execute("SELECT * FROM estado_actual")
           datos = cursor.fetchall()
           if datos:
               # 1. GUARDAR EN BD 
               cursor.execute('''CREATE TABLE IF NOT EXISTS historico
                               (fecha_registro TEXT, poste TEXT, estado TEXT, luz TEXT, validacion TEXT)''')
               for fila in datos:

                   cursor.execute("INSERT INTO historico VALUES (?,?,?,?,?)",
                                  (fila[4], fila[0], fila[1], fila[2], fila[3]))
               conn.commit()
               print(f"Datos de las {hora_actual}:00 guardados en tabla Histórico.")
               # 2. PROCESO DE CSV PERSONALIZADO
               self.lbl_status.config(text=f"Registro {hora_actual}:00 guardado en BD.", fg="blue")
               if messagebox.askyesno("Guardado Programado", f"Son las {hora_actual}:00. ¿Desea crear un archivo CSV?"):
                   ruta_archivo = filedialog.asksaveasfilename(
                       defaultextension=".csv",
                       filetypes=[("Archivo CSV", "*.csv")],
                       title="Nombre del reporte CSV",
                       initialfile=f"Reporte_Nocturno_{hora_actual}hrs"
                   )
                   if ruta_archivo:
                       with open(ruta_archivo, 'w', newline='') as f:
                           writer = csv.writer(f)
                           writer.writerow(["Fecha", "ID Poste", "Estado LED", "Luz LDR", "Validación"])
                           writer.writerows(datos)
                       messagebox.showinfo("Éxito", "El CSV ha sido generado correctamente.")
           conn.close()
       except Exception as e:
           print(f"Error en persistencia: {e}")
if __name__ == "__main__":
   root = tk.Tk()
   root.attributes("-topmost", True) # Asegura que la pregunta del CSV no se esconda
   app = BackupService(root)
   root.mainloop()