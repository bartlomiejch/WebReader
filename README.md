Program that monitors web sites and reports their availability. This tool is intended as a
monitoring tool for web site administrators for detecting problems on their sites.

Project title:

WebReader

Getting started:

WebReader is written in Python 3.
To run the script pass configuration file as first argument, and port number as second argument.

Example: $ python3 WebReader.py main.conf 8000

Sections in configuration file should look like this:

[Section]
url=https://www.onet.pl   --   url address
content=some text   --   content requirement
period=3    --    interval in seconds to make HTTP request

To run server interface type 127.0.0.1:<port number> in the address bar in the browser.
Example: 127.0.0.1:8000 - port number must be the same as declared in calling the WebReader.py script, as above.

Build with:

Redis - in-memory data structure store.
validators - Python Data Validation

To install redis type:

$ sudo pip3 install redis
