# Imports for Google SQL client library
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import aiomysql
import pymysql 

#Imports for aiohttp/asyncio
from aiohttp import web
import aiohttp_cors
import asyncio

# Imports for Python libaries
import sys
import time
from collections import OrderedDict
import os, os.path
import json
import csv
import io
import signal
import socket
import resource
import hashlib

M_POOL = None

### Hard coded ###
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./dazzling-reach-228306-1db7c4710ccd.json"

# Authentication for Google SQL
credentials = GoogleCredentials.get_application_default()
service = discovery.build('sqladmin', 'v1beta4', credentials=credentials)

### Hard coded ###
projectName = 'dazzling-reach-228306'  
instanceName = 'fp-test'
tableName = 'fpTable'   



def convertListToString(inList, isValue):
    if len(inList) == 0:
        result = ""
        return result
        
    result = "("
    for x in inList:
        if isValue:
            result +=  "'" +  str(x) + "', "
        else:
            result +=  str(x) + ", "
    result = result[:-2] + ")"
    return result


    
async def get_pool(loop):
    global M_POOL
    if M_POOL: 
        return M_POOL
    ### Hard coded ###    
    M_POOL = await aiomysql.create_pool(host='35.224.179.182',
                                        user='root',
                                        password='',
                                        db='testDB',
                                        loop=loop,
                                        maxsize=1000)  
    return M_POOL                                    

    
    
def close_pool():
    global M_POOL
    M_POOL.terminate()
    M_POOL.wait_closed()
 

 
# Create local file from Google SQL JSON results
async def insertToSQL(dataParam): 
    keyList = []
    valueList = []
    concatString = ""
    
    for aPair in dataParam:
        keyList.append("`" + aPair['key'] + "`")
        valueList.append(str(aPair['value']).replace("'", r"\'"))
        concatString = concatString + str(aPair['value']).replace("'", r"\'")

    hasher = hashlib.sha3_512()
    hasher.update(concatString.encode('UTF-8'))
    hashString = hasher.hexdigest()
    
    keyList.append('`concatHash`')   
    valueList.append(hashString)    
        
    columns = convertListToString(keyList, False)
    values = convertListToString(valueList, True)

    loop = asyncio.get_event_loop()
    pool = await get_pool(loop)

    connection = await pool.acquire()                                       
    cursor = await connection.cursor(aiomysql.DictCursor)
    sql = "INSERT INTO " + tableName + " " + columns + " VALUES " + values + ";"
    await cursor.execute(sql)
    await connection.commit()    
    await cursor.close()     
    pool.release(connection)    
    
    

async def post_handle(request):  
    postData = await request.text()
    await insertToSQL(json.loads(postData))
    return web.Response()
    
    
# Requirement: SQL Database/Table already created
def main():     
    resource.setrlimit(resource.RLIMIT_NOFILE, (65536, 65536))
    signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        #aiohttp server
        app = web.Application()
        cors = aiohttp_cors.setup(app, defaults= { "*": aiohttp_cors.ResourceOptions(allow_methods=["POST"],allow_credentials=True,expose_headers="*",allow_headers="*",)})

        theURL = cors.add(app.router.add_resource("/"))
        cors.add(theURL.add_route("POST", post_handle))
        
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(('', 8080))

        web.run_app(app, sock=serversocket)
    finally: 
        close_pool()

if __name__ == "__main__":
    main()
