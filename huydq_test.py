import requests

# Định nghĩa URL của API
url = "http://localhost:9999/llm"

# Tạo payload cho các trường form
payload = {
    "InputText": "",
    "IdRequest": "12345",
    "NameBot": "2",
    "User": "2",
    "GoodsCode": "",
    "ProvinceCode": "",
    "ObjectSearch": "",
    "PriceSearch": "",
    "DescribeSearch": ""
}

# Đường dẫn tới file ảnh bạn muốn gửi
image_path = "/home/aiai01/Production/Rasa_LLM_Elasticsearch_update_v3/data/images/428950/2024-07-15/524d80be-0c7e-4e7c-9122-9d02603c7f4a4492723282515374609.jpg"

# Tạo file object cho ảnh
files = {
    "Image": open(image_path, "rb")
}

response = requests.post(url, data=payload, files=files)

# Kiểm tra kết quả phản hồi
if response.status_code == 200:
    print("Response Data:", response.json())
else:
    print(f"Error {response.status_code}: {response.text}")