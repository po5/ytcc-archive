# This function adapted from https://github.com/cdown/srt/blob/11089f1e021f2e074d04c33fc7ffc4b7b52e7045/srt.py, lines 69 and 189 (MIT License)
def timedelta_to_sbv_timestamp(timedelta_timestamp):
    r"""
    Convert a :py:class:`~datetime.timedelta` to an SRT timestamp.
    .. doctest::
        >>> import datetime
        >>> delta = datetime.timedelta(hours=1, minutes=23, seconds=4)
        >>> timedelta_to_sbv_timestamp(delta)
        '01:23:04,000'
    :param datetime.timedelta timedelta_timestamp: A datetime to convert to an
                                                   SBV timestamp
    :returns: The timestamp in SBV format
    :rtype: str
    """

    SECONDS_IN_HOUR = 3600
    SECONDS_IN_MINUTE = 60
    HOURS_IN_DAY = 24
    MICROSECONDS_IN_MILLISECOND = 1000

    hrs, secs_remainder = divmod(timedelta_timestamp.seconds, SECONDS_IN_HOUR)
    hrs += timedelta_timestamp.days * HOURS_IN_DAY
    mins, secs = divmod(secs_remainder, SECONDS_IN_MINUTE)
    msecs = timedelta_timestamp.microseconds // MICROSECONDS_IN_MILLISECOND
    return "%1d:%02d:%02d.%03d" % (hrs, mins, secs, msecs)


from datetime import timedelta

from json import dumps

from gc import collect

import requests

# https://docs.python.org/3/library/html.parser.html
from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.captions = []
        self.title = ""
        self.description = ""


    def check_attr(self, attrs, attr, value):
        for item in attrs:
            if item[0] == attr and item[1] == value:
                return True
        return False

    def get_attr(self, attrs, attr):
        for item in attrs:
            if item[0] == attr:
                return item[1]
        return False

    def handle_starttag(self, tag, attrs):
        if tag == "input" and self.check_attr(attrs, "class", "yt-uix-form-input-text event-time-field event-start-time") and not ' data-segment-id="" ' in self.get_starttag_text():
            self.captions.append({"startTime": int(self.get_attr(attrs, "data-start-ms")), "text": ""})
        elif tag == "input" and self.check_attr(attrs, "class", "yt-uix-form-input-text event-time-field event-end-time") and not ' data-segment-id="" ' in self.get_starttag_text():
            self.captions[len(self.captions)-1]["endTime"] = int(self.get_attr(attrs, "data-end-ms"))
        elif tag == "input" and self.check_attr(attrs, "id", "metadata-title"):
            self.title = self.get_attr(attrs, "value")

    def handle_data(self, data):
        if self.get_starttag_text() and self.get_starttag_text().startswith("<textarea "):
            if 'name="serve_text"' in self.get_starttag_text() and not 'data-segment-id=""' in self.get_starttag_text():
                self.captions[len(self.captions)-1]["text"] += data
            elif 'id="metadata-description"' in self.get_starttag_text():
                self.description += data

def subprrun(jobs, mysession):
    while not jobs.empty():
        collect() #cleanup memory
        langcode, vid = jobs.get()
        vid = vid.strip()
        print(langcode, vid)
        pparams = (
            ("v", vid),
            ("lang", langcode),
            ("action_mde_edit_form", 1),
            ("bl", "vmp"),
            ("ui", "hd"),
            ("tab", "captions"),
            ("o", "U")
        )

        page = mysession.get("https://www.youtube.com/timedtext_editor", params=pparams)

        assert not "accounts.google.com" in page.url, "Please supply authentication cookie information in config.json. See README.md for more information."

        inttext = page.text
        del page

        if 'id="reject-captions-button"' in inttext or 'id="reject-metadata-button"' in inttext: #quick way of checking if this page is worth parsing
            parser = MyHTMLParser()
            parser.feed(inttext)

            captiontext = False
            for item in parser.captions:
                if item["text"][:-9]:
                    captiontext = True

            if captiontext:
                myfs = open("out/"+vid+"/"+vid+"_"+langcode+".sbv", "w", encoding="utf-8")
                captions = parser.captions
                captions.pop(0) #get rid of the fake one
                while captions:
                    item = captions.pop(0)

                    myfs.write(timedelta_to_sbv_timestamp(timedelta(milliseconds=item["startTime"])) + "," + timedelta_to_sbv_timestamp(timedelta(milliseconds=item["endTime"])) + "\n" + item["text"][:-9] + "\n")
                    
                    del item
                    if captions:
                        myfs.write("\n")
                del captions
                myfs.close()
                del myfs

            del captiontext

            if parser.title or parser.description[:-16]:
                metadata = {}
                metadata["title"] = parser.title
                if metadata["title"] == False:
                    metadata["title"] = ""
                metadata["description"] = parser.description[:-16]
                open("out/"+vid+"/"+vid+"_"+langcode+".json", "w", encoding="utf-8").write(dumps(metadata))
                del metadata

        del inttext

        del langcode
        del vid
        del pparams

        jobs.task_done()

    return True

if __name__ == "__main__":
    from os import environ, mkdir
    from os.path import isfile
    from json import loads
    #HSID, SSID, SID cookies required
    if "HSID" in environ.keys() and "SSID" in environ.keys() and "SID" in environ.keys():
        cookies = {"HSID": environ["HSID"], "SSID": environ["SSID"], "SID": environ["SID"]}
    elif isfile("config.json"):
        cookies = loads(open("config.json").read())
    else:
        print("HSID, SSID, and SID cookies from youtube.com are required. Specify in config.json or as environment variables.")
        assert False
    if not (cookies["HSID"] and cookies["SSID"] and cookies["SID"]):
        print("HSID, SSID, and SID cookies from youtube.com are required. Specify in config.json or as environment variables.")
        assert False

    mysession = requests.session()
    mysession.headers.update({"cookie": "HSID="+cookies["HSID"]+"; SSID="+cookies["SSID"]+"; SID="+cookies["SID"], "Accept-Language": "en-US",})
    del cookies
    from sys import argv
    from queue import Queue
    from threading import Thread
    langs = ['ab', 'aa', 'af', 'sq', 'ase', 'am', 'ar', 'arc', 'hy', 'as', 'ay', 'az', 'bn', 'ba', 'eu', 'be', 'bh', 'bi', 'bs', 'br', 
    'bg', 'yue', 'yue-HK', 'ca', 'chr', 'zh-CN', 'zh-HK', 'zh-Hans', 'zh-SG', 'zh-TW', 'zh-Hant', 'cho', 'co', 'hr', 'cs', 'da', 'nl', 
    'nl-BE', 'nl-NL', 'dz', 'en', 'en-CA', 'en-IN', 'en-IE', 'en-GB', 'en-US', 'eo', 'et', 'fo', 'fj', 'fil', 'fi', 'fr', 'fr-BE', 
    'fr-CA', 'fr-FR', 'fr-CH', 'ff', 'gl', 'ka', 'de', 'de-AT', 'de-DE', 'de-CH', 'el', 'kl', 'gn', 'gu', 'ht', 'hak', 'hak-TW', 'ha', 
    'iw', 'hi', 'hi-Latn', 'ho', 'hu', 'is', 'ig', 'id', 'ia', 'ie', 'iu', 'ik', 'ga', 'it', 'ja', 'jv', 'kn', 'ks', 'kk', 'km', 'rw', 
    'tlh', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'ln', 'lt', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'mni', 'mi', 'mr', 'mas', 'nan', 
    'nan-TW', 'lus', 'mo', 'mn', 'my', 'na', 'nv', 'ne', 'no', 'oc', 'or', 'om', 'ps', 'fa', 'fa-AF', 'fa-IR', 'pl', 'pt', 'pt-BR', 
    'pt-PT', 'pa', 'qu', 'ro', 'rm', 'rn', 'ru', 'ru-Latn', 'sm', 'sg', 'sa', 'sc', 'gd', 'sr', 'sr-Cyrl', 'sr-Latn', 'sh', 'sdp', 'sn', 
    'scn', 'sd', 'si', 'sk', 'sl', 'so', 'st', 'es', 'es-419', 'es-MX', 'es-ES', 'es-US', 'su', 'sw', 'ss', 'sv', 'tl', 'tg', 'ta', 
    'tt', 'te', 'th', 'bo', 'ti', 'tpi', 'to', 'ts', 'tn', 'tr', 'tk', 'tw', 'uk', 'ur', 'uz', 'vi', 'vo', 'vor', 'cy', 'fy', 'wo', 
    'xh', 'yi', 'yo', 'zu']
    vidl = argv
    vidl.pop(0)

    try:
        mkdir("out")
    except:
        pass

    jobs = Queue()
    for video in vidl:
        try:
            mkdir("out/"+video.strip())
        except:
            pass
        for lang in langs:
            jobs.put((lang, video))

    subthreads = []

    for r in range(50):
        subrunthread = Thread(target=subprrun, args=(jobs,mysession))
        subrunthread.start()
        subthreads.append(subrunthread)
        del subrunthread

    for xa in subthreads:
        xa.join() #bug (occurred once: the script ended before the last thread finished)
        subthreads.remove(xa)
        del xa