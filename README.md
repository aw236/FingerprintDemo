# Fingerprint Demo

This is an implementation of an asynchronous Python HTTP server that processes fingerprint data from www.somniolabs.com and uploads it to a Google mySQL database.

# Fingerprinting (index.html)

Fingerprint data is obtained from www.somniolabs.com's fingerprint2.js. This data is displayed to the console and copied to a HTTP request's data section in a JSON-formatted string. This request is then sent to a Google Compute Engine which is hosting the HTTP server.

# Asynchronous HTTP server (fp_server.py)

This HTTP server utilizes asyncio to perform asynchronous tasks. When it receives a HTTP POST request from www.somniolabs.com, it parses the request's fingerprint data and inserts it into a Google mySQL database. Afterwards, it sends a HTTP response to end communication with www.somniolabs.com.
