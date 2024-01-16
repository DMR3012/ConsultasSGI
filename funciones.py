import re
from conexion import conectar_mysql
import mysql.connector
import tkinter as tk 
from tkinter import ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from tkinter import messagebox
from tkinter import Toplevel, Label
import tkinter.font as tkFont
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import datetime
#////////////////////////////    


#///////////////////////////
def mostrar_alerta(driver, mensaje):
    driver.execute_script(f"alert('{mensaje}');")
#////////////////////////////
def mostrar_alerta(driver, mensaje):
    messagebox.showinfo("Información obtenida", mensaje)

def consultar_rues_con_selenium_headless(entry_identificacion):
    identificacion = entry_identificacion.get()
    identificacion_limpia = limpiar_identificacion(identificacion)

    if not identificacion_limpia:
        messagebox.showinfo("Error", "Por favor, ingrese una identificación.")
        return None  # Retorna None para indicar que no se pudo realizar la consulta

    try:
        # Configuración para ejecutar en modo headless
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")  # Habilitar el modo headless

        # Iniciar el WebDriver con las opciones configuradas
        with webdriver.Chrome(options=chrome_options) as driver:
            driver.get("https://www.rues.org.co/RM")

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "txtSearchNIT")))

            input_identificacion = driver.find_element(By.ID, "txtSearchNIT")
            input_identificacion.clear()
            input_identificacion.send_keys(identificacion_limpia)

            driver.find_element(By.ID, "btnConsultaNIT").click()

            # Verificar si la consulta no ha retornado resultados
            no_resultado_element = driver.find_elements(By.XPATH, "//div[@id='card-info'][contains(@class, 'notice-info')][contains(text(), 'La consulta por NIT no ha retornado resultados')]")
            if no_resultado_element:
                messagebox.showinfo("Información", "La consulta por NIT no ha retornado resultados.")
                return "Información no obtenida"  # Retorna un mensaje indicando que no se obtuvo información

            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, "//table[@id='rmTable2']//tbody//td")))

            table_html = driver.find_element(By.ID, "rmTable2").get_attribute("outerHTML")
            soup = BeautifulSoup(table_html, 'html.parser')

            tbody = soup.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')

                for row in rows:
                    data_cells = row.find_all('td')
                    if data_cells:
                        # Extraer información
                        razon_social = data_cells[0].text.strip()
                        sigla = data_cells[1].text.strip()
                        nit_celda = data_cells[2].text.strip()  # Cambiado de nit a nit_celda
                        estado = data_cells[3].text.strip()
                        camara_comercio = data_cells[4].text.strip()
                        matricula = data_cells[5].text.strip()
                        organizacion_juridica = data_cells[6].text.strip()
                        categoria = data_cells[7].text.strip()

                        # Buscar el NIT completo dentro de la celda
                        nit_match = re.search(r'\b\d{8,12}\b', nit_celda)
                        nit_completo = nit_match.group() if nit_match else None
                        insertar_proveedor_en_db_rues(nit_completo, razon_social, estado, camara_comercio, matricula, organizacion_juridica, categoria)
                        # Verificar si el estado es "ACTIVA"
                        if estado == "ACTIVA":
                            # Mostrar información en un messagebox
                            data = (
                                f"Razón Social: {razon_social}\n"
                                f"Sigla: {sigla}\n"
                                f"NIT: {nit_completo}\n"
                                f"Estado: {estado}\n"
                                f"Cámara de Comercio: {camara_comercio}\n"
                                f"Matrícula: {matricula}\n"
                                f"Organización Jurídica: {organizacion_juridica}\n"
                                f"Categoría: {categoria}\n"
                            )
                            return data 

                                # Aquí debes insertar en la base de datos
                            insertar_proveedor_en_db_rues(nit, razon_social, estado, camara_comercio, matricula, organizacion_juridica, categoria)


            return "Consulta RUES completada exitosamente."  # Retorna un mensaje indicando que la consulta fue exitosa

    except TimeoutException:
        messagebox.showerror("Error", "Tiempo de espera agotado. La página puede haber tardado demasiado en cargar.")
        return None  # Retorna None para indicar que no se pudo realizar la consulta
    except NoSuchElementException as e:
        messagebox.showerror("Error", f"No se pudo encontrar el elemento: {type(e).__name__} - {str(e)}")
        return None  # Retorna None para indicar que no se pudo realizar la consulta
    except WebDriverException as e:
        messagebox.showerror("Error", f"Excepción del WebDriver: {str(e)}")
        return None  # Retorna None para indicar que no se pudo realizar la consulta
    except Exception as e:
        messagebox.showerror("Error", f"Ha ocurrido un error en la consulta: {type(e).__name__} - {str(e)}")
        return None  # Retorna None para indicar que no se pudo realizar la consulta
    
import datetime

def insertar_proveedor_en_db_rues(nit, razon_social, estado, camara_comercio, matricula, organizacion_juridica, categoria):
    try:
        # Conectar a la base de datos
        conn = conectar_mysql()
        cursor = conn.cursor()

        # Obtener la fecha actual
        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insertar en la tabla proveedorrues
        cursor.execute(
            f"INSERT INTO proveedorrues (ProvNit, ProvNombre, FechaRegistro, FechaUltimaActualizacion, Estado, CamaraComercio, Matricula, OrganizacionJuridica, NumeroVerificacion, Categoria) "
            f"VALUES ('{nit}', '{razon_social}', '{fecha_actual}', '{fecha_actual}', '{estado}', '{camara_comercio}', '{matricula}', '{organizacion_juridica}', NULL , '{categoria}') "
            f"ON DUPLICATE KEY UPDATE ProvNombre = '{razon_social}', FechaUltimaActualizacion = '{fecha_actual}', Estado = '{estado}', CamaraComercio = '{camara_comercio}', Matricula = '{matricula}', OrganizacionJuridica = '{organizacion_juridica}', Categoria = '{categoria}'"
        )
        conn.commit()  # Guardar cambios en la base de datos

        # Insertar en la tabla consultasrues
        
        conn.commit()  # Guardar cambios en la base de datos

        # Cerrar la conexión a la base de datos
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error en la inserción en la base de datos: {e}")
#///////////////////////////
# Función que realiza ambas consultas y muestra la información en un messagebox
def funciones_juntas(entry_identificacion):
    try:
        # Crear una ventana modal para el mensaje de carga
        loading_window = tk.Toplevel()
        loading_window.title("Cargando")

        # Etiqueta para el mensaje de carga
        loading_label = tk.Label(loading_window, text="Realizando consultas. Por favor, espere...")
        loading_label.pack(padx=20, pady=20)

        # Centrar la ventana de carga en la pantalla
        loading_window.update_idletasks()
        width = loading_window.winfo_width()
        height = loading_window.winfo_height()
        x = (loading_window.winfo_screenwidth() // 2) - (width // 2)
        y = (loading_window.winfo_screenheight() // 2) - (height // 2)
        loading_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        # Actualizar la interfaz gráfica para que se muestre la etiqueta de carga
        loading_window.update()

        # Consultar RUT
        resultado_rues = consultar_rues_con_selenium_headless(entry_identificacion)
        

        # Consultar RUES
        resultado_rut = consultar_rut_con_selenium_headless(entry_identificacion)

        # Cerrar la ventana de carga
        loading_window.destroy()

        # Mostrar la información en una nueva ventana
        if resultado_rut or resultado_rues:
            # Crear una ventana modal para mostrar la información
            info_window = tk.Toplevel()
            info_window.title("Información obtenida")

            # Construir el mensaje final
            mensaje_final = ""
            if resultado_rut:
                mensaje_final += f"Resultados RUT:\n{resultado_rut}\n\n"
            if resultado_rues:
                mensaje_final += f"Resultados RUES:\n{resultado_rues}"

            # Etiqueta para el mensaje final
            info_label = tk.Label(info_window, text=mensaje_final)
            info_label.pack(padx=20, pady=20)

            # Botón para cerrar la ventana de información
            cerrar_boton = tk.Button(info_window, text="Cerrar", command=info_window.destroy)
            cerrar_boton.pack(pady=10)

            # Centrar la ventana de información en la pantalla
            info_window.update_idletasks()
            width = info_window.winfo_width()
            height = info_window.winfo_height()
            x = (info_window.winfo_screenwidth() // 2) - (width // 2)
            y = (info_window.winfo_screenheight() // 2) - (height // 2)
            info_window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        else:
            messagebox.showinfo("Información", "No se obtuvo información de ninguna consulta.")

    except Exception as e:
        messagebox.showerror("Error", f"Ha ocurrido un error: {str(e)}")
#////////////////////////////

#///////////////////////////


def consultar_rut_con_selenium_headless(entry_identificacion):
    identificacion = entry_identificacion.get()
    identificacion_limpia = limpiar_identificacion(identificacion)

    if not identificacion_limpia:
        messagebox.showinfo("Error", "Por favor, ingrese una identificación.")
        return None  # Retorna None para indicar que no se pudo realizar la consulta

    # Configuración para ejecutar en modo headless
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")  # Habilitar el modo headless

    try:
        # Iniciar el WebDriver con las opciones configuradas
        with webdriver.Chrome(options=chrome_options) as driver:
            driver.get("https://muisca.dian.gov.co/WebRutMuisca/DefConsultaEstadoRUT.faces")

            input_identificacion = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:numNit")
            input_identificacion.send_keys(identificacion_limpia)

            boton_buscar = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:btnBuscar")
            boton_buscar.click()

            try:
                WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, "//font[contains(text(), 'El NIT')]")))
                mensaje_error = driver.find_element(By.XPATH, "//font[contains(text(), 'El NIT')]").text
                messagebox.showinfo("Error en la identificación", mensaje_error)
                return None  # Retorna None para indicar que no se obtuvo información

            except TimeoutException:
                pass

            razonSocial_element = None
            try:
                razonSocial_element = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:razonSocial")
            except NoSuchElementException:
                pass

            if razonSocial_element:
                numNit_element = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:numNit")
                numNit = numNit_element.get_attribute("value")
                dv = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:dv").text
                razonSocial = razonSocial_element.text
                fecha_actual_element = driver.find_element(By.XPATH, "//td[contains(text(), 'Fecha Actual')]/following-sibling::td[@class='tipoFilaNormalVerde']")
                fecha_str = fecha_actual_element.text if fecha_actual_element else "Fecha no encontrada"
                fecha_Actual=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Convertir la cadena de fecha a un objeto de fecha
                estado = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:estado").text
                conn=conectar_mysql()
                cursor=conn.cursor()
                cursor.execute(
                f"INSERT INTO proveedorrut (idProveedorRUT, NombreRUT, DvRUT, EstadoRUT) "
                f"VALUES ('{numNit}', '{razonSocial}', '{dv}', '{estado}') "
                f"ON DUPLICATE KEY UPDATE NombreRUT = '{razonSocial}', DvRUT = '{dv}', EstadoRUT = '{estado}'"
                )

# Segunda operación de inserción
                cursor.execute(
                f"INSERT INTO consultarr( Proveedor, FechaConsultaRUT,ProveedorId, ProveedorDv) "
                 f"VALUES('{razonSocial}','{fecha_Actual}','{numNit}','{dv}')"
                )

                conn.commit()
                # Construir la información en el formato deseado
                data = (
                    f"Razón Social: {razonSocial}\n"
                    f"NIT: {numNit}-{dv}\n"
                    f"Fecha de Consulta: {fecha_str}\n"
                    f"Estado: {estado}"
                )
                
                return data  # Retornar la información como una cadena de texto

            else:
                # Recolectar información adicional
                numNit = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:numNit").get_attribute("value")
                dv = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:dv").text

                # Apellidos
                primer_apellido = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:primerApellido").text
                segundo_apellido = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:segundoApellido").text
                apellidos = f"{primer_apellido} {segundo_apellido}"

                # Nombres
                primer_nombre = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:primerNombre").text
                otros_nombres = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:otrosNombres").text
                nombres = f"{primer_nombre} {otros_nombres}"

                # Fecha
                fecha_actual_element = driver.find_element(By.XPATH, "//td[contains(text(), 'Fecha Actual')]/following-sibling::td[@class='tipoFilaNormalVerde']")
                fecha_str = fecha_actual_element.text if fecha_actual_element else "Fecha no encontrada"

                # Convertir la cadena de fecha a un objeto de fecha
                fecha_Actual=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                estado = driver.find_element(By.ID, "vistaConsultaEstadoRUT:formConsultaEstadoRUT:estado").text
                conn=conectar_mysql()
                cursor=conn.cursor()
                cursor.execute(
                    f"INSERT INTO proveedorrut (idProveedorRUT, NombreRUT, DvRUT, EstadoRUT) "
                    f"VALUES ('{numNit}', '{apellidos} {nombres}', '{dv}', '{estado}') "
                    f"ON DUPLICATE KEY UPDATE NombreRUT = '{apellidos} {nombres}', DvRUT = '{dv}', EstadoRUT = '{estado}'"
                    
                )
                cursor.execute(
                    f"INSERT INTO consultarr( Proveedor, FechaConsultaRUT,ProveedorId, ProveedorDv)"
                    f"VALUES({apellidos} {nombres}','{fecha_Actual}','{numNit}','{dv}')"
                )
                conn.commit()
                # Construir la información en el formato deseado
                data = (
                    f"NIT: {numNit}-{dv}\n"
                    f"Nombre: {apellidos} {nombres}\n"
                    f"Fecha de Consulta: {fecha_str}\n"
                    f"Estado: {estado}"
                )
                
                return data  # Retornar la información como una cadena de texto
            
    except Exception as e:
        print(f"Error: {e}")
        return None  # Retorna None para indicar que no se pudo realizar la consulta
  # Retorna None para indicar que no se pudo realizar la consulta


# Funciones de limpieza y visualización de resultados
def limpiar_identificacion(identificacion):
    """
    The function `limpiar_identificacion` removes dots and dashes from an identification number.
    
    :param identificacion: The parameter "identificacion" is a string representing an identification
    number
    :return: the cleaned identification number without any dots or dashes.
    """
    identificacion_limpia = identificacion.replace('.', '').replace('-', '')
    return identificacion_limpia

def ver_consultas_identificacion(entry_identificacion):
    """
    The function `ver_consultas_identificacion()` retrieves and displays consultation records from a
    MySQL database based on a given identification number.
    """
    identificacion = entry_identificacion.get()
    identificacion_limpia = limpiar_identificacion(identificacion)
    
    try:
        conn = conectar_mysql()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM consultarr WHERE ProveedorId = '{identificacion_limpia}'")
        resultados = cursor.fetchall()
        conn.close()

        if resultados:
            mostrar_resultados(resultados, "Resultados de Consulta")
        else:
            messagebox.showinfo("No hay resultados", "No se encontraron consultas para esta identificación.")
    except mysql.connector.Error as e:
        print(f"Error al conectar a la base de datos: {e}")

#///////////////////
        
#//////////////////        






def ver_info_proveedor(entry_identificacion):
    """
    The function `ver_info_proveedor()` retrieves information about a supplier from a MySQL database
    based on their identification number.
    """
    identificacion = entry_identificacion.get()
    identificacion_limpia = limpiar_identificacion(identificacion)
    
    try:
        conn = conectar_mysql()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT rut.idProveedorRUT, rut.NombreRUT, rut.DvRUT, rut.EstadoRUT, r.ProvNit, r.ProvNombre, r.Estado, r.Categoria
            FROM proveedorrut rut
            JOIN proveedorrues r ON rut.idProveedorRUT = r.ProvNit
            WHERE rut.idProveedorRUT = '{identificacion_limpia}'
        """)
        resultados = cursor.fetchall()
        conn.close()

        if resultados:
            mostrar_resultados_proveedor(resultados, "Información de Proveedor")
        else:
            messagebox.showinfo("No hay resultados", "No se encontró proveedor para esta identificación.")
    except mysql.connector.Error as e:
        print(f"Error al conectar a la base de datos: {e}")

def mostrar_resultados_proveedor(resultados, title):
    root_resultados = tk.Toplevel()
    root_resultados.title(title)

    columns = ('idProveedorRUT', 'NombreRUT', 'DvRUT', 'EstadoRUT', 'ProvNit', 'ProvNombre', 'Estado', 'Categoria')
    tree = ttk.Treeview(root_resultados, columns=columns, show='headings')

    y_scrollbar = ttk.Scrollbar(root_resultados, orient='vertical', command=tree.yview)
    y_scrollbar.pack(side='right', fill='y')

    x_scrollbar = ttk.Scrollbar(root_resultados, orient='horizontal', command=tree.xview)
    x_scrollbar.pack(side='bottom', fill='x')

    tree.configure(yscroll=y_scrollbar.set, xscroll=x_scrollbar.set)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor='center')

    for resultado in resultados:
        tree.insert('', 'end', values=resultado)

    tree.pack(expand=True, fill='both')
    root_resultados.mainloop()

def mostrar_resultadosrues(resultados, title):
    """
    La función `mostrar_resultados` crea una nueva ventana y muestra una tabla con los resultados
    y un título.

    :param resultados: Una lista de resultados que se mostrarán en el treeview
    :param title: El parámetro title es una cadena que representa el título de la ventana donde
    se mostrarán los resultados
    """
    root_resultados = tk.Toplevel()
    root_resultados.title(title)

    columns = ('Id Consulta', 'Fecha Consulta', 'Proveedor Nit', 'Resultado Consulta')
    tree = ttk.Treeview(root_resultados, columns=columns, show='headings')
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor='center')
    
    # Obtener el ancho máximo del contenido en la columna 'Proveedor Nit'
    max_width_proveedor = max(len(str(row[2])) for row in resultados)  # Considerando que 'Proveedor Nit' es el tercer elemento (índice 2)

    # Establecer un ancho mínimo para la columna 'Proveedor Nit' (puedes ajustar este valor)
    tree.column('Proveedor Nit', width=max_width_proveedor * 10)  # Ajusta el ancho multiplicando por un factor adecuado

    for resultado in resultados:
        tree.insert('', 'end', values=resultado)

    tree.pack(expand=True, fill='both')
    root_resultados.mainloop()
#////////////////////////////
def mostrar_resultados(resultados, title):
    """
    La función `mostrar_resultados` crea una nueva ventana y muestra una tabla con los
    resultados y un título.

    :param resultados: Una lista de resultados que se mostrarán en el treeview
    :param title: El parámetro title es una cadena que representa el título de la ventana donde
    se mostrarán los resultados
    """
    root_resultados = tk.Toplevel()
    root_resultados.title(title)

    columns = ('Id Consulta', 'Proveedor', 'Fecha consulta', 'Identificación', 'DV')
    tree = ttk.Treeview(root_resultados, columns=columns, show='headings')
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor='center')

    # Obtener el ancho máximo del contenido en la columna 'Identificación'
    max_width_identificacion = max(len(str(row[3])) for row in resultados)  # Considerando que 'Identificación' es el cuarto elemento (índice 3)

    # Establecer un ancho mínimo para la columna 'Identificación' (puedes ajustar este valor)
    tree.column('Identificación', width=max_width_identificacion * 10)  # Ajusta el ancho multiplicando por un factor adecuado

    for resultado in resultados:
        tree.insert('', 'end', values=resultado)

    tree.pack(expand=True, fill='both')
    root_resultados.mainloop()
#////////////////////////////
def consultar_todos_los_resultados():
    # Esta función debería retornar todos los registros de la tabla 'consultarr'
    conn = conectar_mysql()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM consultarr")
    resultados = cursor.fetchall()

    conn.close()

    return resultados

def mostrar_tabla_completa():
    resultados_completos = consultar_todos_los_resultados()

    root_resultados = tk.Toplevel()
    root_resultados.title("Tabla Completa de consultarr")

    columns = ('Id Consulta', 'Proveedor', 'Fecha consulta', 'Identificación', 'DV')
    tree = ttk.Treeview(root_resultados, columns=columns, show='headings')
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor='center')

        # Obtener el ancho máximo del contenido en cada columna
        max_width = max(len(str(row[columns.index(col)])) for row in resultados_completos)
        
        # Establecer un ancho mínimo para la columna (puedes ajustar este valor)
        tree.column(col, width=max_width * 10)  # Ajusta el ancho multiplicando por un factor adecuado

    for resultado in resultados_completos:
        tree.insert('', 'end', values=resultado)

    tree.pack(expand=True, fill='both')
    root_resultados.mainloop()
    

#///////////////////////////
 
#//////////////////////////////////////////////////////////////

