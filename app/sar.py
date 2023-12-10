from flask import (
    Blueprint, flash, g, render_template, request, url_for, session, redirect, current_app, make_response, Response, send_file
)
from app.db import get_db, val_request, approve_request, deny_request
from app.ars import ars_run, cmd_add, cmd_del


bp = Blueprint('sar', __name__, url_prefix='/')



@bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@bp.route('/api', methods=['GET'])
def api():
    uid = request.args.get('uid')
    resource = request.args.get('resource')
    user = request.args.get('user')
    validator = request.args.get('validator')
    action= request.args.get('action')

    try:
        val_uid = val_request(uid, resource, user, validator)
        if  val_uid != None:
            if action == 'approve':
                command = cmd_add(user, resource)
                approve = ars_run(command)
                if approve.returncode != 0:
                    current_app.logger.error('api error aplicando permisos: '+ uid + ' '+ resource + ' '+  user + ' '+  validator + ' '+ action)
                else:
                    approve_request(val_uid[0])
            if action == 'deny':
                deny_request(val_uid[0])
    except:
        current_app.logger.error('api error con los  parametros: '+ uid + ' '+ resource + ' '+  user + ' '+  validator + ' '+ action)
    return render_template('thanks.html')