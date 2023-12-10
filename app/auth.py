from flask import (
    Blueprint, flash, g, render_template,render_template_string, request, url_for, session, redirect, current_app, make_response,jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash
import functools
import uuid
import os
import time
import datetime

from app.db import *
from app.ldap.global_ldap_authentication import *
from app.ldap.LoginForm import *
from . import socketio, join_room
from app.ars import ars_run, cmd_add, cmd_del
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import html
import json


bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.after_request
def add_security_headers(resp):
    #resp.headers['Content-Security-Policy']='default-src \'self\''
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return resp

def request_notify(uid, res, user_id, val):
    to = get_email(val.lower())
    mail_content = """
    <p>Hola,
    -name- ha solicitado permisos para el recurso -res-
    <br>
    <a href:"http//-sever_url-:5000/api?uid=-uid-&resource=-res-&user=-user_id-&validator=-val-&action=approve">aprobar</a>
    <a href:"http//-sever_url-:5000/api?uid=-uid-&resource=-res-&user=-user_id-&validator=-val-&action=deny">denegar</a>

    Gracias por tu colaboración
    </p>
    """
    mail_content = mail_content.replace("-uid-", str(uid))
    mail_content = mail_content.replace("-res-", str(res).strip())
    mail_content = mail_content.replace("-val-", str(val).strip())
    mail_content = mail_content.replace("-user_id-", str(user_id).strip())
    name = get_username(user_id)
    mail_content = mail_content.replace("-name-", str(name[0]))
    #print(mail_content)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # initiate the form..
        form = LoginValidation()
    
        if request.method in ('POST') :
            login_id = request.form['username']
            login_password = request.form['password']
    
            # create a directory to hold the Logs
            login_msg = global_ldap_authentication(login_id, login_password)

            # validate the connection
            if login_msg == "Success":
                success_message = f"*** Authentication Success "
                db, c = get_db()
                error = None
                c.execute(
                    'SELECT username FROM [SARV3].[dbo].[Users] WHERE username = ?', (login_id.lower().strip(),)
                )
                
                user = c.fetchone()

                
                if user is None:
                    # insert database
                    mail = get_email(login_id.lower())
                    name = get_displayName(login_id.lower())

                    db, c = get_db()
                    error = None
                    c.execute(
                    'INSERT INTO [SARV3].[dbo].[Users] (username,mail,name) VALUES (?,?,?)', (login_id.lower().strip(),mail.strip(),name)
                )               
                    db.commit()

                    session.clear()
                    session['user_id'] = login_id.lower()
                    resp = make_response(render_template('auth/personal.html'))
                    return resp
                else:
                    session.clear()
                    session['user_id'] = user[0]
                    requests = get_requests(user[0])
                    permissions = get_permissions(user[0])


                    validator = False
                    admin = False
                    if is_validator(user[0])[0] == True:
                        validator=True

                    if is_admin(user[0])[0] == True:
                        admin=True

                    resp = make_response(render_template('auth/personal.html', requests = requests, permissions = permissions, validator = validator, admin = admin))
                    return resp
          
    
            else:
                error_message = f"*** Authentication Failed - {login_msg}"
                return render_template("auth/error.html", error_message=str(error_message))

        resp = make_response(render_template('auth/login.html', error=error_message))
        return resp

    else:

        resp = make_response(render_template('auth/login.html'))
        return resp
    

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        db, c = get_db()
        c.execute(
            'SELECT username FROM [SARV3].[dbo].[Users] WHERE username = ?', (user_id,)
        )
        g.user = c.fetchone()


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


@bp.route('/')
@login_required
def index():
    resp = make_response(render_template('auth/login.html'))
    return resp

@bp.route('/personal')
@login_required
def personal():
    
    requests = get_requests(session['user_id'])
    permissions = get_permissions(session['user_id'])

    validator = False
    admin = False
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True

    resp = make_response(render_template('auth/personal.html', requests = requests, permissions = permissions, validator=validator, admin=admin))
    return resp

@bp.route('/personal_validator')
@login_required
def personal_validator():

    requests_val = get_requests_val(session['user_id'])
    resources_val = get_resources_val(session['user_id'])

    validator = False
    admin = False
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True

    resp = make_response(render_template('auth/personal_validator.html',resources=resources_val, requests = requests_val, validator=validator ,admin=admin))
    return resp

@bp.route('/admin_panel')
@login_required
def admin_panel():

    validator = False
    admin = False
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True

    resp = make_response(render_template('auth/admin_panel.html', validator=validator ,admin=admin))
    return resp

@bp.route('/admin_requests')
@login_required
def admin_requests():

    requests_val = get_requests_val_adm()
    validator = False
    admin = False
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True

    resp = make_response(render_template('auth/admin_requests.html', requests = requests_val, validator=validator ,admin=admin))
    return resp

@bp.route('/admin_resources', methods=['GET', 'POST'])
@login_required
def admin_resources():
    validator = False
    admin = False
    user_id = session['user_id']
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        owner = request.form['owner']
        path = request.form['path']
        ADGroup = request.form['ADGroup']

        update_resource(name, description, owner, path, ADGroup)

    resources = get_resources_adm('')
    resp = make_response(render_template('auth/admin_resources.html', resources = resources, validator = validator, admin = admin, user_id=user_id))
    return resp

@bp.route('/admin_new_resource', methods=['POST'])
@login_required
def admin_new_resources():
    validator = False
    admin = False
    user_id = session['user_id']
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        owner = request.form['owner']
        path = request.form['path']
        ADGroup = request.form['ADGroup']

        resources = get_resources(name)

        if not resources:
            new_resource(name, description, owner, path, ADGroup)

    resources = get_resources_adm('')
    resp = make_response(render_template('auth/admin_resources.html', resources = resources, validator = validator, admin = admin, user_id=user_id))
    return resp

@bp.route('/admin_validators', methods=['GET','POST'])
@login_required
def admin_validators():
    validator = False
    admin = False
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True
    
    if request.method == 'POST':
        delete = ''
        add = ''
        data =  json.loads(request.data)
        try:
            delete = data['delete_val']
        except:
            pass
        
        try:
            add = data['add_val']
        except:
            pass
        if delete:
            delete_validator(delete)
        
        if add:
            add_validator(add)

        validators = get_allvalidators()
        users = get_notvalidators()
        resp = make_response(render_template('auth/admin_validators.html',validators=validators,users=users, validator=validator ,admin=admin))
        return resp
    else:
        validators = get_allvalidators()
        users = get_notvalidators()
        resp = make_response(render_template('auth/admin_validators.html',validators=validators,users=users, validator=validator ,admin=admin))
        return resp
    
@bp.route('/admin_resource_validators', methods=['GET','POST'])
@login_required
def admin_resource_validators():
    validator = False
    admin = False
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True

    if request.method == 'POST':
        delete = ''
        add = ''
        data =  json.loads(request.data)
        resource = request.cookies.get('resource')

        
        try:
            delete = data['delete_val']
        except:
            pass
        
        try:
            add = data['add_val']
        except:
            pass
        if delete:
            delete_resource_validator(resource, delete)
        
        if add:
            add_resource_validator(resource, add)

        validators = get_all_resource_validators(resource)
        users = get_resource_notvalidators(resource)
        resp = make_response(render_template('auth/admin_resource_validators.html',resource=resource, validators=validators,users=users, validator=validator ,admin=admin))
        resp.set_cookie('resource', resource)
        return resp
    else:
        if request.args.get('resource') != None:
            resource = request.args.get('resource')
            print('error en get')
        else:
            resource = request.cookies.get('resource')
            print('error en cooky')

        validators = get_all_resource_validators(resource)
        users = get_resource_notvalidators(resource)
        resp = make_response(render_template('auth/admin_resource_validators.html',resource=resource, validators=validators,users=users, validator=validator ,admin=admin))
        resp.set_cookie('resource',  resource)
        return resp

@bp.route('/admin_administrators', methods=['GET','POST'])
@login_required
def admin_administrators():
    validator = False
    admin = False
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True
    
    if request.method == 'POST':
        delete = ''
        add = ''
        data =  json.loads(request.data)
        try:
            delete = data['delete_adm']
        except:
            pass
        
        try:
            add = data['add_adm']
        except:
            pass
        if delete:
            delete_administrator(delete)
        
        if add:
            add_administrator(add)

        administrators = get_alladministrators()
        users = get_notadministrators()
        resp = make_response(render_template('auth/admin_administrators.html',administrators=administrators,users=users, validator=validator ,admin=admin))
        return resp
    else:
        administrators = get_alladministrators()
        users = get_notadministrators()
        resp = make_response(render_template('auth/admin_administrators.html',administrators=administrators,users=users, validator=validator ,admin=admin))
        return resp

@bp.route('/requests', methods=['GET', 'POST'])
@login_required
def requests():
    validator = False
    admin = False
    user_id = session['user_id']
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True

    if request.method == 'POST':
        user_id = session.get('user_id')
        data =  json.loads(request.data)
        val = data['val']
        res = data['rec']
       
        set_request(res, user_id, val)
        uid = get_UID(res, user_id, val)
        request_notify(str(uid[0]), res, user_id, val)

        resp = make_response(render_template('auth/personal.html', validator = validator, admin = admin))
        return resp
    
    else:
        resp = make_response(render_template('auth/requests.html', validator = validator, admin = admin, user_id=user_id))
        return resp
    
@bp.route('/thanks')
@login_required
def thanks():
    resp = make_response(render_template('auth/thanks.html'))
    return resp

@bp.route('/request_deny')
@login_required
def request_deny():
    UID = request.args.get('uid')
    deny_request(UID)
    
    requests_val = get_requests_val(session['user_id'])
    validator = False
    admin = False
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True

    resp = make_response(render_template('auth/personal_validator.html', requests = requests_val, validator=validator ,admin=admin))
    return resp

@bp.route('/request_delete_adm')
@login_required
def request_delete_adm():
    UID = request.args.get('uid')
    delete_request(UID)
    
    requests_val = get_requests_val_adm()
    validator = False
    admin = False
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True

    resp = make_response(render_template('auth/admin_requests.html', requests = requests_val, validator=validator ,admin=admin))
    return resp

@bp.route('/request_manual_adm')
@login_required
def request_manual_adm():
    UID = request.args.get('uid')
    manual_request(UID)
    
    requests_val = get_requests_val_adm()
    validator = False
    admin = False
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True

    resp = make_response(render_template('auth/admin_requests.html', requests = requests_val, validator=validator ,admin=admin))
    return resp

@bp.route('/request_approve')
@login_required
def request_approve():
    UID = request.args.get('uid')
    user = get_request_user(UID)
    resource = get_request_resource(UID)

    command = cmd_add(user, resource)
    approve = ars_run(command)
    if approve.returncode != 0:
        current_app.logger.error('api error aplicando permisos: '+ UID + ' '+ resource + ' '+  user + ' '+  validator )
    else:
        approve_request(UID)
   
    
    
    requests_val = get_requests_val(session['user_id'])
    validator = False
    admin = False
    if is_validator(session['user_id'])[0] == True:
        validator=True
    if is_admin(session['user_id'])[0] == True:
        admin=True

    resp = make_response(render_template('auth/personal_validator.html', requests = requests_val, validator=validator ,admin=admin))
    return resp


@socketio.on('resource')
def handle_message(data):
    # Maneja el evento 'message' recibido desde el cliente
    # Puedes realizar acciones específicas aquí
    room = session['user_id']
    str = data['data']
    resources = get_resources(str)
    # Genera una tabla HTML de ejemplo (puedes personalizarla según tus datos)
    html_table = """
        <table class="report-table" id="tbl-resources">
        <thead>
            <tr>
                <th>Nombre</th>
                <th>Descripción</th>
            </tr>
        </thead>
        {% for reg in resources %}
        <tr class="fila-tabla" data-name={{ reg['name'] }}>
            <td>{{ reg['name'] }}</td>
            <td>{{ reg['description'] }}</td>
        </tr>
        {% if not loop.last%}
        {%endif%}
        {%endfor%}
    </table>
    """
    join_room(room)
    
    # Emitir la tabla HTML como respuesta al cliente
    rendered_table = render_template_string(html_table, resources=resources)
    socketio.emit('resources', {'html_table': rendered_table}, room=room)

@socketio.on('validators')
def handle_message(data):
    # Maneja el evento 'message' recibido desde el cliente
    # Puedes realizar acciones específicas aquí
    str = data['data']
    resources = get_validators(str)
    room = session['user_id']
    # Genera una tabla HTML de ejemplo (puedes personalizarla según tus datos)
    html_table = """
        <table class="report-table" id="tbl-validators">
        <thead>
            <tr>
                <th>Nombre</th>
                <th>email</th>
            </tr>
        </thead>
        {% for reg in resources %}
        <tr class="fila-tabla" data-name={{ reg['username'] }}>
            <td>{{ reg['name'] }}</td>
            <td>{{ reg['mail'] }}</td>
        </tr>
        {% if not loop.last%}
        {%endif%}
        {%endfor%}
    </table>
    """
    join_room(room)
    
    # Emitir la tabla HTML como respuesta al cliente
    rendered_table = render_template_string(html_table, resources=resources)
    socketio.emit('validators', {'html_table': rendered_table}, room=room)

@socketio.on('resource-adm')
def handle_message(data):
    # Maneja el evento 'message' recibido desde el cliente
    # Puedes realizar acciones específicas aquí
    str = data['data']
    room = session['user_id']
    resources = get_resources_adm(str)
    # Genera una tabla HTML de ejemplo (puedes personalizarla según tus datos)
    html_table = """
        <table class="report-table" id="tbl-resources-adm">
        <thead>
            <tr>
                <th>Recurso</th>
                <th>Descripción</th>
                <th>Owner</th>
                <th>Path</th>
                <th>AD group</th>
                <th>Acción</th>

            </tr>
        </thead>
        {% for reg in resources %}
        <tr class="fila-tabla" data-name={{ reg['name'] }}>
            <td>{{ reg['name'] }}</td>
            <td>{{ reg['description'] }}</td>
            <td>{{ reg['owner'] }}</td>
            <td>{{ reg['path'] }}</td>
            <td>{{ reg['ADGroup'] }}</td>
            <td>
                &nbsp;&nbsp;
                <a class="table-button" href="javascript:void(0);" onclick="deleteRessources('{{ reg['name'] }}');">X</a>
                <a class="table-button" href="javascript:void(0);" onclick="modifyRessource('{{ reg['name'] }}');">M</a>
                <a class="table-button" href="/auth/admin_resource_validators?resource={{ reg['name'] }}">V</a>
            </td>
        </tr>
        {% if not loop.last%}
        {%endif%}
        {%endfor%}
    </table>
    """
    join_room(room)
    
    # Emitir la tabla HTML como respuesta al cliente
    rendered_table = render_template_string(html_table, resources=resources)
    socketio.emit('resources-adm', {'html_table': rendered_table}, room=room)

@socketio.on('resource-delete-adm')
def handle_message(data):
    # Maneja el evento 'message' recibido desde el cliente
    # Puedes realizar acciones específicas aquí
    
    str = data['data']
    delete_resource(str)
    room = session['user_id']
    resources = get_resources_adm(str)
    # Genera una tabla HTML de ejemplo (puedes personalizarla según tus datos)
    html_table = """
        <table class="report-table" id="tbl-resources-adm">
        <thead>
            <tr>
                <th>Recurso</th>
                <th>Descripción</th>
                <th>Owner</th>
                <th>Path</th>
                <th>AD group</th>
                <th>Acción</th>

            </tr>
        </thead>
        {% for reg in resources %}
        <tr class="fila-tabla" data-name={{ reg['name'] }}>
            <td>{{ reg['name'] }}</td>
            <td>{{ reg['description'] }}</td>
            <td>{{ reg['owner'] }}</td>
            <td>{{ reg['path'] }}</td>
            <td>{{ reg['ADGroup'] }}</td>
            <td>
                &nbsp;&nbsp;
                <a class="table-button" href="javascript:void(0);" onclick="deleteRessources('{{ reg['name'] }}');">X</a>
                <a class="table-button" href="javascript:void(0);" onclick="modifyRessource('{{ reg['name'] }}');">M</a>
                <a class="table-button" href="/auth/admin_resource_validators?resource={{ reg['name'] }}">V</a>
            </td>
        </tr>
        {% if not loop.last%}
        {%endif%}
        {%endfor%}
    </table>
    """
    join_room(room)
    
    # Emitir la tabla HTML como respuesta al cliente
    rendered_table = render_template_string(html_table, resources=resources)
    socketio.emit('resources-adm', {'html_table': rendered_table}, room=room)

@socketio.on('resource-modify-adm')
def handle_message(data):
    # Maneja el evento 'message' recibido desde el cliente
    # Puedes realizar acciones específicas aquí
    
    str = data['data']
    get_resources_adm(str)
    room = session['user_id']
    resources = get_resources_adm(str)
    # Genera una tabla HTML de ejemplo (puedes personalizarla según tus datos)
  
    html_form = """
        <form id="frm-resources-adm" method="post" action="admin_resources">
            <label name="name"> Recurso</label>
            <input name="name" type="text" value="{{ resources[0][0] }}" required readonly>

            <label name="description">Descripción</label>
            <input name="description" type="text" value="{{ resources[0][1] }}">

            <label name="owner">Owner</label>
            <input name="owner" type="text" value="{{ resources[0][2] }}">
            
            <label name="path">Path</label><br>
            <input name="path" type="text" value="{{ resources[0][3] }}">

            <label name="ADGroup">AD group</label>
            <input name="ADGroup" type="text"  value="{{ resources[0][4] }}">
            
            <input class="button" type="submit" value="Modificar">
        </form>
    """
    join_room(room)
    
    # Emitir la tabla HTML como respuesta al cliente
    rendered_table = render_template_string(html_form, resources=resources)
    socketio.emit('resource-modify-adm', {'html_form': rendered_table}, room=room)

@socketio.on('resource-new-adm')
def handle_message(data):
 # Maneja el evento 'message' recibido desde el cliente
    # Puedes realizar acciones específicas aquí
    room = session['user_id']
    # Genera una tabla HTML de ejemplo (puedes personalizarla según tus datos)
  
    html_form = """
        <form id="frm-resources-adm" method="post" action="admin_new_resource">
            <label name="name"> Recurso</label>
            <input name="name" type="text" value="" required >

            <label name="description">Descripción</label>
            <input name="description" type="text" value="">

            <label name="owner">Owner</label>
            <input name="owner" type="text" value="">
            
            <label name="path">Path</label><br>
            <input name="path" type="text" value="">

            <label name="ADGroup">AD group</label>
            <input name="ADGroup" type="text"  value="">
            
            <input class="button" type="submit" value="Añadir">
        </form>
    """
    join_room(room)
    
    # Emitir la tabla HTML como respuesta al cliente
    rendered_table = render_template_string(html_form, resources="")
    socketio.emit('resource-modify-adm', {'html_form': rendered_table}, room=room)
