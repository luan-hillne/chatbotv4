import requests
import pandas as pd
from config_app.config import get_config
config_app = get_config()

# URL của API

data_private = config_app['parameter']['data_inventory']
num_get_inventory = config_app['parameter']['num_get_inventory']
# df = pd.read_excel(data_private)

# Dữ liệu cần gửi trong yêu cầu POST
def get_inventory(msp,mt=None):
    print('============get_inventory============')
    url = "http://wms.congtrinhviettel.com.vn/wms-service/service/magentoSyncApiWs/getListRemainStockV2"
    if mt:
        payload = {
            "source": {
                "goodsCode": msp.upper(),
                "provinceCode": mt.upper()
            }
        }
    else:
        payload = {
            "source": {
                "goodsCode": msp.upper(),
                "provinceCode": mt
            }
        }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers,timeout=60)
    if response.status_code == 200:
        response_data = response.json()

        if len(response_data['data']) == 0:
            in_stock_out = find_stock(msp, mt)
            if len(in_stock_out) == 0:
                return "Hiện tại tôi không thể tra cứu thông tin hàng tồn kho của sản phẩm bạn đang mong muốn, xin vui lòng thử lại sau."

            return f"Anh/chị xin thông cảm! Hiện tại hàng tại {mt} đã hết. Các khu vực sau còn hàng Anh/chị hãy liên hệ các CNCT sau: \n" + '\n'.join(in_stock_out)
        
        if 'data' in response_data and response_data['data'] is not None:

            info_strings = []
            num = 0
            for item in response_data['data']:

                amount = item["amount"] if item["amount"] is not None else ""
                goods_name = item["goodsName"] if item["goodsName"] is not None else ""
                stock_name = item["stockName"] if item["stockName"] is not None else ""
                stock_code = item["stockCode"] if item["stockCode"] is not None else ""
                # In hoặc xử lý thông tin từng mục
                if stock_name != '' or stock_code !='':
                    if num <= 15:
                        info_string = (
                            f"  Tên Kho: {stock_name}\n"
                            f"  Mã kho: {stock_code}\n"
                            f"  SL: {int(amount)}\n"
                            "  ---------------------------"
                        )
                        info_strings.append(info_string)
                    num += 1
                # Kết hợp các chuỗi thành một chuỗi duy nhất
            final_string = "\n".join(info_strings)
            return final_string
    else:
        # In lỗi nếu có
        return "Hiện tại tôi không thể tra cứu thông tin hàng tồn kho của sản phẩm bạn đang mong muốn, xin vui lòng thử lại sau."

def find_stock(msp, mt):
    print('============in_stock============')
    df = pd.read_excel(data_private)
    fil_df = df[df["origin_CNCT"].str.lower() == mt.lower()]
    sorted_df = fil_df.sort_values(by=["distanceMeters"])
    stock = []
    # find 5 stock remain good
    for index, row in sorted_df.iterrows():
        destination_CNCT = row["destination_CNCT"]
        has_stock = in_stock(msp, destination_CNCT)
        outtext = ""
        if isinstance(has_stock, str):
            outtext = "Kho khu vực: " + destination_CNCT + "\n"
            outtext += has_stock + "\n"
            stock.append(outtext)
            if len(stock) >= 25:
                break
    return stock

def in_stock(msp, mt):
    # print('============in_stock============')
    url = "http://wms.congtrinhviettel.com.vn/wms-service/service/magentoSyncApiWs/getListRemainStockV2"

    if mt:
        payload = {
            "source": {
                "goodsCode": msp.upper(),
                "provinceCode": mt.upper()
            }
        }
    else:
        payload = {
            "source": {
                "goodsCode": msp.upper(),
                "provinceCode": mt
            }
        }
    # Headers nếu có (ở đây để trống nếu không yêu cầu)
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers,timeout=60)
    if response.status_code == 200:
        response_data = response.json()
        
        if len(response_data['data']) == 0:
            return 0
        if 'data' in response_data and response_data['data'] is not None:
            info_strings = []
            num = 0
            for i, item in enumerate(response_data['data']):
                # Xử lý từng mục trong danh sách
                amount = item["amount"] if item["amount"] is not None else ""
                goods_name = item["goodsName"] if item["goodsName"] is not None else ""
                stock_name = item["stockName"] if item["stockName"] is not None else ""
                stock_code = item["stockCode"] if item["stockCode"] is not None else ""
                # In hoặc xử lý thông tin từng mục
                if stock_name != '' or stock_code !='':
                    if num <= 5:
                        info_string = (
                            f"  {i+1}. Tên Kho: {stock_name}\n"
                            f"  Mã kho: {stock_code}\n"
                            f"  SL: {int(amount)}\n"
                            "   ------------------------------"
                        )
                        info_strings.append(info_string)
                    num += 1
                # Kết hợp các chuỗi thành một chuỗi duy nhất
            final_string = "\n".join(info_strings)
            return final_string
    else:
        # In lỗi nếu có
        return "Hiện tại tôi không thể tra cứu thông tin hàng tồn kho của sản phẩm bạn đang mong muốn, xin vui lòng thử lại sau."

def multi_get(ma, mt):
    product = ""
    masp = ma.strip().split(", ")
    for i, msp in enumerate(masp):
        outtext = f"- Với mã/tên sản phẩm {msp}: \n"
        get_msp = get_inventory(msp, mt)
        outtext+= get_msp
        product += outtext + "\n\n"
    return product
print(multi_get('điều hòa, máy giặt','HNI'))
