# SuperClean Ecommerce platform

A fullstack ecommerce web application with JavaScript frontend, interfacing with flask backend and data stored on an Oracle SQL database. 

<img src="./static/images/screenshot.PNG" height="400px"></img>

### Setup instructions:
1. Change directory into folder with main.py
2. Install dependencies on python3 with
```
pip install -r requirements.txt
```
3. Wipe and initialize database (**WARNING: RUNNING database.py WILL WIPE THE EXISTING STORED DATABASE**)
```
python database.py
```

Ensure database keys are set in:
```
HOST_NAME = "/"
PORT_NUMBER = "/"
SERVICE_NAME = "/"
USERNAME = "/"
PASSWORD = "/"
```

### Running the server: 
This is for running the development server.
1. On Anaconda Prompt, run
```
python main.py
```
2. Go to http://127.0.0.1:5000/

### Deployment
This is for running the production server. ngrok is used here for reference, though you may use other services if preferred.
1. Run flask server deployment script
```
python serve.py
```
2. Run ngrok
```
ngrok http 8000
```

### Functional requirements:

<img src="./static/images/fun_req1.png" height="400px"></img>
<img src="./static/images/fun_req2.png" height="400px"></img>

