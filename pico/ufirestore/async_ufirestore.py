import ujson
import asyncio
from async_urequests import _requests
import aiohttp

class FirestoreException(Exception):
    def __init__(self, message, code=400):
        super().__init__()
        self.message = message
        self.code = code

    def __str__(self):
        return f"{self.code}: {self.message}"


class FIREBASE_GLOBAL_VAR:
    GLOBAL_URL_HOST = "https://firestore.googleapis.com"
    GLOBAL_URL_ADINFO = {
        "host": "https://firestore.googleapis.com", "port": 443}
    PROJECT_ID = None
    DATABASE_ID = "(default)"
    ACCESS_TOKEN = None
    SLIST = {}

class TimeoutError(Exception):
    pass

def construct_url(resource_path=None):
    path = "%s/v1/projects/%s/databases/%s/documents" % (
        FIREBASE_GLOBAL_VAR.GLOBAL_URL_HOST, FIREBASE_GLOBAL_VAR.PROJECT_ID, FIREBASE_GLOBAL_VAR.DATABASE_ID)

    if resource_path:
        path += "/"+resource_path

    return path


def to_url_params(params=dict()):
    return "?" + "&".join(
        [(str(k) + "=" + str(v)) for k, v in params.items() if v is not None])


async def send_request(path, method="GET", params=dict(), data=None, dump=True):
    headers = {}
    if FIREBASE_GLOBAL_VAR.ACCESS_TOKEN:
        headers["Authorization"] = "Bearer " + FIREBASE_GLOBAL_VAR.ACCESS_TOKEN

    try:
        print("Try here to post")
        print(method)
        if method == "POST":
            print(path)
            # response = await asyncio.wait_for(requests._requests(method, path, data=data, json=data, headers=headers), timeout=10)
            # response = await post(path, timeout=10, data=data, json=data)
#             response = await _requests("POST", path, data=data, json=data)
            print("POSTING")
            async with aiohttp.ClientSession(path) as session:
#             data = doc.process()
                async with session.post("", json=data) as resp:
                    #assert resp.status == 200
                    print(resp)
                    rpost = await resp.text()
                    print(f"POST: {rpost}")
                    response = rpost
        else:
            response = await asyncio.wait_for(requests._requests(method, path, headers=headers), timeout=10)
    except asyncio.TimeoutError as e:
        raise FirestoreException("Timeout", 1234)

    if dump == True:
        if response.status_code < 200 or response.status_code > 299:
            raise FirestoreException(response.reason, response.status_code)

        jsonResponse = response.json()
        if jsonResponse.get("error"):
            error = jsonResponse["error"]
            code = error["code"]
            message = error["message"]
            raise FirestoreException(message, code)
        return jsonResponse


class INTERNAL:

    async def patch(DOCUMENT_PATH, DOC, cb, update_mask=None):
        PATH = construct_url(DOCUMENT_PATH)
        LOCAL_PARAMS = to_url_params()
        if update_mask:
            for field in update_mask:
                LOCAL_PARAMS += "updateMask=" + field
        DATA = DOC.process()
        LOCAL_OUTPUT = await send_request(PATH, "POST", data=DATA)
        if cb:
            try:
                return cb(LOCAL_OUTPUT)
            except:
                raise OSError(
                    "Callback function could not be executed. Try the function without ufirestore.py callback.")
        return LOCAL_OUTPUT

    async def create(COLLECTION_PATH, DOC, cb, document_id=None):
        PATH = construct_url(COLLECTION_PATH)
        PARAMS = {"documentId": document_id}
        LOCAL_PARAMS = to_url_params(PARAMS)
        DATA = DOC.process()
        print("Send Request")
        LOCAL_OUTPUT = await send_request(PATH+LOCAL_PARAMS, "POST", PARAMS, DATA)
        if cb:
            try:
                return cb(LOCAL_OUTPUT)
            except:
                raise OSError(
                    "Callback function could not be executed. Try the function without ufirestore.py callback.")
        return LOCAL_OUTPUT

    async def get(DOCUMENT_PATH, cb, mask=None):
        PATH = construct_url(DOCUMENT_PATH)
        LOCAL_PARAMS = to_url_params()
        if mask:
            for field in mask:
                LOCAL_PARAMS += "mask.fieldPaths=" + field
        LOCAL_OUTPUT = await send_request(PATH+LOCAL_PARAMS, "GET")
        if cb:
            try:
                return cb(LOCAL_OUTPUT)
            except:
                raise OSError(
                    "Callback function could not be executed. Try the function without ufirestore.py callback.")
        return LOCAL_OUTPUT

    async def getfile(DOCUMENT_PATH, FILENAME, cb, mask=None):
        PATH = construct_url(DOCUMENT_PATH)
        LOCAL_PARAMS = to_url_params()
        if mask:
            for field in mask:
                LOCAL_PARAMS += "mask.fieldPaths=" + field
        LOCAL_OUTPUT = await send_request(PATH+LOCAL_PARAMS, "get")

        with open(FILENAME, "wb") as LOCAL_FILE:
            ujson.dump(LOCAL_OUTPUT, LOCAL_FILE)

        if cb:
            try:
                return cb(FILENAME)
            except:
                raise OSError(
                    "Callback function could not be executed. Try the function without ufirestore.py callback.")
        return FILENAME

    async def delete(RESOURCE_PATH, cb):
        PATH = construct_url(RESOURCE_PATH)
        await send_request(PATH, "DELETE")
        if cb:
            try:
                return cb(True)
            except:
                raise OSError(
                    "Callback function could not be executed. Try the function without ufirestore.py callback.")
        return True

    async def list(COLLECTION_PATH, cb, page_size=None, page_token=None, order_by=None, mask=None, show_missing=None):
        PATH = construct_url(COLLECTION_PATH)
        LOCAL_PARAMS = to_url_params({
            "pageSize": page_size,
            "pageToken": page_token,
            "orderBy": order_by,
            "showMissing": show_missing
        })
        if mask:
            for field in mask:
                LOCAL_PARAMS += "mask.fieldPaths=" + field
        LOCAL_OUTPUT = await send_request(PATH+LOCAL_PARAMS, "get")
        if cb:
            try:
                return cb(LOCAL_OUTPUT.get("documents"),
                          LOCAL_OUTPUT.get("nextPageToken"))
            except:
                raise OSError(
                    "Callback function could not be executed. Try the function without ufirestore.py callback.")
        return (LOCAL_OUTPUT.get("documents"), LOCAL_OUTPUT.get("nextPageToken"))

    async def list_collection_ids(DOCUMENT_PATH, cb, page_size=None, page_token=None):
        PATH = construct_url(DOCUMENT_PATH)+":listCollectionIds"
        DATA = {
            "pageSize": page_size,
            "pageToken": page_token
        }
        LOCAL_OUTPUT = await send_request(PATH, "POST", data=DATA)
        if cb:
            try:
                return cb(LOCAL_OUTPUT.get("collectionIds"),
                          LOCAL_OUTPUT.get("nextPageToken"))
            except:
                raise OSError(
                    "Callback function could not be executed. Try the function without ufirestore.py callback.")
        return (LOCAL_OUTPUT.get("collectionIds"),
                LOCAL_OUTPUT.get("nextPageToken"))

    async def run_query(DOCUMENT_PATH, query, cb):
        PATH = construct_url(DOCUMENT_PATH)+":runQuery"
        DATA = {
            "structuredQuery": query.data
        }
        LOCAL_OUTPUT = await send_request(PATH, "POST", data=DATA)
        if cb:
            try:
                return cb(LOCAL_OUTPUT.get("document"))
            except:
                raise OSError(
                    "Callback function could not be executed. Try the function without ufirestore.py callback.")
        return LOCAL_OUTPUT


def set_project_id(id):
    FIREBASE_GLOBAL_VAR.PROJECT_ID = id


def set_access_token(token):
    FIREBASE_GLOBAL_VAR.ACCESS_TOKEN = token


def set_database_id(id="(default)"):
    FIREBASE_GLOBAL_VAR.DATABASE_ID = id


async def patch(PATH, DOC, update_mask=None, bg=True, cb=None):
    if bg:
        asyncio.create_task(
            INTERNAL.patch(PATH, DOC, cb, update_mask))
    else:
        return await INTERNAL.patch(PATH, DOC, cb, update_mask)


async def create(PATH, DOC, document_id=None, bg=True, cb=None):
    if bg:
        asyncio.create_task(
            INTERNAL.create(PATH, DOC, cb, document_id))
    else:
        return await INTERNAL.create(PATH, DOC, cb, document_id)


async def get(PATH, mask=None, bg=False, cb=None):
    if bg:
        asyncio.create_task(
            INTERNAL.get(PATH, cb, mask))
    else:
        return await INTERNAL.get(PATH, cb, mask)


async def getfile(PATH, FILENAME, mask=None, bg=False, cb=None):
    if bg:
        asyncio.create_task(
            INTERNAL.getfile(PATH, FILENAME, cb, mask))
    else:
        return await INTERNAL.getfile(PATH, FILENAME, cb, mask)


async def delete(PATH, bg=True, cb=None):
    if bg:
        asyncio.create_task(INTERNAL.delete(PATH, cb))
    else:
        return await INTERNAL.delete(PATH, cb)


async def list(PATH, page_size=None, page_token=None, order_by=None, mask=None, show_missing=None, bg=True, cb=None):
    if bg:
        asyncio.create_task(
            INTERNAL.list(PATH, cb, page_size, page_token, order_by, mask, show_missing))
    else:
        return await INTERNAL.list(PATH, cb, page_size,
                                    page_token, order_by, mask, show_missing)


async def list_collection_ids(PATH, page_size=None, page_token=None, bg=True, cb=None):
    if bg:
        asyncio.create_task(
            INTERNAL.list_collection_ids(PATH, cb, page_size, page_token))
    else:
        return await INTERNAL.list_collection_ids(PATH, cb, page_size, page_token)


async def run_query(PATH, query, bg=True, cb=None):
    if bg:
        asyncio.create_task(
            INTERNAL.run_query(PATH, query, cb))
    else:
        return await INTERNAL.run_query(PATH, query, cb)
