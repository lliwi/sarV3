import pyodbc 
import click
from flask import current_app, g
from flask.cli import with_appcontext
from .schema import instructions


def get_db():
    if 'db' not in g:
        g.db = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server}; SERVER=" 
            + current_app.config['DATABASE_HOST']+";DATABASE="
            + current_app.config['DATABASE']+";UID="
            + current_app.config['DATABASE_USER']+";PWD="
            + current_app.config['DATABASE_PASSWORD']
        )
        g.c = g.db.cursor()
    return g.db, g.c


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db, c = get_db()

    for i in instructions:
        c.execute(i)

    db.commit()


@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Base de datos inicializada')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def get_requests(user):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [Resources].name, [Resources].description, [validator],[status],[date] 
        FROM [SARV3].[dbo].[Requests] 
        INNER JOIN [SARV3].[dbo].[Resources] ON [Requests].[resource] = [Resources].name WHERE username = ?''', (user,)
    )
    return c.fetchall()

def get_requests_val(validator):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [Users].[name], [Requests].[resource], [Resources].[description] ,[status]  ,[date], [UID]
        FROM [SARV3].[dbo].[Requests]
        INNER JOIN [SARV3].[dbo].[Users] ON [Requests].[username] = [Users].[username]
        INNER JOIN [SARV3].[dbo].[Resources] ON [Requests].[resource] = [Resources].[name]
        WHERE  [status] = 'New' AND [validator] =?''', (validator,)
    )
    return c.fetchall()


def get_resources_val(validator):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT  [name] ,[description],[path] 
        FROM [SARV3].[dbo].[Resources]
        WHERE [owner] = ?''', (validator,)
    )
    return c.fetchall()

def get_requests_val_adm():
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [Users].[name], [Requests].[resource], [Resources].[description] ,[status]  ,[date], [UID]
        FROM [SARV3].[dbo].[Requests]
        INNER JOIN [SARV3].[dbo].[Users] ON [Requests].[username] = [Users].[username]
        INNER JOIN [SARV3].[dbo].[Resources] ON [Requests].[resource] = [Resources].[name]
        WHERE  [status] = 'New' '''
    )
    return c.fetchall()

def deny_request(UID):
    db, c = get_db()
    error = None
    c.execute(
        '''UPDATE [SARV3].[dbo].[Requests] SET [status] = 'Denied' 
            WHERE [UID] = ?''', (UID,)
    )
    db.commit()
    return

def delete_request(UID):
    db, c = get_db()
    error = None
    c.execute(
        '''UPDATE [SARV3].[dbo].[Requests] SET [status] = 'Deleted' 
            WHERE [UID] = ?''', (UID,)
    )
    db.commit()
    return

def get_request_user(uid):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT username
        FROM [SARV3].[dbo].[Requests]

        WHERE  [UID] =?''', (uid,)
    )
    return c.fetchone()

def get_request_resource(uid):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [resource]
        FROM [SARV3].[dbo].[Requests]

        WHERE  [UID] =?''', (uid,)
    )
    return c.fetchone()

def approve_request(UID):
    db, c = get_db()
    error = None
    c.execute(
        f"""UPDATE [SARV3].[dbo].[Requests] SET [status] = 'Approved' 
            WHERE [UID] = '{UID}'

            INSERT INTO [SARV3].[dbo].[Permissions] ([resouce] ,[username] ,[date]) 
            VALUES ((SELECT  [resource]  FROM [SARV3].[dbo].[Requests] WHERE [UID] = '{UID}'),(SELECT [username] FROM [SARV3].[dbo].[Requests] WHERE [UID] = '{UID}'),CURRENT_TIMESTAMP)
            """
    )
    db.commit()
    return


def manual_request(UID):
    db, c = get_db()
    error = None
    c.execute(
        f"""UPDATE [SARV3].[dbo].[Requests] SET [status] = 'Manual' 
            WHERE [UID] = '{UID}'

            INSERT INTO [SARV3].[dbo].[Permissions] ([resouce] ,[username] ,[date]) 
            VALUES ((SELECT  [resource]  FROM [SARV3].[dbo].[Requests] WHERE [UID] = '{UID}'),(SELECT [username] FROM [SARV3].[dbo].[Requests] WHERE [UID] = '{UID}'),CURRENT_TIMESTAMP)
            """
    )
    db.commit()
    return

def get_permissions(user):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [Resources].name, [Resources].description, [Resources].owner,[Resources].path, [date]
        FROM [SARV3].[dbo].[Permissions]
        INNER JOIN [SARV3].[dbo].[Resources] ON [Permissions].[resouce] = [Resources].name WHERE username = ?''', (user,)
    )
    return c.fetchall()

def get_resources(str):
    db, c = get_db()
    error = None
    c.execute(
        f"""SELECT [name] ,[description]
        FROM [SARV3].[dbo].[Resources] 
        WHERE name like '%{str}%' OR description like '%{str}%'"""
    )
    return c.fetchall()

def get_resources_adm(str):
    db, c = get_db()
    error = None
    c.execute(
        f"""SELECT [name] ,[description], [owner], [path], [ADGroup]
        FROM [SARV3].[dbo].[Resources] 
        WHERE name like '%{str}%' OR description like '%{str}%'"""
    )
    return c.fetchall()

def delete_resource(str):
    db, c = get_db()
    error = None
    c.execute(
        '''DELETE FROM  [SARV3].[dbo].[Resources] 
        WHERE [name] = ?''', (str,)
    )
    db.commit()
    del_resource_validators(str.strip())
    return

def update_resource(name, description, onwer, path, ADGroup):
    db, c = get_db()
    error = None
    c.execute(
        '''UPDATE [SARV3].[dbo].[Resources] 
        SET [name] = ?,[description] = ?, [owner] = ?, [path] = ?, [ADGroup] = ?
        WHERE [name] = ?''', (name, description, onwer, path, ADGroup, name)
    )
    db.commit()
    return

def new_resource(name, description, onwer, path, ADGroup):
    db, c = get_db()
    error = None
    c.execute(
        '''INSERT INTO [SARV3].[dbo].[Resources] ([name],[description], [owner], [path], [ADGroup])
        VALUES ( ?,?,?,?,?)
        ''', (name.strip(), description, onwer.strip(), path, ADGroup.strip())
    )
    add_resource_validator(name.strip(), onwer.strip())
    db.commit()

    return

def get_all_resource_validators(resource):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [Validators].[username], [Users].name, [Users].mail
        FROM [SARV3].[dbo].[Validators] 
        JOIN [SARV3].[dbo].[Users] ON [Validators].username = [Users].username
        WHERE [resource] = ?''', (resource,)
    )
    return c.fetchall()

def get_resource_notvalidators(resource):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [username] ,[mail] ,[name]
        FROM [SARV3].[dbo].[Users] WHERE [username] NOT IN (
        SELECT [username] FROM [SARV3].[dbo].[Validators]
        WHERE [resource] = ?)''', (resource,)
    )
    return c.fetchall()

def delete_resource_validator(resource, username):
    db, c = get_db()
    error = None
    c.execute(
        '''DELETE  FROM [SARV3].[dbo].[Validators]
        WHERE [resource] = ? AND [username] = ?
        ''', (resource, username )
    )
    db.commit()
    return

def del_resource_validators(resource):
    db, c = get_db()
    error = None
    c.execute(
        '''DELETE FROM [SARV3].[dbo].[Validators]
        WHERE [resource] = ?
        ''', (resource )
    )
    db.commit()
    return

def add_resource_validator(resource, username):
    db, c = get_db()
    error = None
    c.execute(
        '''INSERT INTO [SARV3].[dbo].[Validators]
        ([resource],[username]) VALUES (?,?)
        ''', (resource,username )
    )
    db.commit()
    return


def get_validators(str):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [Validators].[username], [Users].name, [Users].mail
        FROM [SARV3].[dbo].[Validators]
        INNER JOIN [SARV3].[dbo].[Users] ON [Users].username = [Validators].username
        WHERE resource in (SELECT  [name] FROM [SARV3].[dbo].[Resources]
        WHERE name = ?)''', (str,)
    )
    return c.fetchall()

def get_allvalidators():
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [username], name, mail
        FROM [SARV3].[dbo].[Users]
        WHERE isValidator = 1'''
    )
    return c.fetchall()


def delete_validator(username):
    db, c = get_db()
    error = None
    c.execute(
        '''UPDATE [SARV3].[dbo].[Users] SET isValidator = NULL
        WHERE [username] = ?
        ''', (username )
    )
    db.commit()
    return

def add_validator(username):
    db, c = get_db()
    error = None
    c.execute(
        '''UPDATE [SARV3].[dbo].[Users] SET isValidator = 1
        WHERE [username] = ?
        ''', (username )
    )
    db.commit()
    return

def get_notvalidators():
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [username], name, mail
        FROM [SARV3].[dbo].[Users]
        WHERE isValidator IS NULL'''
    )
    return c.fetchall()

def get_alladministrators():
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [username], name, mail
        FROM [SARV3].[dbo].[Users]
        WHERE isAdmin = 1'''
    )
    return c.fetchall()

def get_notadministrators():
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [username], name, mail
        FROM [SARV3].[dbo].[Users]
        WHERE isAdmin IS NULL'''
    )
    return c.fetchall()

def delete_administrator(username):
    db, c = get_db()
    error = None
    c.execute(
        '''UPDATE [SARV3].[dbo].[Users] SET isAdmin = NULL
        WHERE [username] = ?
        ''', (username )
    )
    db.commit()
    return

def add_administrator(username):
    db, c = get_db()
    error = None
    c.execute(
        '''UPDATE [SARV3].[dbo].[Users] SET isAdmin = 1
        WHERE [username] = ?
        ''', (username )
    )
    db.commit()
    return

def set_request(resource, user, validator):
    db, c = get_db()
    error = None
    c.execute(
        '''INSERT INTO [SARV3].[dbo].[Requests] ( [resource],[username],[validator],[UID],[status],[date])
        VALUES (?,?,?,NEWID(),'New', CURRENT_TIMESTAMP )''', (resource.strip(), user.strip(), validator.strip())
    )
    db.commit()
    return

def get_UID(resource, user, validator):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT UID FROM [SARV3].[dbo].[Requests] WHERE [username] = ? AND [validator] = ? AND [resource] = ?''', (user, validator, resource)
    )
    return c.fetchone()

def is_validator(str):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [isValidator] FROM [SARV3].[dbo].[Users] Where [username] = ?''', (str,)
    )
    return c.fetchone()

def is_admin(str):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [isAdmin] FROM [SARV3].[dbo].[Users] Where [username] = ?''', (str,)
    )
    return c.fetchone()

def get_username(str):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [name] FROM [SARV3].[dbo].[Users] Where [username] = ?''', (str,)
    )
    return c.fetchone()

def val_request(uid, resource, user, validator):
    db, c = get_db()
    error = None
    c.execute(
        '''SELECT [UID] FROM [SARV3].[dbo].[Requests] 
        WHERE [UID] = ? AND [resource] = ? AND [username] = ? AND [validator] = ? AND [status] = ?''', (uid, resource,user,validator,'New')
    )
    return c.fetchone()