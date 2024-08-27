# import uvicorn
# from fastapi import FastAPI, File, UploadFile, Form
# from fastapi.responses import JSONResponse
# import threading
# import datetime
# from config_app.config import get_config
# from main_run import handle_request
# from logs.log_file import Logger_Days
# import time

# config_app = get_config()
# app = FastAPI()
# numberrequest = 0

# MAX_THREADS = 10
# active_threads = []
# results = {}
# results_lock = threading.Lock()

# class RequestHandlerThread(threading.Thread):
#     def __init__(self, *args, **kwargs):
#         threading.Thread.__init__(self)
#         self.args = args
#         self.kwargs = kwargs
#         self.result = None
#         self.id_request = kwargs['IdRequest']
#         self.event = threading.Event()

#     def run(self):
#         self.result = handle_request(*self.args, **self.kwargs)
#         with results_lock:
#             results[self.id_request] = self.result
#         self.event.set()  # Signal that the result is ready

# @app.post('/llm')
# async def post(
#     InputText: str = Form(None),
#     IdRequest: str = Form(...),
#     NameBot: str = Form(...),
#     User: str = Form(...),
#     GoodsCode: str = Form(None),
#     ProvinceCode: str = Form(None),
#     ObjectSearch: str = Form(None),
#     PriceSearch: str = Form(None),
#     DescribeSearch: str = Form(None),
#     Image: UploadFile = File(None),
#     Voice: UploadFile = File(None)
# ):
#     global numberrequest, active_threads, results

#     if len(active_threads) >= MAX_THREADS:
#         return {"error": "Server is busy. Please try again later."}

#     numberrequest += 1

#     thread = RequestHandlerThread(
#         InputText=InputText,
#         IdRequest=IdRequest,
#         NameBot=NameBot,
#         User=User,
#         GoodsCode=GoodsCode,
#         ProvinceCode=ProvinceCode,
#         ObjectSearch=ObjectSearch,
#         PriceSearch=PriceSearch,
#         DescribeSearch=DescribeSearch,
#         Image=Image,
#         Voice=Voice
#     )
#     thread.start()
#     active_threads.append(thread)

#     # Clean up finished threads
#     active_threads = [t for t in active_threads if t.is_alive()]

#     # Polling for the result
#     while not thread.event.is_set():
#         time.sleep(0.1)  # Polling interval

#     # Retrieve the result once the thread has completed
#     with results_lock:
#         result = results.pop(IdRequest, {"error": "Result not found"})
    
#     return JSONResponse(content=result)

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=9999)


import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from config_app.config import get_config
from main_run import handle_request
import datetime
from logs.log_file import Logger_Days
from concurrent.futures import ThreadPoolExecutor
import asyncio

config_app = get_config()

app = FastAPI()
numberrequest = 0

# Tạo ThreadPoolExecutor với số lượng worker tối đa
max_workers = config_app['server'].get('max_workers', None)  # Lấy từ config hoặc để mặc định
executor = ThreadPoolExecutor(max_workers=max_workers)

@app.post('/llm')
async def post(
    InputText: str = Form(None),
    IdRequest: str = Form(...),
    NameBot: str = Form(...),
    User: str = Form(...),
    GoodsCode: str = Form(None),
    ProvinceCode: str = Form(None),
    ObjectSearch: str = Form(None),
    PriceSearch: str = Form(None),
    DescribeSearch: str = Form(None),
    Image: UploadFile = File(None),
    Voice: UploadFile = File(None)
):
    global numberrequest
    numberrequest += 1

    # Thực thi handle_request trong thread pool
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        executor,
        handle_request,
        InputText,
        IdRequest,
        NameBot,
        User,
        GoodsCode,
        ProvinceCode,
        ObjectSearch,
        PriceSearch,
        DescribeSearch,
        Image,
        Voice
    )
    return results

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9999)