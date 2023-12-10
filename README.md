# sarv3 
SAR es una aplicación para la gestión de recursos. Permite a sus usuarios realizar solicitudes y a los establecidos como validadores aprobarlas o denegarlas. 

# Features 
- Autenticación mediante LDAP 
- Gestión de recursos 
- Gestión de solicitudes 
- Aplicación de permisos en AD 

# Todo 
- Perfiles 

# Instalación  
## Servidor físico  
Instalamos los requisitos de Python.  

```bash 
pip install –r requirements.txt 
```
# Variables de entorno 
Es necesario crear el fichero .env con los siguientes parámetros para iniciar la aplicación.

```text 
| Variable                                     | Descripción                                                 | 
|----------------------------------------------|̣̣̣--------------------------------------------------------------|
|FLASK_APP=app                                 | nombre app flask                                             |
|FLASK_DATABASE_HOST=xxx.xxx.xxx.xxx           | IP de la base de datos SQL                                   |
|FLASK_DATABASE_USER=sql                       | Usuario de la base de datos SQL                              |
|FLASK_DATABASE_PASSWORD=Passw0rd$             | Contraseña de la base de datos SQL                           |
|FLASK_DATABASE=SARV3                          | Nombre de la base de datos SQL                               |
|FLASK_SECRET_KEY=yourseccret                  | Secreto para la sesión html                                  |
|FLASK_LDAP_SERVER=xxx.xxx.xxx.xxx             | IP del servidor LDAP                                         |
|FLASK_LDAP_ROOT_DN="dc=CHAOS,dc=GROUP"        | root DN del dominio                                          |
|FLASK_LDAP_USER="CN=user01,dc=CHAOS,dc=GROUP" | Usuario para lectura del LDAP                                 |
|FLASK_LDAP_PASSWORD=Passw0rd                  | Contraseña del usuario lectura LDAP                          |
|FLASK_LDAP_ATTRIBUTE=cn                       | Atributo usuario del LDAP                                            |
|FLASK_LDAP_ATTRIBUTE_MAIL=userPrincipalName   | Atributo Nombre completo del LDAP                            |
|--------------------------------------------------------------------------------------------------------------
```

Iniciamos la base de datos con el comando: 

```bash 
flask init-db 
```
Este comando creará las tablas en la base de dados indicada en las variables de entorno y creará las credenciales por defecto (usuario: admin, contraseña: password)  
Se recomienda crear un nuevo usuario e eliminar el existente durante el primer acceso.  
Una vez inicializada la base de datos podemos iniciar el servidor:
```bash 
gunicorn –w 4 –b 0.0.0.0:8000 app:create_app() 
```
Una vez iniciado podemos acceder a la url del servidor. 
http://localhost:8000 

Una vez iniciado podemos acceder a la url del servidor. 
http://localhost:8000 
