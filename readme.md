# AutoBookingIZIX

El proyecto AutoBookingIZIX automatiza el proceso de iniciar sesión en un sistema de reservas, navegar por sus páginas y realizar reservas. Utiliza Selenium para la automatización web, PGPY para descifrar las credenciales de usuario y SMTP para enviar notificaciones por correo electrónico sobre el resultado de los intentos de reserva.

## Características

- **Automatización Web**: Automatiza acciones en el navegador para iniciar sesión en el sistema de reservas, navegar y hacer reservas.
- **Descifrado de Credenciales**: Descifra de manera segura las credenciales de usuario almacenadas en formato cifrado.
- **Notificaciones por Correo Electrónico**: Envía correos electrónicos a los usuarios con el resultado de sus intentos de reserva.

## Prerrequisitos

Antes de ejecutar el script, asegúrate de tener instalado lo siguiente:

- Python 3
- Selenium, automatización web
- PGPY, encriptación de clave privada
- Pillow, para formatear pantallazos en jpg
- Un controlador web compatible con Selenium (por ejemplo, ChromeDriver para Google Chrome)

## Instalación

1. **Instalar Python 3**: Descarga e instala Python 3 desde [python.org](https://www.python.org/).

2. **Instalar Librerías Requeridas**: Ejecuta el siguiente comando para instalar las librerías necesarias de Python:

   ```sh
   pip install selenium pgpy Pillow
   ```

3. **Controlador Web**: Descarga un controlador web compatible con tu navegador (por ejemplo, ChromeDriver para Google Chrome) y asegúrate de que esté en tu PATH.

## Configuración

1. **Archivo de Configuración**: Crea un archivo `config.txt` en un lugar seguro. Este archivo debe contener configuraciones como URLs, rutas de archivos y credenciales de correo electrónico. Utiliza el siguiente formato:

   ```ini
   [Paths]
   url_izix = URL_AL_SISTEMA_DE_RESERVAS
   log = RUTA_AL_ARCHIVO_DE_LOG
   screenshot_path = RUTA_A_LA_CAPTURA_DE_PANTALLA
   private_key = RUTA_AL_ARCHIVO_DE_CLAVE_PRIVADA

   [Settings]
   pass_email_notif = CONTRASEÑA_DE_LA_CUENTA_DE_CORREO
   email_admin = DIRECCIÓN_DE_CORREO_DEL_ADMINISTRADOR
   ```

2. **Variable de Entorno**: Establece una variable de entorno `izix_path` que apunte al directorio que contiene `config.txt`.

   ```sh
   nano ~/.zshrc
   export izix_path="/Users/kktc183/PyProjects/AutoBookingIzix"
      ```
    Aplicar cambios
   ```sh
   source ~/.zshrc
   ```

   Añade esta línea a tu archivo de perfil de shell (por ejemplo, `.bash_profile`, `.zshrc`) para hacerlo persistente.

    **Atención**: si se usa **launchd** para la automatizacion, la variable de entorno tiene que especificarse en el fichero **plist**

3. **Configuración del Correo Electrónico**: Asegúrate de que la configuración del correo electrónico en `config.txt` esté correctamente configurada para enviar notificaciones.

## Ejecución del Script

Para ejecutar el script, navega al directorio del proyecto y ejecuta:

```sh
python3 AutoBookingIZIX.py
```

## Solución de Problemas

- **Controlador Web de Selenium**: Si encuentras problemas relacionados con el controlador web, asegúrate de que esté correctamente instalado y que su ruta esté incluida en la variable de entorno PATH de tu sistema.
- **Errores de Descifrado**: Verifica que la ruta del archivo de clave privada y la frase de paso sean correctas.
- **Notificaciones por Correo Electrónico**: Revisa la configuración SMTP y las credenciales si fallan las notificaciones por correo electrónico.

## Automatización

1- PMSET despierta el mac todos los días a las 0h

2- LAUNCHD tiene un trabajo definido en plist a las 0h, L-V

3- LAUNCHD lanza el script Python

## Gestión de Energía en macOS con `pmset`

El comando `pmset` se utiliza en macOS para gestionar las políticas de energía del sistema. Esto incluye programar eventos para que el sistema se despierte, duerma, reinicie, apague o encienda en horarios específicos. A continuación, se detallan algunos comandos útiles de `pmset`:

### Ver Eventos Programados

Para consultar los eventos de energía programados en tu sistema, ejecuta:

```terminal
pmset -g sched
```

Este comando muestra todos los eventos programados, incluyendo los tiempos de despertar y dormir.

### Cancelar Todos los Eventos Programados

Si necesitas cancelar todos los eventos programados, utiliza:

```terminal
sudo pmset repeat cancel
```

Este comando elimina todos los eventos de encendido, apagado y despertar programados. Recuerda que necesitarás privilegios de administrador para ejecutar comandos `sudo`.

### Programar Encendido o Despertar del Sistema

Para programar tu sistema para que se encienda o despierte todos los días a una hora específica, utiliza:

```terminal
sudo pmset repeat wakeorpoweron DÍAS HORA
```

Por ejemplo, para hacer que tu sistema se encienda o despierte a las 00:00 horas todos los días, ejecutarías:

```terminal
sudo pmset repeat wakeorpoweron MTWRFSU 00:00:00
```

`MTWRFSU` abarca todos los días de la semana, desde el lunes hasta el domingo.

Estos comandos te permiten tener un control preciso sobre los ciclos de energía de tu sistema macOS, asegurando que esté activo o en reposo según tus necesidades específicas.


## Programar la Ejecución con `launchd`

Para automatizar la ejecución de tu script en macOS utilizando `launchd`, sigue estos pasos para crear y cargar un archivo `.plist` que defina cuándo y cómo se debe ejecutar tu script.

### Crear el Archivo `.plist`

1. Abre tu editor de texto preferido y crea un nuevo archivo con la estructura XML proporcionada. Asegúrate de personalizar los valores según tus necesidades:

    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.user.autoizix</string>
        <key>ProgramArguments</key>
        <array>
            <string>/usr/local/bin/python3</string>
            <string>/Users/kktc183/PyProjects/AutoBookingIzix/AutoBookingIZIX.py</string>
        </array>
        <key>EnvironmentVariables</key>
        <dict>
            <key>izix_path</key>
            <string>/Users/kktc183/PyProjects/AutoBookingIzix</string>
        </dict>
        <key>RunAtLoad</key>
        <false/>
        <key>StartCalendarInterval</key>
        <array>
            <dict>
                <key>Hour</key>
                <integer>0</integer>
                <key>Minute</key>
                <integer>0</integer>
                <key>Weekday</key>
                <integer>1</integer> <!-- Monday -->
            </dict>
            <!-- Repite para cada día de la semana hasta el viernes -->
        </array>
        <key>StandardErrorPath</key>
        <string>/tmp/com.user.autoizix.err</string>
        <key>StandardOutPath</key>
        <string>/tmp/com.user.autoizix.out</string>
    </dict>
    </plist>
    ```

2. Guarda el archivo con una extensión `.plist`, por ejemplo, `com.user.autoizix.plist`.

### Cargar el Archivo `.plist`

1. Mueve tu archivo `.plist` a `~/Library/LaunchAgents/`:

    ```sh
    mv com.user.autoizix.plist ~/Library/LaunchAgents/
    ```

2. Utiliza `launchctl` para cargar y activar tu trabajo:

    ```sh
    launchctl load ~/Library/LaunchAgents/com.user.autoizix.plist
    ```

### Verificar y Depurar

- Para verificar que tu trabajo se ha cargado correctamente, puedes usar:

    ```sh
    launchctl list | grep com.user.autoizix
    ```

- Revisa los archivos `/tmp/com.user.autoizix.out` y `/tmp/com.user.autoizix.err` para cualquier salida estándar o errores generados por tu script.

### Notas Adicionales

- Este trabajo está configurado para ejecutarse automáticamente a las 00:00 horas de lunes a viernes.
- Asegúrate de reemplazar los valores de `<string>` y `<integer>` en el archivo `.plist` según corresponda a tu configuración específica.
- La variable de entorno `izix_path` se establece específicamente para este trabajo, asegurándose de que tu script tenga acceso a ella durante su ejecución.


