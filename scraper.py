# Importación de módulos necesarios de Selenium
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import Select
from datetime import datetime, timedelta


class scraper:

	def __init__(self, path_driver,link_main,date_from,date_until):
		self.path_driver = path_driver
		self.driver = None 
		self.link_main = link_main
		self.date_from = date_from
		self.date_until = date_until


	def initialize_driver(self):
		# Crea opciones de configuración para el controlador Chrome.
		chrome_options = webdriver.ChromeOptions() 
		# Configura la ubicación del ejecutable del controlador.
		chrome_options.add_argument("executable_path=" + self.path_driver)  
		# Inicializa el controlador de Chrome con las opciones.
		self.driver = webdriver.Chrome(options=chrome_options)  

	# PRINCIPAL METHOD
	def filter_jurisprudencia(self):

		while True :

			try :

				self.driver.get( self.link_main )
				# Encuentra y llena el campo "Fecha Desde" en la página web
				fecha_desde = self.driver.find_element(By.ID, "formBusqueda:j_id20:j_id23:fechaDesdeCalInputDate")
				fecha_desde.send_keys(self.date_from)

				# Encuentra y llena el campo "Fecha Hasta" en la página web
				fecha_hasta = self.driver.find_element(By.ID, "formBusqueda:j_id20:j_id147:fechaHastaCalInputDate")
				fecha_hasta.send_keys(self.date_until)
				# Simula presionar la tecla Enter
				self.select_option_by_value()

				fecha_hasta.send_keys(Keys.ENTER)

				print('\n ESPERANDO \n')

				time.sleep(2)

				number_pages = self.extract_npages()
				print(number_pages)
				

				# # for page in tqdm(range(1,number_pages+1)) :
				for page in tqdm(range(1,10)) :

					# print(f'\n PAGINA NUMERO : { page } \n')

					fecha_str = self.extract_document()

					if fecha_str != 0 :
					
						print('\n SURGIO UN ERROR , VAMOS POR EL DIA SIGUIENTE \n')
						print(f'\nlast date : { fecha_str }\n')
						fecha = datetime.strptime(fecha_str, '%d/%m/%Y')
						# Suma un día
						nueva_fecha = fecha + timedelta(days=1)
						# Convierte la nueva fecha en una cadena de texto
						nueva_fecha_str = nueva_fecha.strftime('%d/%m/%Y')
						print(f'\nnueva_fecha_str : {nueva_fecha_str}\n')

						self.date_from = nueva_fecha_str

					else :
						print('\nVAMOS A CAMBIAR DE PAGINA\n')
						self.change_page()

					time.sleep(1)

			except Exception:
				print('ERROR EL METODO DE FILTER JURISPRUDENCIA')
				# self.date_from = last_date


	def extract_document(self):

		dict_aux = {}
		list_total = []
		
		try:

			for sample in range(0,10) :		

				segundo_elemento= self.driver.find_element(By.ID, f"formResultados:dataTable:{sample}:colFec")
				segundo_elemento.click()
				# print('Esperando 1 segundo')
				time.sleep(1)

				# Cambia al manejo de la ventana emergente recién abierta
				ventana_actual = self.driver.window_handles[0]  # 0 es el índice de la ventana principal
				ventana_emergente = self.driver.window_handles[1]  # 1 es el índice de la ventana emergente
				self.driver.switch_to.window(ventana_emergente)
				time.sleep(1)

				# Extrae el contenido HTML de la ventana emergente
				html_ventana_emergente = self.driver.page_source
				self.driver.switch_to.window(ventana_actual )

				soup = BeautifulSoup(html_ventana_emergente,'html.parser')

				# Modify the dict_aux to use the helper function for elements
				dict_aux = {
					'titulo': self.find_text_or_none(soup,'td', 'j_id3:0:j_id13').replace('/','_').replace(' ','') + '-' + self.find_text_or_none(soup,'td', 'j_id3:0:j_id15').replace(' ','_').replace('º',''),
					'numero': self.find_text_or_none(soup,'td', 'j_id3:0:j_id13'),
					'sede': self.find_text_or_none(soup,'td', 'j_id3:0:j_id15'),
					'importancia': self.find_text_or_none(soup,'td', 'j_id3:0:j_id17'),
					'tipo': self.find_text_or_none(soup,'td', 'j_id3:0:j_id19'),
					'fecha': self.find_text_or_none(soup,'td', 'j_id21:0:j_id29'),
					'ficha': self.find_text_or_none(soup,'td', 'j_id21:0:j_id31'),
					'procedimiento': self.find_text_or_none(soup,'td', 'j_id21:0:j_id33'),
					'materias': self.find_text_or_none(soup,'td', 'j_id35:0:j_id39'),
					'firmantes': self.extract_table(soup,'firmantes', 'gridFirmantes:tb'),
					'redactores': self.extract_table(soup,'redactores', 'gridRedactores:tb'),
					'abstract': self.extract_table(soup,'abstract', 'j_id77:tb'),
					'sentencias similares': self.extract_table(soup,'sentencias similares', 'gridSimil:tb'),
					'descriptores' : self.find_text_or_none(soup,'tbody', 'j_id89:tb'),
					'Resumen': self.find_text_or_none(soup,'tbody', 'j_id77:tb'),
					'texto de la sentencia': self.find_text_or_none(soup,'div', 'panelTextoSent_body')
				}		


				# Abre el archivo JSON en modo escritura ('w')
				with open(f'sentencias/{dict_aux["titulo"]}.json', 'w', encoding='utf-8') as archivo:
					# Agrega el nuevo diccionario en formato JSON
					json.dump(dict_aux, archivo, ensure_ascii=False,indent=4)				


			return 0
			
		except Exception:
			with open('fechas_error/fechaserror.json', 'a', encoding='utf-8') as archivo:
				# Agrega el nuevo diccionario en formato JSON
				json.dump(dict_aux["fecha"], archivo, ensure_ascii=False,indent=4)
				# Agrega una coma para separar las fechas
				archivo.write(",")

			print(f'\n dict_aux[fecha] : { dict_aux["fecha"]}\n')
			return dict_aux["fecha"]
			
			
	def change_page(self):

		max_attempts = 2
		current_attempt = 0

		while current_attempt < max_attempts:
			try:

				next_page =  self.driver.find_element(By.ID, f"formResultados:sigLink")
				next_page.click()
				time.sleep(1)
				break

			except Exception as e:
				print(f'current_attempt : {current_attempt}')
				print(f'Error {e}')
				current_attempt += 1
				time.sleep(5)

								  
	def select_option_by_value(self):
		combobox = self.driver.find_element(By.NAME, "formBusqueda:j_id20:j_id240:j_id248")
		
		# Crea un objeto Select a partir del elemento select
		select = Select(combobox)
		
		# Selecciona la opción "Fecha ascendente" por su valor
		select.select_by_value("FECHA_ASCENDENTE")		

	# Define a helper function to find the text of an element or return None if not found
	def find_text_or_none(self,soup,node, element_id):
		element = soup.find(node, {'id': element_id})
		return element.get_text() if element is not None else None


	def extract_table(self,soup,name_table, id_body):

		body = soup.find('tbody',{'id':id_body})

		if body is not None :

			if name_table == 'abstract':
				return [{'camino': elements.find_all("td")[0].get_text(), 'descriptores abstract': elements.find_all("td")[1].get_text()} for elements in soup.find('tbody', {'id': id_body})]

			if name_table == 'firmantes' or name_table == 'redactores':
				return [{'nombre': elements.find_all("td")[0].get_text(), 'cargo': elements.find_all("td")[1].get_text()} for elements in (soup.find('tbody', {'id': id_body}))]
		
			if name_table == 'sentencias similares':
				return [{'numero': elements.find_all("td")[0].get_text(), 'sede': elements.find_all("td")[1].get_text()} for elements in (soup.find('tbody', {'id': id_body}))]

		
		else:
			return None

				
	def extract_npages(self):

		try : 
			elemento = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Página 1')]").text
			# print(f'\n La consulta tiene {elemento.split("de")[1]} paginas')

			return int(elemento.split("de")[1])
		
		except Exception as e:
			print(f'Error {e}')


	def close_driver(self):
		if self.driver:
			self.driver.quit()  


if __name__ == "__main__":
	# Establece la ruta al ejecutable de ChromeDriver.
	chrome_driver_path = r'B:\work\ingesol_scrapy_poder_judicial\driver\chromedriver.exe'
	link_poderj = "https://bjn.poderjudicial.gub.uy/BJNPUBLICA/busquedaSelectiva.seam"

	# fecha_inicio = "07/02/1989"
	fecha_inicio = "16/11/2007"
	fecha_fin = '02/11/2023'

	# Crea una instancia de la clase scraper pasando la ruta del ejecutable como argumento.
	ins_scraper = scraper( chrome_driver_path,link_poderj,fecha_inicio,fecha_fin )
	# Inicializa el controlador de Chrome.
	ins_scraper.initialize_driver()

	ins_scraper.filter_jurisprudencia()


	# Cierra el controlador cuando hayas terminado.
	# ins_scraper.close_driver()