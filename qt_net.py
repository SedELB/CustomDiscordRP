# qt_net.py — async networking via Qt (no Python threads, no requests).
# Doing network on a raw threading.Thread crashes on some setups (security/
# overlay DLLs injected into socket calls), so all HTTP goes through Qt's event
# loop instead. Callbacks always fire on the main thread; PIL stays main-thread.
from urllib.parse import quote
from PyQt6.QtCore import QObject, QUrl
from PyQt6.QtNetwork import (
    QNetworkAccessManager, QNetworkRequest, QNetworkReply, QHttpMultiPart, QHttpPart,
)

_UA = (
    b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    b"(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
_SEARCH_URL = "https://api.brandfetch.io/v2/search/"
_CATBOX_URL = "https://catbox.moe/user/api.php"


class Net(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._nam = QNetworkAccessManager(self)

    def get(self, url, callback):
        # callback(bytes_or_None)
        req = QNetworkRequest(QUrl(url))
        req.setRawHeader(b"User-Agent", _UA)
        req.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                         QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
        reply = self._nam.get(req)

        def done():
            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = bytes(reply.readAll())
            else:
                data = None
            reply.deleteLater()
            callback(data)

        reply.finished.connect(done)

    def search_brandfetch(self, query, callback):
        # callback(json_bytes_or_None)
        self.get(_SEARCH_URL + quote(query), callback)

    def upload_catbox(self, png_bytes, callback):
        # callback(url_or_None)
        multipart = QHttpMultiPart(QHttpMultiPart.ContentType.FormDataType)

        reqtype = QHttpPart()
        reqtype.setHeader(QNetworkRequest.KnownHeaders.ContentDispositionHeader,
                          'form-data; name="reqtype"')
        reqtype.setBody(b"fileupload")
        multipart.append(reqtype)

        filepart = QHttpPart()
        filepart.setHeader(QNetworkRequest.KnownHeaders.ContentDispositionHeader,
                           'form-data; name="fileToUpload"; filename="image.png"')
        filepart.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "image/png")
        filepart.setBody(png_bytes)
        multipart.append(filepart)

        req = QNetworkRequest(QUrl(_CATBOX_URL))
        req.setRawHeader(b"User-Agent", _UA)
        reply = self._nam.post(req, multipart)
        multipart.setParent(reply)  # keep multipart alive until the reply finishes

        def done():
            if reply.error() == QNetworkReply.NetworkError.NoError:
                text = bytes(reply.readAll()).decode("utf-8", "replace").strip()
            else:
                text = ""
            reply.deleteLater()
            callback(text if text.startswith("https://") else None)

        reply.finished.connect(done)
