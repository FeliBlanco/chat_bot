# Para levantar la API solamente se debe usar docker-compose up --build
# Se usa FastApi para poder levantar una RestAPI de forma fácil, con los módulos básicos correspondientes como para leer las variables de entorno, junto con el archivo de configuracion
# Luego, el Docker mismo instala postgres, que será usado en la API para guardar los productos.
# .env: ENGINE_IA si es 0, va a usar el asistente, si es 1 usa un chat común.
