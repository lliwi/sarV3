from ldap3 import Server, Connection, ALL, SUBTREE, SIMPLE, NTLM
from ldap3.core.exceptions import LDAPException, LDAPBindError
from flask import current_app

def global_ldap_authentication(user_name, user_pwd):
    # LDAP server hostname and port
    ldap_server = "ldap://" + current_app.config['LDAP_SERVER'] + ":389"
    # Root DN
    root_dn = current_app.config['LDAP_ROOT_DN']
    # Service account DN and password
    service_dn = current_app.config['LDAP_USER']
    service_password = current_app.config['LDAP_PASSWORD']
    # Group DN to check membership
    if current_app.config['LDAP_GROUP_DN']:
        group_dn = current_app.config['LDAP_GROUP_DN']

    # Create server and connection objects

    server = Server(ldap_server)
    conn = Connection(server, user=service_dn, password=service_password, authentication=SIMPLE)

    try:

        # Authenticate service account
        conn.bind()

 

        # Search for the user
        search_filter = f"({current_app.config['LDAP_ATTRIBUTE']}={user_name})"
        conn.search(search_base=root_dn, search_filter=search_filter, search_scope=SUBTREE)

       

        # Check if the user was found
        if len(conn.entries) == 0:
            return "User not found"

 

        # Construct user_dn using the distinguishedName attribute of the user object
        user_dn = conn.entries[0].entry_dn

        # Authenticate user
        user_conn = Connection(server, user=user_dn, password=user_pwd, authentication=SIMPLE)
        user_conn.bind()

        # Check if the user authentication is successful
        if not user_conn.bound:
            return "Invalid credentials"

 

        # Check group membership
        if current_app.config['LDAP_GROUP_DN']:
            group_filter = f"(&(objectClass=user)(distinguishedName={user_dn})(memberOf={group_dn}))"
            conn.search(search_base=root_dn, search_filter=group_filter, search_scope=SUBTREE)
 

        # If the user is not a member of the group, return an error message
        if len(conn.entries) == 0:
            return "User is not a member of the required group"

        # Authentication and group membership validation successful
        return "Success"



    except LDAPException as e:
        # Authentication failed
        return f"LDAP error: {e}"

def get_email(user_name):
    # LDAP server hostname and port
    ldap_server = "ldap://" + current_app.config['LDAP_SERVER'] + ":389"
    # Root DN
    root_dn = current_app.config['LDAP_ROOT_DN']
    # Service account DN and password
    service_dn = current_app.config['LDAP_USER']
    service_password = current_app.config['LDAP_PASSWORD']
    # Group DN to check membership
    if current_app.config['LDAP_GROUP_DN']:
        group_dn = current_app.config['LDAP_GROUP_DN']

    # Create server and connection objects

    server = Server(ldap_server)
    conn = Connection(server, user=service_dn, password=service_password, authentication=SIMPLE)

    # Realiza la autenticación
    if conn.bind():
        # Busca al usuario y obtén su correo electrónico
        username_to_search = user_name 

        search_filter = f'(&(objectClass=user)(sAMAccountName={username_to_search}))'
        conn.search(search_base=root_dn, search_filter=search_filter,attributes=['userPrincipalName'])

        if conn.entries:
            email = conn.entries[0]['userPrincipalName'].value
            #print(f"Email del usuario: {email}")
        else:
            print("Usuario no encontrado o no tiene correo electrónico.")
    else:
        print("Error de autenticación en Active Directory")

    # Cierra la conexión
    conn.unbind()
    return email

def get_displayName(user_name):
    # LDAP server hostname and port
    ldap_server = "ldap://" + current_app.config['LDAP_SERVER'] + ":389"
    # Root DN
    root_dn = current_app.config['LDAP_ROOT_DN']
    # Service account DN and password
    service_dn = current_app.config['LDAP_USER']
    service_password = current_app.config['LDAP_PASSWORD']
    # Group DN to check membership
    if current_app.config['LDAP_GROUP_DN']:
        group_dn = current_app.config['LDAP_GROUP_DN']

    # Create server and connection objects

    server = Server(ldap_server)
    conn = Connection(server, user=service_dn, password=service_password, authentication=SIMPLE)

    # Realiza la autenticación
    if conn.bind():
        # Busca al usuario y obtén su correo electrónico
        username_to_search = user_name 

        search_filter = f'(&(objectClass=user)(sAMAccountName={username_to_search}))'
        conn.search(search_base=root_dn, search_filter=search_filter,attributes=['displayName'])

        if conn.entries:
            name = conn.entries[0]['displayName'].value
            #print(f"Email del usuario: {email}")
        else:
            print("Usuario no encontrado o no tiene correo electrónico.")
    else:
        print("Error de autenticación en Active Directory")

    # Cierra la conexión
    conn.unbind()
    return name