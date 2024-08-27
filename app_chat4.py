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
    uvicorn.run(app, host="0.0.0.0", port=config_app['server']['port'][3])