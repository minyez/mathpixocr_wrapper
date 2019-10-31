#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This scripts tries to get the resolved LaTeX code converted from image
by using MathPix OCR API, and copy the code to the system clipboard

Some codes are adapted from the official example:

    https://github.com/Mathpix/api-examples/blob/master/python/mathpix.py
    https://github.com/Mathpix/api-examples/blob/master/python/simple.py

Author : Min-Ye Zhang (minyez@github)
"""
import os
import base64
import json
import datetime
import sys
import subprocess as sp
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import requests

SERVICE = 'https://api.mathpix.com/v3/latex'
DIRNAME = os.path.dirname(os.path.realpath(__file__))
API_FILE = os.path.join(DIRNAME, '.mathpix_api.json')
HIST_FILE = os.path.join(DIRNAME, '.mathpix_hist.json')

def load_api_keys():
    """get the API id and key.

    Two ways are provided.
    
    1. Set the environment variables `app_key` and `app_id` according to your account
    2. Set those values in JSON format in .mathpix_api.json in the same REAL path as the script

    1 will be tried first, and 2 will be attempted then if 1 raises a KeyError.
    """
    api = {}
    api["app_id"] = os.environ.get("app_id", None)
    api["app_key"] = os.environ.get("app_key", None)
    if None in api.values():
        try:
            with open(API_FILE, 'r') as h:
                _api = json.load(h)
            api["app_id"] = _api.get("app_id", None)
            api["app_key"] = _api.get("app_key", None)
        except (FileNotFoundError, KeyError):
            pass
    if None in api.values():
        raise ValueError("API keys are not properly set.")
    return api


def month_usage(thres=900):
    """Get the rough monthly usage
    """
    today = datetime.date.today()
    if os.path.isfile(API_FILE):
        with open(API_FILE, 'r') as h:
            api = json.load(h)
    else:
        api = {}
    if "last_date" not in api:
        api["last_date"] = today.isoformat()
    if "month_usage" not in api:
        api["month_usage"] = 0
    last_date = datetime.date.fromisoformat(api["last_date"])
    diff = today - last_date
    # we reach a new month! Clean history
    if diff.days > 32:
        api["last_date"] = today.isoformat()
        api["month_usage"] = 0
        if os.path.isfile(HIST_FILE):
            os.remove(HIST_FILE)
    n = api["month_usage"]
    if n < thres:
        n += 1
        with open(API_FILE, 'w') as h:
            json.dump(api, h, indent=2)
    return n
    

def get_headers(**kwargs):
    """Get the headers
    """
    headers = {'Content-type': 'application/json'}
    try:
        for k in ["app_key", "app_id"]:
            if k in kwargs.keys():
                if kwargs[k] is None:
                    raise ValueError
    except ValueError:
        api = load_api_keys()
        kwargs.update(api)
    finally:
        headers.update(kwargs)
    return headers


def image_uri(filename):
    """Return the base64 encoding of an image with the given filename.
    """
    image_data = open(filename, "rb").read()
    return "data:image/jpg;base64," + base64.b64encode(image_data).decode()

def get_image_from_clipboard():
    """Dump the image from the clipboard

    In case that ImageGrab.grabclipboard is not supported in macOS,
    pbpaste can be used to get the image content in the clipboard (not implemented though)
    """
    from PIL import ImageGrab
    im = ImageGrab.grabclipboard()
    # print(os.path.isfile(im.filename))  # False
    fn = os.path.join(DIRNAME, ".temp_eq.png")
    if im is None:
        image = ''
    else:
        im.save(fn, "PNG")
        image = fn
    return image
        

def get_latex(args, headers, timeout=30):
    """Call the Mathpix service with the given arguments, headers, and timeout.
    """
    r = requests.post(SERVICE, data=json.dumps(args), headers=headers, timeout=timeout)
    return json.loads(r.text)


def add_to_history(new, hist=HIST_FILE):
    """save the new OCR json to history file hist
    """
    dt = datetime.datetime.now().isoformat(timespec="seconds")
    j = {}
    if os.path.isfile(hist):
        with open(hist, 'r') as h:
            j = json.load(h)
    j.update({dt: new})
    with open(hist, 'w') as h:
        json.dump(j, h, indent=2, sort_keys=True)


def send_text_to_clipboard(text, std_out=False):
    """Send the LaTeX code to the clipboard

    Set std_out to True to actually disable the copy and print the text to stdout
    You can use some function of OS, e.g. Automator action, to copy text to the clipboard
    """
    if std_out:
        print(text)
    else:
        p = sp.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=sp.PIPE)
        p.communicate(text.encode())


def main():
    """the main stream for calling the mathpix OCR API
    """
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("--app_key", type=str, default=None)
    parser.add_argument("--app_id", type=str, default=None)
    parser.add_argument("--format", type=str, default="latex_simplified", \
            choices=["latex_simplified", "latex_styled"], \
            help="LaTeX format to parsed to OCR API")
    parser.add_argument("--thres", type=int, default=900, help="threshold for API calls/month")
    parser.add_argument("-i", dest="image", type=str, default=None, \
            help="path to image file. Default None to use clipboard")
    parser.add_argument("-D", dest="debug", action="store_true", help="debug mode")
    parser.add_argument("-p", action="store_true", \
            help="directly print the output string (OCR results or error message) to stdout")
    args = parser.parse_args()
    headers = get_headers(**{"app_key": args.app_key, "app_id": args.app_id})
    if args.debug:
        print(headers)

    image = args.image
    # get image from the clipboard if manual image input is specified
    if image is None:
        image = get_image_from_clipboard()
    if not os.path.isfile(image):
        send_text_to_clipboard("image not found " + image, std_out=args.p)
        sys.exit(0)

    n = month_usage(thres=args.thres)
    if n > args.thres:
        send_text_to_clipboard(f"Large API calls ({n}) this month ", std_out=args.p)
        
    r = get_latex({'src': image_uri(image), 'formats': [args.format,]}, \
            headers=headers)
    if args.debug:
        print(r)
    if "error" in r:
        r = {args.format: f"Error: {r['error']}. f{n} API calls used"}
    else:
        add_to_history(r)
    send_text_to_clipboard(r[args.format], std_out=args.p)

    
if __name__ == "__main__":
    main()

