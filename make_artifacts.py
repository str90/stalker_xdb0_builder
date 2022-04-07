import configparser
import os
from os import path
import shutil
from pathlib import Path
import subprocess

def makeXdb(xdbcounter, xdbname, builderPath):
    packParameter = ' -pack ' + builderPath + '\\temp\\' + str(xdbcounter)
    outParameter = ' -out ' + builderPath + '\\artifacts\\xdb\\' + xdbname + str(xdbcounter) + '.xdb0'
    converterString = 'build_tools\\xdb_converter\\converter.exe' + packParameter + outParameter
    subprocess.call(converterString, shell=True)
    xdbcounter += 1
    return xdbcounter

def calcCrc32(fileToCalc):
    t = str(subprocess.check_output(['build_tools\\crc32.exe', fileToCalc, '-nf']))
    r = t.split(r'\r')[0].split('\'')[1]
    return r

bufferArtifactSize = 0
file_makedir_path = ''
xdbcounter = 0

configArtBuilder = configparser.ConfigParser()
configArtBuilder.read('builder_config.ini')

xdbname = configArtBuilder['artifactbuilder']['xdb_name']
targetArtifactSize = int(configArtBuilder['artifactbuilder']['target_artifact_size']) * 1024 * 1024
builderPath = configArtBuilder['artifactbuilder']['builder_path']
gamedatadir = os.walk(configArtBuilder['artifactbuilder']['mod_gamedata_path'])

print('Cleaning for new build: \n')

Path("temp").mkdir(parents=True, exist_ok=True)
Path("artifacts\\xdb").mkdir(parents=True, exist_ok=True)
Path("artifacts\\artifacts_cab_fileserver").mkdir(parents=True, exist_ok=True)
shutil.rmtree('temp', ignore_errors=True, onerror=None)
shutil.rmtree('artifacts\\artifacts_cab_fileserver', ignore_errors=True, onerror=None)
Path("temp").mkdir(parents=True, exist_ok=True)
Path("artifacts\\xdb").mkdir(parents=True, exist_ok=True)
Path("artifacts\\artifacts_cab_fileserver").mkdir(parents=True, exist_ok=True)

print('Building xdb0 files: \n')

for root, directories, filenames in gamedatadir:
    for filename in filenames:
        filepath = os.path.join(root, filename)
        filesizevar = os.stat(filepath).st_size
        file_makedir_path = filepath.partition('gamedata')[2].split('\\')[:-1]
        file_makedir_path = '\\' + os.path.join(*file_makedir_path)

        if bufferArtifactSize + filesizevar >= targetArtifactSize:
            xdbcounter = makeXdb(xdbcounter, xdbname, builderPath)
            bufferArtifactSize = 0

        bufferArtifactSize += filesizevar
        file_makedir_path = 'temp\\' + str(xdbcounter) + file_makedir_path
        Path(file_makedir_path).mkdir(parents=True, exist_ok=True)
        shutil.copy(filepath, file_makedir_path)


lastfilepath = 'artifacts\\xdb\\' + xdbname + str(xdbcounter) + '.xdb0'
if not path.exists(lastfilepath):
   xdbcounter = makeXdb(xdbcounter, xdbname, builderPath)

makecabString = 'makecab /V1 /L artifacts_cab_fileserver artifacts\\xdb\\' + xdbname + str(xdbcounter) + '.xdb0'

configFzGamedata = configparser.ConfigParser()
configFzGamedata['main'] = {'files_count': xdbcounter}

for i in range(xdbcounter):
    cabPath = 'artifacts\\artifacts_cab_fileserver\\' + xdbname + str(i) + '.xdb0.cab'
    makecabString = 'makecab /V1 /L artifacts\\artifacts_cab_fileserver artifacts\\xdb\\' + xdbname + str(i) + '.xdb0 ' + xdbname + str(i) + '.xdb0.cab'
    subprocess.call(makecabString)
    print('Making config entry and calculating CRC32 for game asset #: ', str(i))
    configFzGamedata['file_' + str(i)] = {'path': configArtBuilder['cabmaker']['path'] + xdbname + str(i) + '.xdb0',
                                          'url': configArtBuilder['cabmaker']['url'] + xdbname + str(i) + '.xdb0.cab',
                                          'size': str(os.stat(cabPath).st_size), 'crc32': calcCrc32(cabPath), 'compression': '2'}

configFzGamedata.write(open('artifacts\\artifacts_cab_fileserver\\' + configArtBuilder['cabmaker']['cab_config_name'], 'w'))

print('Cleaning temporary files: \n')
shutil.rmtree('temp', ignore_errors=True, onerror=None)
print(r'Path of xdb0 for server: artifacts\xdb')
print('\n')
print(r'Path of cab files for fileserver and .ini config of gamedata: artifacts\artifacts_cab_fileserver')
print('\n')
print('\n')
print('Game assets built. Have a nice day, bye !')
