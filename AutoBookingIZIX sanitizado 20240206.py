#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

from datetime import datetime
import time
import datetime

# import urllib

# todo

    # funciona calendar, no funciona cron
    # cazar error internet
    # espera ante error??
    # usr y pas en fichero externo


def automate_booking(usr, passw):
    
    # Create a new instance of the Chrome driver

    # INSTALACIÓN LOCAL DE CHROMEDRIVER
    # Specify the path to chromedriver that you've downloaded and cached
    # para evitar los errores de acceso online a la última versión del driver
    # att, el chromedriver tiene que soportar la versión de Chrome instalada
    # en este caso, v121
    # descargar chromedriver de: https://googlechromelabs.github.io/chrome-for-testing/#stable
    # y dejarlo localmente en:
    # svc = Service('/usr/local/bin/chromedriver-mac-arm64/chromedriver')
    # o instalar HomeBrew /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # /opt/homebrew/bin/chromedriver
    # para que mac lo autorice:
    # xattr -d com.apple.quarantine /usr/local/bin/chromedriver-mac-arm64/chromedriver
    # options = webdriver.ChromeOptions()
    # driver = webdriver.Chrome(service=svc) 
    
    # sin instalar localmente, comprueba internet y usa versión de Chrome instalada
    driver = webdriver.Chrome() 

    # def check_loader_present():
    #     try:
    #         driver.find_element(By.ID, 'loader')
    #         return True
    #     except:
    #         return False

   


    # def wait_for_ready_state_complete(driver, timeout=30):
    #     try:
    #         WebDriverWait(driver, timeout).until(
    #             lambda driver: driver.execute_script('return document.readyState') == 'complete'
    #         )
    #     except WebDriverException:
    #         print("Timed out waiting for page to load")
    #         return False
    #     return True




    try:
        # Navigate to the login page
        # acceder directamente a la parte de reserva https://business.bepark.eu/booking/267723/create
        # abrirá la página del login
        
        wait = WebDriverWait(driver, 20)  # timeout after 10 seconds
        url = "https://business.bepark.eu/booking/267723/create"
        
        print("Abriendo pag web")
        driver.get(url)

        # print("esperando a que esté cargada")
        # no hace falta, ya esperamos con la caja de cookies
        # wait.until(EC.presence_of_element_located((By.ID, 'CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll')))
        # is_loaded = wait_for_ready_state_complete(driver)


       
        print ("aceptando cookies")
    
        # Aceptado de cookies, con el formato anterior
        # cookies_ok = wait.until(EC.presence_of_element_located((By.ID, 'hs-eu-confirmation-button')))
        # cookies_ok.click()

        # Nuevas cookies
        # <button id="CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll" class="CybotCookiebotDialogBodyButton" tabindex="0" lang="en">Allow all</button>
        cookies_ok = wait.until(EC.presence_of_element_located((By.ID, 'CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll')))
        cookies_ok.click()

        print ("quitando caja del chat")
        # está en un iframe!!!!!
        # cambiar al iframe por el ID
        wait.until(EC.presence_of_element_located((By.ID, 'hubspot-conversations-iframe')))
        iframe_id = "hubspot-conversations-iframe"
        # print("iframe_id:", iframe_id)
        driver.switch_to.frame(iframe_id)

        # Now that the context is inside the iframe, locate the 'Dismiss' button.
        # Since you have not provided the exact HTML of the button, I will assume it can be uniquely identified by its aria-label attribute.
        try:
            # Wait for the button to be clickable before clicking it
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Dismiss']"))).click()
            print("Dissmiss chat clicado ok")
        except WebDriverException:
            print("Button not found or not clickable within 10 seconds.")

        # Switch back to the main document
        driver.switch_to.default_content()


        # Enter username and password
        print("entrando usuario")
        driver.find_element(by=By.NAME, value="email").send_keys(usr)
        print("entrando pass")
        driver.find_element(by=By.NAME, value="password").send_keys(passw)
        
        print("clicando sign in")
        submit_button = driver.find_element(by=By.ID, value="pendo_sign_in_button")
        
        submit_button.click()
        
        # si no sale el loader, ha habido error de captcha, repetir
        #while not check_loader_present():
            # print ("clicando otra vez por error captcha")
            # time.sleep(1)
            # submit_button = driver.find_element(by=By.ID, value="pendo_sign_in_button")
            # submit_button.click()
        #    print ("Error de captcha, vuelta a empezar")
        #    raise Exception("Error de captcha")


        # Wait for the page to load      
        wait.until(EC.invisibility_of_element((By.ID, 'loader')))

        # y hacer clic en next (semana siguiente)"
        print ("clicar next")
        seleccionar_next = wait.until(EC.element_to_be_clickable ((By.ID, 'next')))
        seleccionar_next.click()


        # Esperar a que esté cargada la página

        print ("Esperar a página cargada")
        loader_element_id = "loader"
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.ID, loader_element_id))
        )
        #time.sleep(5)
        


        #Seleccionar todo el día
        print ("detectando la selección de días")
        # Encuentra todos los botones "Select all day"
        select_all_day_buttons = driver.find_elements(By.CSS_SELECTOR, ".cta-btn.hidden.lg\\:block")
        # print (select_all_day_buttons)

        # Haz clic en cada botón
        for button in select_all_day_buttons:
            try:
                # Espera a que el botón sea clickeable antes de hacer clic
                # print(button)
                print ("seleccionar el día", end="")
                wait.until(EC.element_to_be_clickable(button))
                button.click()
                # Darle al check para validar la selección
                print (" -> Clicar en el check")
                check_button = driver.find_element(by=By.ID, value="submit-icon")
                check_button.click()
                time.sleep(3)

            except Exception as e:
                print(f"Hubo un problema al hacer clic en el botón: {e}")




        print ("Guardando pantallazo de reservas")

        time.sleep(3)   

        # Guardar pantallazo de resultado
        screenshot_path = "/Users/xxxxxxxxx/Downloads/izix/Reservas.png"
        driver.save_screenshot(screenshot_path)

        time.sleep(1)   

        resultado = "finalizado"
        # print (resultado)
        


    except Exception as e:
        print("Error: ", str(e))
        # driver.save_screenshot('descargas/error_screenshot.png')
        resultado = "Error: "+str(e)
        # print(resultado, "\n\nIntentando de nuevo:\n")
       
        
        # time.sleep(5)
        
    finally:
        # Close the browser window
        # time.sleep(5)
        print (f"{datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}, {resultado}\n")
        driver.quit()
        return (resultado)



######################################################################################

# Código principal



if __name__ == "__main__":
    import time
    from datetime import datetime

# Alternativa de sacar los user pass desde un sharepoint, parseandolos
# url_usrpas = "https://xxxxxxxxxxxxx.sharepoint.com/xxxxx"
# for line in urllib.request.urlopen(url_usrpas):
#     pieces = line.split(":")
#     usr = pieces[0]
#     passw = pieces[1]
#     print (usr)
#     print (passw)
#     #do whatever else you need to with each email and password here>

usr = "xxxxxxxx"
passw = "xxxxxxxxxx"

print (f"\n{datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}, Lanzando el trabajo\n")

resultado = None
while resultado != "finalizado":
    if resultado != None:
        print ("\nIntentando de nuevo... \n\n")
    print ("Llamando al proc automate_booking")
    resultado = automate_booking(usr, passw)

    # logado del resulado
    print ("guardando log.txt")
    log = '/Users/xxxxxxxxx/Downloads/izix/log.txt'
    entrada_log = f"{datetime.now().strftime('%Y-%m-%d, %H:%M:%S')}, {resultado}\n"
    with open(log, 'r') as file:
        original_content = file.read()
    with open(log, 'w') as file:
        file.write(entrada_log + original_content)

print ("Fin")



######################################################################################


# Automatización:
# 1- PMSET despierta el mac todos los días a las 0h
# 2- CALENDAR tiene una entrada a las 0:0h
# 3- en esa entrada, en vez de un aviso, abre una app
# 4- la app está hecha con AUTOMATOR, y abre un script 
# 5- el script ejecuta el código PYTHON de la reserva automática
# 6- también trabajo Crono, a las 0:01h, funcionamiento irregular


# mac despertado automáticamente con pmset
# pmset -g sched: Ver el horario actual
# sudo pmset repeat cancel: Cancelar el horario actual
# sudo pmset repeat wake MTWR 00:00:00
# sudo pmset repeat wakeorpoweron MTWRFSU 00:00:00

# script shell ejecutando el código python
# /Users/xxxxxxx/PyProjects/AutoBookinIZIXexec
        #!/bin/sh
        # /usr/local/bin/python3 /Users/xxxxxxx/PyProjects/AutoBookingIZIX.py
        # echo "$(date): Automatización IZIX OK" >> //Users/xxxxxxx/Downloads/izix/log_automator.txt

# Automator para construir una app con ese script
# https://medium.com/analytics-vidhya/effortlessly-automate-your-python-scripts-cd295697dff6
# /Users/xxxxxx/AutomatizarIZIX.app


# NO FUNCIONA CRONTAB??? - ¿porque la tapa está cerrada?
# Crontab 
# crontab -e
# /usr/local/bin/python3 /Users/xxxxxx/PyProjects/AutoBookingIZIX.py
# 1 0 * * 1-4 /usr/local/bin/python3 /Users/xxxxxxx/PyProjects/AutoBookingIZIX.py
# hacerlo ejecutable para el crontab
# chmod a+x /Users/xxxxxxxx/PyProjects/AutoBookingIZIX.py

