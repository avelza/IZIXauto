#!/usr/bin/env python3


# todo
        # booking desde una hora concreta
        # resultado con detección de días concretos de reserva
        # arreglar logs con multithreading



from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from datetime import datetime
import time

import shutil
import configparser

import pgpy

import warnings
from cryptography.utils import CryptographyDeprecationWarning

import smtplib
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import mimetypes

from PIL import Image
import io
import os

from concurrent.futures import ThreadPoolExecutor   # para paralelizar el booking de todos los usuarios




class LoginError(Exception):
    """Exception raised for errors in the login process."""
    pass



def envia_email (sender, receiver_email, password, asunto, body, pantallazo=None):
    
    # Email settings
    
    if isinstance(pantallazo, str):

        # Create the email message
        msg = MIMEMultipart('related')
       
        # HTML body with image
        html_body = f"""
        <html>
            <body>
                <p>{body}</p>
                <img src="cid:image1" style="width: 50%; height: auto;">
            </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))

        # Open the screenshot image to embed
        image_path = pantallazo
        ctype, encoding = mimetypes.guess_type(image_path)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        
        maintype, subtype = ctype.split("/", 1)
        with open(image_path, 'rb') as fp:
            img = MIMEImage(fp.read(), _subtype=subtype)
            img.add_header('Content-ID', '<image1>')  # Use this 'Content-ID' in the HTML img src
            msg.attach(img)
    else:
        msg = EmailMessage()
        msg.set_content(body)

    msg['Subject'] = asunto
    msg['From'] = sender
    # receiver_email = sender           # for testing
    msg['To'] = receiver_email

    # Send the message via SMTP server
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
            print("Email enviado al usuario")
    except Exception as e:
        print(f"Fallo al enviar el email: {e}")


def decrypt_userpass(encrypted_msg, private_key_path):
    
    # Load the private key
    with open(private_key_path, 'r') as f:
        priv_key = pgpy.PGPKey()
        priv_key.parse(f.read())
    
    # Attempt to unlock the private key
    # if not priv_key.unlock(passphrase):
    #     print("Failed to unlock the private key. Please check the passphrase.")
    #     return

    pgp_msg = pgpy.PGPMessage.from_blob(encrypted_msg.strip())
    try:
        decrypted_message = priv_key.decrypt(pgp_msg)
        print("Usuario contraseña detectado:", decrypted_message.message)
        return decrypted_message.message
    except Exception as e:
        print(f"An error occurred during decryption: {e}")


def extract_pgp_messages(file_path):
    """
    Extracts PGP encrypted messages from a file and returns them in a dictionary.
    
    Args:
    file_path (str): The path to the file containing the PGP messages.
    
    Returns:
    dict: A dictionary of PGP messages, keyed by an incrementing integer.
    """
    
    
    # Suppress only CryptographyDeprecationWarning
    warnings.simplefilter('ignore', CryptographyDeprecationWarning)
    
    # Initialize an empty dictionary to hold the messages
    messages = {}
    
    # Initialize an empty string to hold the current message being read
    current_message = ""
    message_started = False
    message_counter = 1  # Start counting messages from 1
    
    try:
        # Open the file and read line by line
        with open(file_path, 'r') as file:
            for line in file:
                # Check for the beginning of a PGP message
                if line.strip() == '-----BEGIN PGP MESSAGE-----':
                    message_started = True
                    current_message = line  # Include the start line as part of the message
                elif line.strip() == '-----END PGP MESSAGE-----' and message_started:
                    # Include the end line, save the current message, and reset for the next message
                    current_message += line
                    # print (current_message)
                    messages[message_counter] = current_message
                    message_counter += 1
                    current_message = ""
                    message_started = False
                elif message_started:
                    # If we are within a message, continue appending lines to the current message
                    current_message += line
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return {}
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return {}
    
    return messages


def setup_driver():
    chrome_options = Options()
    # vamos a evitar que trate de abrir la página configurada de inicio en chrome
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    # chrome_options.add_argument("--incognito")

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def abrir_pagina(driver, url):
    
    driver.get (url)
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((
                By.XPATH, "//h2[contains(@class, 'mt-5') and contains(@class, 'text-2xl') and contains(@class, 'font-bold') and contains(text(), 'Log in to Izix')]")
            )
        )
        # print("Page has rendered and the specific element is present.")
    except TimeoutException:
        print("-> No se ha podido cargar la página")
        raise TimeoutException ("Error, no he podido cargar la página")

def accept_cookies(driver):
    wait = WebDriverWait(driver, 10)
    cookies_ok = wait.until(EC.presence_of_element_located((By.ID, 'CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll')))
    cookies_ok.click()

def dismiss_chat_box(driver):
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, 'hubspot-conversations-iframe')))
    driver.switch_to.frame("hubspot-conversations-iframe")
    try:
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Dismiss']"))).click()
    except Exception as e:
        print("-> Error, no he podido quitar el chat box")
        raise Exception ("Error, no he podido quitar el chat box")
    
    driver.switch_to.default_content()

def login(driver, usr, passw):
    driver.find_element(By.NAME, "email").send_keys(usr)
    driver.find_element(By.NAME, "password").send_keys(passw)
    driver.find_element(By.ID, "pendo_sign_in_button").click()
    # comprobar que el login ha sido correcto:
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "Create a booking")))
    except TimeoutException:
        print ("-> Error, no he podido hacer login")
        raise LoginError ("Login failed")

def navigate_to_booking(driver):
    wait = WebDriverWait(driver, 10)
    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Create a booking"))).click()

def pasar_siguiente_semana(driver):
    # y hacer clic en next (semana siguiente)"
    wait = WebDriverWait(driver, 10)
    seleccionar_next = wait.until(EC.element_to_be_clickable ((By.ID, 'next')))
    seleccionar_next.click()

def select_days_and_book(driver):
    wait = WebDriverWait(driver, 10)
    select_all_day_buttons = driver.find_elements(By.CSS_SELECTOR, ".cta-btn.hidden.lg\\:block")
    for button in select_all_day_buttons[:4]:  # Los 4 primeros días, de lunes a jueves
        wait.until(EC.element_to_be_clickable(button)).click()
        driver.find_element(By.ID, "submit-icon").click()
        time.sleep(4)   # da tiempo a que se recargue la página

def save_screenshot(driver, screenshot_path):
    screenshot_as_png = driver.get_screenshot_as_png()
    image = Image.open(io.BytesIO(screenshot_as_png))
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        image = image.convert("RGB")
    image.save(screenshot_path, 'JPEG', quality=85)

def automate_booking(usr, passw, configuracion):
    
    try:
        print ("abriendo chrome")
        driver = setup_driver()
        print ("abriendo página")
        url  = configuracion ['Paths']['url_izix']
        abrir_pagina(driver, url)
        print ("aceptando cookies")
        accept_cookies(driver)
        print ("quitando chatbox")
        dismiss_chat_box(driver)
        print ("haciendo login")
        login(driver, usr, passw)
        WebDriverWait(driver, 10).until(EC.invisibility_of_element((By.ID, 'loader')))
        print ("pasando a página de booking")
        navigate_to_booking(driver)
        WebDriverWait(driver, 10).until(EC.invisibility_of_element((By.ID, 'loader')))
        print ("pasando a la siguiente semana")
        pasar_siguiente_semana(driver)
        WebDriverWait(driver, 10).until(EC.invisibility_of_element((By.ID, 'loader')))
        print ("seleccionar y reservar días")
        select_days_and_book(driver)
        return "Ejecución correcta!"

    except LoginError as e:
        return "Error en login"
    except Exception as e:
        return f"An error occurred: {e}"
    
    finally:
        print ("guardando pantallazo")
        time.sleep (3)
        screenshot_path = configuracion ['Paths']['screenshot_path']
        # Use the current datetime to ensure uniqueness for each user
        screenshot_file = f"reservas_{usr}.jpg"                # Constructs the filename with the user prefix and user name
        screenshot_full = f"{screenshot_path}/{screenshot_file}"     # Combines the path with the filename
        save_screenshot(driver, screenshot_full)

        driver.delete_all_cookies()
        driver.quit()


def guarda_log (entrada_log, log):
        
    print("Guardando en log")
    # entrada_log = f"{datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}, {usr} \t\tresultado: {resultado} \n"

    # Asegúrate de que el log.txt existe, si no, lo creas, y añades entrada de log
    try:
        with open(log, 'r') as file:
            original_content = file.read()
        with open(log, 'w') as file:
            file.write(entrada_log + original_content)
    except FileNotFoundError:
        with open(log, 'w') as file:
            file.write(entrada_log)
    
    

def booking (usr, passw, registro_resultados, configuracion):
       
    envio_email = configuracion ['Settings']['enviar_email']
    enviar_changelog = configuracion ['Settings']['enviar_changelog']
    changelog = configuracion ['Paths']['changelog']
    screenshot_path = configuracion ['Paths']['screenshot_path']

    print (f"\n{datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}, Lanzando el trabajo de",usr,"\n")
    resultado = None
    intentos = 0
    intentos_max = 3    # número máximo de intentos para cada usuario
    while resultado != "Ejecución correcta!" and intentos < intentos_max:
        if resultado != None:
            print ("\nIntentando de nuevo ... \n\n")
        
        print ("Lanzando el booking automático\n")
        try:
            resultado = automate_booking(usr, passw, configuracion)
        except Exception as e:
            print("Error: ", str(e))
            resultado = "Error: "+str(e)
        
        intentos = intentos + 1

    # incluye el resultado en la lista de registro de resultados
    registro_resultados[usr] = f"{datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}, {resultado}"      

    entrada_log = f"{datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}, {usr} \t\tresultado: {resultado} \n"
    log = configuracion ['Paths']['log']
    guarda_log (entrada_log, log)
    print (entrada_log)
    
    # envía un email al usuario con el resultado
    if envio_email:
        if resultado == "Ejecución correcta!":
            rdo_email = "OK"
        else:
            rdo_email = "Error"
        asunto = "Booking automático IZIX: " + rdo_email
        body = "Usuario: " + usr + "\nResultado del booking automático de hoy: " + resultado
        sender = configuracion ['Settings']['email_notif']
        pass_email = configuracion ['Settings']['pass_email_notif']
        screenshot_file = f"reservas_{usr}.jpg"                # Constructs the filename with the user prefix and user name
        screenshot_full = f"{screenshot_path}/{screenshot_file}"     # Combines the path with the filename
        if enviar_changelog:
            with open(changelog, 'r') as clfile:
                chglogcontent = clfile.read()
            body += "\n<pre>CHANGELOG:\n\n" + chglogcontent + "</pre>"    # añadiendo <pre> para que en el html del email mantenga el formato
        envia_email (sender, usr, pass_email, asunto, body, screenshot_full)


def extraer_usrpass (fichero_a_procesar, private_key) -> dict:

    lista_usrpass = {}

    print("Extrayendo mensajes encriptados")
    encrypted_messages = extract_pgp_messages(fichero_a_procesar)
    decrypted_messages = {}

    print("Desencriptando mensajes")
    
    for msg_id, encrypted_msg in encrypted_messages.items():
        decrypted_msg = decrypt_userpass(encrypted_msg, private_key)
        decrypted_messages[msg_id] = decrypted_msg

    print ("Separando usr:passw en una lista")
    for msg_id, message in decrypted_messages.items():
        try:
            usr, passwd = message.split(':')
            lista_usrpass[usr] = passwd
        except:
            print(f"Error al procesar el mensaje con ID {msg_id}: formato incorrecto")

    return lista_usrpass

def procesar_concurrentemente (lista_usrpass, registro_resultados, configuracion):

    # Usar ThreadPoolExecutor para procesar cada usuario en paralelo
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for usr, passwd in lista_usrpass.items():
            futures.append(executor.submit(booking, usr, passwd, registro_resultados, configuracion))

    # Esperar a que todos los hilos terminen
    for future in futures:
        result = future.result()  # Esto bloquea hasta que el hilo asociado termine


def procesar (lista_usrpass, registro_resultados, configuracion):

    for usr, passwd in lista_usrpass.items():
        booking (usr, passwd, registro_resultados, configuracion)


def carga_config (config_file) -> dict:
    
    configs : dict = {}
            
    # Initialize the configparser
    config = configparser.ConfigParser()

    # Attempt to read the configuration file
    try:
        config.read(config_file)
    except Exception as e:
        print(f"Error reading config file: {e}")
        return configs

    try:
        # Iterate over sections and options to populate the configs dictionary
        for section in config.sections():
            configs[section] = {}  # Initialize a sub-dictionary for each section
            for option in config.options(section):
                value = config.get(section, option)  # Get the value as a string
                # Attempt to interpret string values as boolean, int, or float if applicable
                if value.lower() in ('true', 'false'):
                    value = config.getboolean(section, option)
                elif value.isdigit():
                    value = config.getint(section, option)
                else:
                    try:
                        value = config.getfloat(section, option)
                    except ValueError:
                        pass  # Keep as string if it's not a float
                configs[section][option] = value
    except configparser.NoSectionError:
        print('Error, falta una sección en el fichero de config')
    except configparser.NoOptionError:
        print('Error, falta una opción en el fichero de config')

    # Print out settings for verification
    print ("Ajustes:")
    for section, options in configs.items():
        print(f"     {section}:")
        for option, value in options.items():
            print(f"          {option}: {value}")

    return configs



def main ():

    print ("\n\nInicio")
    print (f"{datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}\n")
  
    # Carga de configuración
    try:
        # Ajustes
        print ("Carga de configuración")
        configuracion : dict = {}
        config_dir = 'izix_path'        # variable de entorno os, fijada en el plist del launchd, y en .zshrc
        config_file = '/files/config.txt'
        config_dir = os.getenv(config_dir)        # extraigo el path del fichero de config de variables de entorno os
        if config_dir:
            config_file = config_dir + config_file  # Construct the full path to the config file
            print(f"     izix_path: {config_file}")
        else:
            print ("     izix_path: falta la vatriable de entorno de configuraciones")
            raise Exception ("Error, falta la vatriable de entorno de configuraciones")
        
        configuracion = carga_config (config_file)

        if configuracion == {}:
            print ("Error, no se puede cargar la configuración")
            raise Exception ("Error, no se puede cargar la configuración")

    except:
        resultado = "Error"


    # Proceso de reservas
    registro_resultados = {}
    private_key = configuracion['Paths']['private_key']

    # procesar las reservas en batch
    batch = configuracion['Settings']['funcionar_en_batch']
    if batch:
        print ("\nReserva automatizada BATCH iterativa de fichero online de claves\n")
        print ("proceso el fichero de passes de onedrive")
        
        #descargar fichero de los passes del directorio onedrive mapeado, a local
        intento_fichero = 0
        max_intento_fichero = 5

        passes_onedrive = configuracion['Paths']['passes_onedrive']
        passes_file = configuracion['Paths']['passes_file']
        passes_backup = configuracion['Paths']['passes_backup']
        while intento_fichero < max_intento_fichero:
            try:
                shutil.copyfile(passes_onedrive, passes_file)
                print("fichero de passes copiado de onedrive a local")
                # guardar un backup del fichero de passes
                if os.stat(passes_file).st_size != 0:
                    shutil.copyfile(passes_file, passes_backup)
                break
            except OSError as e:
                print(f"Attempt {intento_fichero + 1} failed: {e}")
                time.sleep(2)  # wait for 2 seconds before retrying
                intento_fichero += 1
        
        if configuracion ['Settings']['modo_pruebas']:
            print ("Modo de pruebas ACTIVADO, cambiando fichero a procesar")
            passes_file = configuracion ['Paths']['passes_pruebas']
        lista_usrpass = extraer_usrpass (passes_file, private_key)
        # procesar (lista_usrpass, configuracion)                       # procesar individualmente 
        procesar_concurrentemente (lista_usrpass, registro_resultados, configuracion)     # lanzando todos en paralelo
    
    # procesar la reserva en fichero local
    print ("\nReserva automatizada desde el fichero LOCAL de claves\n")
    mipass_encriptado = configuracion['Paths']['mipass_encriptado']
    mipass = extraer_usrpass (mipass_encriptado, private_key)
    procesar (mipass, registro_resultados, configuracion)


    # envía un correo electrónico al admin, sobre el resultado del proceso batch

    email_admin = configuracion['Settings']['email_admin']
    pass_email = configuracion ['Settings']['pass_email_notif']
    body = "Resultado del booking automático en batch:\n\n"
    body += "Total usuarios : " + str(len(registro_resultados)) + "\n\n"
    for user, result in registro_resultados.items():
        body +=  f"Usuario: {user} \t\tResultado: {result}\n"
    print (body)                    # imprime en stdout el resultado del booking batch
    asunto = "Resultado de los Booking automático IZIX"
    print ("Enviando resumen a admin")
    sender = configuracion ['Settings']['email_notif']
    envia_email (sender, email_admin, pass_email, asunto, body)


    # copia el log a una carpeta donde pueda ver el resultado en remoto
    # log = configuracion['Paths']['log_onedrive']
    # shutil.copyfile(log, log_onedrive)

    print ("\nFin\n")




if __name__ == "__main__":

    main ()

