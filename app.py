from distutils.command.build import build
import os
import time
import threading
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, Response, stream_with_context

projectpath = "" # put your project file location (example.sln) 
vcvarsall = "C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Community\\VC\\Auxiliary\\Build\\vcvarsall.bat"
buildconfig = "Release" # Release or Debug
Project_File_output = "" # put your project file output location (\x64\Release\example.exe)


building = False # status

domain = "https://example.com" # your host url

app = Flask(__name__)

# for test
@app.route('/', methods=['GET', 'POST'])
def hello():
    return "Hello!" 

# main page
@app.route('/Main', methods=['GET', 'POST'])
def Main():
    global building
    if request.method == 'POST':
        subject=request.form.get('subject')

        if subject == "Build":

            if building:

                # this function is for bypass cloudflare timeout
                def Stream():
                    global building
                    if building :
                        yield "Server is busy"
                    while building:
                        time.sleep(1)
                        yield "."
                    yield "<br>"
                    yield f"<meta http-equiv=\"refresh\" content=\"0;url={domain}/Main\" />"
                return Response(stream_with_context(Stream()))
            
            # if server is free, then redirect to build 
            return redirect(url_for('Build', number = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr).replace(":", "")))
        
        elif subject == "Download":
            return redirect(url_for(f'Download', number = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr).replace(":", "")))

    return render_template('Main.html')

# build page
# front end
@app.route('/Build/<number>', methods=['GET'])
def Build(number):
    global building
    nowNum = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr).replace(":", "")

    # check IP
    if number != nowNum:
        return "IP Mismatch. Fuck off :)"
    
    # if this ip is already build, then redirect to download
    if os.path.exists(f".\\data\\{number}.exe"):
        return redirect(url_for(f'Download', number = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr).replace(":", "")))

    if building == False:

        # this function is for bypass cloudflare timeout
        def Stream():
            global building
            yield "Please Wait..."
            
            threading.Thread(target=bulidMain, args=(number,)).start() # open thread for build
            time.sleep(3)
            while building:
                time.sleep(1)
                yield "."
            
            yield "<br>"
            yield "Done!"
            yield "<br>"
            yield "Redirecting..."
            time.sleep(5)
            yield f"<meta http-equiv=\"refresh\" content=\"0;url={domain}/Download/{number}\" />"
        return Response(stream_with_context(Stream()))
    else:
        return "hmm...:)"

# build thread
# backend
def bulidMain(number):
    global building
    building = True

    Project_File_save = f".\\data\\{number}.exe"
    os.system(f'cmd /c ""{vcvarsall}" x64 && msbuild "{projectpath}" -t:rebuild /p:Configuration={buildconfig}"')
    time.sleep(1)

    os.system(f'copy {Project_File_output} {Project_File_save} /y')

    building = False

# download page
@app.route('/Download/<number>', methods=['GET', 'POST'])
def Download(number):
    nowNum = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr).replace(":", "")
    if request.method == 'GET':

        # check ip
        if number != nowNum:
            return "IP Mismatch. Fuck off :)"
        
        # find file
        try:
            filenameTemp = f"{number}.exe"
            return send_from_directory('data', filenameTemp, as_attachment=True)
        except:
            return "File not found :("
        
    return ""