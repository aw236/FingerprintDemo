# Imports for Google SQL client library
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

# Imports for Asynchronous Python
from aiohttp import web
import aiohttp_cors
import asyncio
import aiomysql
import pymysql 

# Imports for Python libaries
import sys
import time
import os, os.path
import json
import csv
import io
import signal
import socket
import resource
import hashlib

# Globals for Google SQL
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



# Convert JSON object to mySQL query string
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

    

# Set up pool of connections to Google SQL
# Hard coded for up to 1000 concurrent SQL queries   
# If beginning of server set up, connect to SQL else returns M_POOL
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


    
# Closes Google SQL connections
# Only called during server shutdown   
def close_pool():
    global M_POOL
    M_POOL.terminate()
    M_POOL.wait_closed()
 

 
# Generate mySQL query string and send to mySQL database
async def insertToSQL(dataParam): 
    keyList = []
    valueList = []
    concatString = ""
    curHash = ""
    curDate = ""
    
    # Iterate through JSON object and convert to string for SQL query
    for aPair in dataParam:
        keyList.append("`" + aPair['key'] + "`")
        valueList.append(str(aPair['value']).replace("'", r"\'"))
        concatString = concatString + str(aPair['value']).replace("'", r"\'") 
        
        if aPair['key'] == 'date':
            curDate = aPair['value']
        
        if aPair['key'] == 'concatHash':
            curHash = aPair['value']
        
    # Get column and value names as string for mySQL query
    columns = convertListToString(keyList, False)
    values = convertListToString(valueList, True)

    # Get a connection thread("cursor") to mySQL
    loop = asyncio.get_event_loop()
    pool = await get_pool(loop)
    connection = await pool.acquire()                                       
    cursor = await connection.cursor(aiomysql.DictCursor)
    
    # Concatanate mySQL query string and execute query
    # If hash is in the mySQL table, update else insert into table
    sql = "UPDATE " + tableName + " SET date='" + curDate + "' WHERE concatHash='" + curHash + "';"
    await cursor.execute(sql)
    await connection.commit()       
    
    if cursor.rowcount == 0:
        sql = "INSERT INTO " + tableName + " " + columns + " VALUES " + values + ";"
        await cursor.execute(sql)
        await connection.commit()   
    
    # Release thread 
    await cursor.close()     
    pool.release(connection)    
    
    
    
# Handler for HTTP POST request
# Converts object to text then calls insertToSQL then returns HTTP response
async def post_handle(request):  
    postData = await request.text()
    await insertToSQL(json.loads(postData))
    return web.Response()
    
    
    
def main():     
    # Increase maximum number of tcp connections to server to 65536
    resource.setrlimit(resource.RLIMIT_NOFILE, (65536, 65536))
    signal.signal(signal.SIGINT, signal.default_int_handler)
    
    try:
        # aiohttp server initiation
        app = web.Application()
        
        # Set up cors to allow cross origin domain usage
        # Allow a HTTP request from our webpage's server to our fingerprinting server because they have different IPs
        cors = aiohttp_cors.setup(app, defaults= { "*": aiohttp_cors.ResourceOptions(allow_methods=["POST"],allow_credentials=True,expose_headers="*",allow_headers="*",)})

        # Only allow HTTP POST requests
        theURL = cors.add(app.router.add_resource("/"))
        cors.add(theURL.add_route("POST", post_handle))
        
        # Set up TCP socket listener to port 8080
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(('', 8080))

        # Run aiohttp server
        web.run_app(app, sock=serversocket)
    finally: 
        # Shut down process
        close_pool()

if __name__ == "__main__":
    main()
