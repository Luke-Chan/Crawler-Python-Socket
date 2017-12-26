# Author: Luke-Chan
# E-mail: luke-chan@qq.com
import socket
import threading
import os
import re

# create directories with the same structure as the URL.
def create_folder(url):
    try:
        url = url.replace('http://','').replace('https://','')
        url = url.strip('/')
        urlcontent = url.split('/')
        
        folder = "Download"
        for item in urlcontent:
            folder = folder + "\\" + item
        folder = folder.rstrip("\\")
        isExists = os.path.exists(folder)
        if not isExists:
            os.makedirs(folder)
            print('\nPath Created: "' + folder + '"\n')
    except Exception as e:
        print("MultiThread Crash: Folder Already Exist\n")

# http request: get html content of the page
def http_get_html(url):
    try:
        url = url.replace('http://','').replace('https://','')
        urlcontent = url.split('/')

        # get the host adress and current page address from url
        httphost = urlcontent[0] #get the host address
        httpget = ""
        del urlcontent[0]
        for item in urlcontent:
            httpget = httpget + "/" + item #get the current folder
        if not httpget.endswith("/"):
            httpget = httpget + "/" #add a "/" at the end of url

        # *** Key Point of socket's http request ***
        # Generating a http header for http request
        http_header = "GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n" % (httpget, httphost)

        # send the http request
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((httphost, 80))
        s.send(http_header.encode())

        # get the html content
        data = ''
        while True:
            recv=s.recv(1024)
            if recv:
                data += recv.decode()
            else:
                s.close()
                break

        header, html = data.split('\r\n\r\n', 1)

        if ("404 Not Found") not in str(header):
            return html
        else:
            print('Page 404 Not Found: "' + url + '"')
            return ""

    except Exception as e:
        print(e)

# http request: Download an image by URL
# image will be saved to path if certain path required
# URL must be specific, for example: "www.baidu.com/baidu.jpg"
def http_get_imgs(url, path=""):
    url = url.replace('http://','').replace('https://','')
    urlcontent = url.split('/')
    
    # get the image path at first, then it will be used to create folder
    imgname = urlcontent.pop()
    imgpath = ""
    for item in urlcontent:
        imgpath = imgpath.rstrip("/") + "/" + item.lstrip("/")
    urlcontent.append(imgname)

    if (path == ""):
        path = "Download/" + url
    else:
        # Triggered when downloading a image from absolute url
        # and the image will be saved to the page url folder
        path = path.replace('http://','').replace('https://','')
        imgpath = path.strip("/") + "/"
        path = "Download/" + imgpath + imgname.strip("/")
    
    isExists = os.path.exists(path)

    if not isExists: 
        httphost = urlcontent[0] #get the host address
        httpget = ""
        del urlcontent[0]
        for item in urlcontent:
            httpget = httpget + "/" + item # address for http get request
        if httpget.endswith("/"):
            httpget = httpget.rstrip('/') # remove "/" at the end of url

        # *** Key Point of socket's http request ***
        # Generating a http header for http request
        http_header = "GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n" % (httpget, httphost)

        try:
            # Create the folder for this image
            create_folder(imgpath)
            
            # send the http request
            s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((httphost, 80))
            s.send(http_header.encode())

            # receive the image and save
            data = b''
            while True:
                recv=s.recv(1024)
                if recv:
                    data += recv
                else:
                    s.close()
                    break

            header, img = data.split(b'\r\n\r\n', 1)

            if ("404 Not Found") not in str(header):
                f = open(path, "wb")
                f.write(img)
                f.close()
                print('Image Saved: "' + path + '"\n')
            else:
                print('Image 404 Not Found: "' + url + '"\n')
        except Exception as e:
            print(e)
    else:
        print('Image Exist: "' + path + '"\n')

# Get all the URL of images from html, return type is list
def html_img_url(html):
    content = html.replace(" ","").replace("'", '"')
    urls = re.findall('<imgsrc="(.*?)"', content)
    return urls

# Get all URLs from html, return type is list
def html_href_url(html):
    urls = html.replace(" ","").replace("'", '"')
    urls = re.findall('<ahref="(.*?)"', urls)
    return urls

# Download all images of a page
def DownloadPage(url):
    html = http_get_html(url)
    url_imgs = html_img_url(html)
    ref_list = html_href_url(html)
    for item in url_imgs:
        # if url is absolute path
        if item.startswith("/") or item.startswith("../") or item.startswith("http"):
            hosturl = url.replace('http://','').replace('https://','')
            hosturl = hosturl.split('/')[0] + "/"   #get the host address
            geturl = item.strip("/").lstrip("../")
            geturl = hosturl + geturl.replace('http://','').replace('https://','')
            http_get_imgs(geturl, path=url)
        else:
            geturl = url.rstrip("/") + "/" + item.lstrip("/")
            http_get_imgs(geturl)
    return ref_list

# Class For Multithreading processing
class DownLoadThread(threading.Thread):
    def __init__(self, url):
        threading.Thread.__init__(self)
        self.url = url
    def run(self):
        self.ref_list = DownloadPage(self.url)
    def join(self):
        threading.Thread.join(self)
        return self.ref_list
    # if not return the reference list here,
    # the program need two http requests for one page

# Image Crawler, the main function
def Crawler(url, depth):
    RestDepth = depth - 1
    # Download page by multithreading
    thread = DownLoadThread(url)
    thread.start()
    # Limit the running threads
    while True:
        if(len(threading.enumerate()) < 10):
            break
    # Crawl all the pages that referenced in current page
    if (RestDepth > 0):
        # get the return value of this thread, which is url list
        ref_list = thread.join() 
        for item in ref_list:
            # if the url is absolute path
            if item.startswith("/") or item.startswith("../") or item.startswith("http"):
                hosturl = url.replace('http://','').replace('https://','')
                hosturl = hosturl.split('/')[0] + "/"   #get the host address
                geturl = item.strip("/").lstrip("../") + "/"
                geturl = hosturl + geturl.replace('http://','').replace('https://','')
                Crawler(geturl, RestDepth)
            else:
                geturl = url.rstrip("/") + "/" + item.lstrip("/")
                Crawler(geturl, RestDepth)
    else:
        print("Crawler Traceback...\n\n")



########## Main Function ##########

# program start parameters
url = "csse.xjtlu.edu.cn/classes/CSE205/"
depth = 3

# Starting the crawler, downloading images
Crawler(url, depth)

# Program Finished, print a message in the end
while True:
    if (len(threading.enumerate()) <= 1):
        print('\nProgram Finished, all images saved in "Download\\..."')
        break

# Program Finish, Pause
stop = 0
while True: stop = 1







