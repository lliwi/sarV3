import os
from flask import Flask
from flask_socketio import SocketIO, join_room

from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()

socketio = SocketIO()

# Configuración del logging
import logging

log_level = os.environ.get('LOG_LEVEL', 'DEBUG')  # Puedes ajustar el nivel según tus necesidades
log_file = os.environ.get('LOG_FILE', 'sarv3.log')
# Configuración del logger principal de la aplicación
logging.basicConfig(filename=log_file, level=log_level)


def create_app():
    app = Flask(__name__)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('FLASK_SECRET_KEY'),
        DATABASE_HOST=os.environ.get('FLASK_DATABASE_HOST'),
        DATABASE_PASSWORD=os.environ.get('FLASK_DATABASE_PASSWORD'),
        DATABASE_USER=os.environ.get('FLASK_DATABASE_USER'),
        DATABASE=os.environ.get('FLASK_DATABASE'),
        LDAP_SERVER=os.environ.get('FLASK_LDAP_SERVER'),
        LDAP_ROOT_DN=os.environ.get('FLASK_LDAP_ROOT_DN'),
        LDAP_USER=os.environ.get('FLASK_LDAP_USER'),
        LDAP_PASSWORD=os.environ.get('FLASK_LDAP_PASSWORD'),
        LDAP_ATTRIBUTE=os.environ.get('FLASK_LDAP_ATTRIBUTE'),
        LDAP_ATTRIBUTE_MAIL=os.environ.get('FLASK_LDAP_ATTRIBUTE_MAIL'),
        LDAP_GROUP_DN=os.environ.get('FLASK_LDAP_GROUP_DN')

    )

    app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    )
  

    from . import db
    db.init_app(app)

    from . import sar
    app.register_blueprint(sar.bp)

    from . import auth
    app.register_blueprint(auth.bp)

    # Inicializa Socket.IO con tu aplicación
    socketio.init_app(app)

    # Hacer que el logger esté disponible globalmente
    app.logger.addHandler(logging.FileHandler(log_file))
    app.logger.setLevel(log_level)

  
    return app
