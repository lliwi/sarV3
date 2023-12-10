from flask import current_app, g
from flask.cli import with_appcontext
import subprocess


def cmd_add(user, resource):
    add_command = """
    Write-Host 'approved' resource -resource- for user -user-
    Clear-Host

    Import-Module ActiveRolesConfiguration -DisableNameChecking

    $null = Connect-QADService -Service 'ARSDE.in.audi.vwg' -Proxy
      
    try{
        $null = Add-QADGroupMember -Identity -resource- -Member -user-
    }catch{
        Write-Host "Failure while trying to add -user- to -resource-"
        Add-Content C:\temp\sarv3.txt "Failure while trying to add -user- to -resource-"
                
    }
    """
    add_command = add_command.replace('-user-', str(user).strip())
    add_command = add_command.replace('-resource-', str(resource).strip())

    return add_command

def cmd_del(user, resource):
    del_command = """
    Write-Host 'approved' resource -resource- for user -user-
    Clear-Host

    Import-Module ActiveRolesConfiguration -DisableNameChecking

    $null = Connect-QADService -Service 'ARSDE.in.audi.vwg' -Proxy

    try{
        $null = Remove-QADGroupMember -Identity -resource- -Member -user-
    }catch{
         Write-Host "Failure while trying to remove -user- to -resource-"
         Add-Content C:\temp\sarv3.txt "Failure while trying to remove -user- to -resource-"            
    }
    """
    del_command = del_command.replace('-user-', str(user).strip())
    del_command = del_command.replace('-resource-', str(resource).strip())

    return del_command

def ars_run(command):
    completed = subprocess.run(["powershell", "-Command", command], capture_output=True)
    return completed
