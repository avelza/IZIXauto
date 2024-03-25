#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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
import mimetypes

from PIL import Image
import io

import os





class LoginError(Exception):
    """Exception raised for errors in the login process."""
    pass



# todo
#       asegurar automatización!!!!
#       error apertura de chrome, sin logado a proxy
#       resultado con días concretos de reserva
#       limpiar código



def envia_email (email, asunto, body, pantallazo=None):
    # Email settings
    sender_email = "izix.notificaciones@gmail.com"
    receiver_email = email
    password = pass_email_notif

    # Create the email message
    msg = EmailMessage()
    msg['Subject'] = asunto
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg.set_content(body)

    if pantallazo:
        
        image_path = pantallazo
        ctype, encoding = mimetypes.guess_type(image_path)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)

        with open(image_path, 'rb') as fp:
            msg.add_attachment(fp.read(), maintype=maintype, subtype=subtype, filename=image_path.split("/")[-1])

    # Send the email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, password)
            smtp.send_message(msg, from_addr=sender_email, to_addrs=[receiver_email])
        print("\nEmail enviado al usuario")
    except Exception as e:
        print(f"Failed to send email: {e}")


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
    # chrome_options.add_argument("--incognito")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def abrir_pagina(driver):
    
    driver.get (url_izix)
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((
                By.XPATH, "//h2[contains(@class, 'mt-5') and contains(@class, 'text-2xl') and contains(@class, 'font-bold') and contains(text(), 'Log in to Izix')]")
            )
        )
        # print("Page has rendered and the specific element is present.")
    except TimeoutException:
        print("No se ha podido cargar la página")

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
        print("Chat box dismiss button not found or not clickable.")
    driver.switch_to.default_content()

def login(driver, usr, passw):
    driver.find_element(By.NAME, "email").send_keys(usr)
    driver.find_element(By.NAME, "password").send_keys(passw)
    driver.find_element(By.ID, "pendo_sign_in_button").click()
    # comprobar que el login ha sido correcto:
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.LINK_TEXT, "Create a booking")))
    except TimeoutException:
        raise LoginError("Login failed")

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
    for button in select_all_day_buttons[:4]:  # Assuming 4 days, Monday to Thursday
        wait.until(EC.element_to_be_clickable(button)).click()
        driver.find_element(By.ID, "submit-icon").click()
        time.sleep(3)

def save_screenshot(driver):
    screenshot_as_png = driver.get_screenshot_as_png()
    image = Image.open(io.BytesIO(screenshot_as_png))
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        image = image.convert("RGB")
    image.save(screenshot_path, 'JPEG', quality=85)

def automate_booking(usr, passw):
    driver = setup_driver()
    try:
        print ("abriendo página")
        abrir_pagina(driver)
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
        return "Booking correcto!"

    except LoginError as e:
        return "Error en login"
    except Exception as e:
        return f"An error occurred: {e}"
    
    finally:
        print ("guardando pantallazo")
        save_screenshot(driver)
        driver.delete_all_cookies()
        driver.quit()


def booking_logado(usr, passw, unique_id):
       
        print (f"\n{datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}, Lanzando el trabajo de",usr,"\n")
        resultado = None
        intentos = 0
        intentos_max = 1    # número máximo de intentos para cada usuario
        while resultado != "finalizado" and intentos < intentos_max:
            if resultado != None:
                print ("\nIntentando de nuevo ... \n\n")
            
            print ("Lanzando el booking automático\n")
            try:
                resultado = automate_booking(usr, passw)
            except Exception as e:
                print("Error: ", str(e))
                resultado = "Error: "+str(e)
            
            intentos = intentos + 1

        print("Guardando en log")
        entrada_log = f"{datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}, {usr} \t\tresultado: {resultado} \n"

        # Asegúrate de que el log.txt existe, si no, lo creas, y añades entrada de log
        try:
            with open(log, 'r') as file:
                original_content = file.read()
            with open(log, 'w') as file:
                file.write(entrada_log + original_content)
        except FileNotFoundError:
            with open(log, 'w') as file:
                file.write(entrada_log)
        
        # imprime el resultado
        print (f"{datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}, {resultado}")
        
        # incluye el resultado en la lista de registro de resultados
        registro_resultados[unique_id] = f"{datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}, {resultado}"
        
        # envía un email al usuario con el resultado
        if envio_email:
            asunto = "Booking automático IZIX"
            body = "Resultado del booking automático de hoy: " + resultado + "\n\n¡Comprueba el pantallazo adjunto!"
            envia_email (usr, asunto, body, screenshot_path)


def procesar (fichero_a_procesar):

    print ("extrayendo mensajes encriptados")
    encrypted_messages = extract_pgp_messages(fichero_a_procesar)
    decrypted_messages = {}

    print ("desencriptando mensajes")
    for msg_id, encrypted_msg in encrypted_messages.items():
        decrypted_msg = decrypt_userpass(encrypted_msg, private_key)
        decrypted_messages[msg_id] = decrypted_msg
        
    for msg_id, message in decrypted_messages.items():
        try:
            usr, passwd = message.split(':')
            booking_logado (usr, passwd, usr)
        except:
            print(f"Error processing message ID {msg_id}: incorrect format.")





######################################################################################

# Código principal



if __name__ == "__main__":

    print ("\n\nInicio\n")
  
    # Ajustes
    print ("Ajustes:")
    # config_path = os.getenv('izix_path')    # extraigo el path del fichero de config de variables de entorno os
    config_dir = os.getenv('izix_path')    # extraigo el path del fichero de config de variables de entorno os
    print (config_dir)
    config_path = config_dir + '/files/config.txt' if config_dir else None
    if config_path:
        print(f"     evotempo_path:{config_path}")
    else:
        print("     evotempo_path: environment variable not set.")
    print(f"     izix_path: {config_path}")
    envio_email = True
    print ("     envio_email: " + str(envio_email))
    batch = True
    print ("     modo batch: " + str(batch))
   
    # Initialize the configparser
    config = configparser.ConfigParser()
    # Read the configuration file
    config.read(config_path)

    # Now, extract the variables from the configuration file
    url_izix = config['Paths']['url_izix']                            # url de la página de booking
    log = config['Paths']['log']                            # path al fichero local de logado
    log_onedrive = config['Paths']['log_onedrive']          # path al fichero log, copiado en onedrive  
    screenshot_path = config['Paths']['screenshot_path']    # path al fichero local con pantallazo
    passes_onedrive = config['Paths']['passes_onedrive']    # path al fichero de passes en onedrive, mapeado en el pc
    passes_file = config['Paths']['passes_file']            # path al fichero local de passes que vamos a copiar desde onedrive
    mipass = config['Paths']['mipass']                      # path al fichero logal donde está mi usr pass
    mipass_encriptado = config['Paths']['mipass_encriptado']                  # path al fichero logal donde está mi usr pass encriptado
    private_key = config['Paths']['private_key']                  # path al fichero con la clave privada
    pass_email_notif = config['Settings']['pass_email_notif']                  # contraseña de email de notificaciones
    email_admin = config['Settings']['email_admin']                  # email de notificaciones

    

    registro_resultados = {}





    print ("\nModo LOCAL\n")    
    procesar (mipass_encriptado)
    
    if batch:
        print ("\nModo BATCH\n")
        print ("proceso el fichero de passes de onedrive")
        #descargar fichero de los passes del directorio onedrive mapeado, a local
        shutil.copyfile(passes_onedrive, passes_file)
        procesar (passes_file)
    
    body = "Resultado del booking automático:\n\n"
    for user, result in registro_resultados.items():
        body +=  f"Usuario: {user}, Resultado: {result}\n"
    asunto = "Resultado de los Booking automático IZIX"
    print ("enviando resumen a admin")
    envia_email (email_admin, asunto, body, False)

    # copia el log a una carpeta donde pueda ver el resultado en remoto
    shutil.copyfile(log, log_onedrive)

    print ("\nFin\n")

