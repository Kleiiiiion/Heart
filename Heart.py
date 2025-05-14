import asyncio
from bleak import BleakScanner
import aiohttp
import time

# 配置
TARGET_MAC = "" #MAC
BASE_URL = "" #URL http://url:port
SECRET = "" #SECRET
REQUEST_INTERVAL = 1  # N秒间隔
last_request_time = 0

def format_mac(address: str) -> str:
    return address.replace(':', '').replace('-', '').upper()

async def send_heart_rate(heart_rate: int):
    """ 异步发送心率数据到服务器 """
    global last_request_time
    
    current_time = time.time()
    if current_time - last_request_time < REQUEST_INTERVAL:
        return
    
    last_request_time = current_time
    
    endpoint = f"{BASE_URL}/device/set"
    
    display_value = "寄了" if heart_rate == 255 else str(heart_rate)
    
    params = {
        "secret": SECRET,
        "id": "heart",
        "show_name": "心率",
        "using": "true",
        "app_name": display_value
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, params=params) as response:
                if response.status == 200:
                    print(f"成功发送心率数据: {display_value}")
                else:
                    print(f"服务器错误: HTTP {response.status}")
    except Exception as e:
        print(f"网络请求失败: {str(e)}")

def handle_device(device, advertisement_data):
    global last_request_time
    
    current_time = time.time()
    if current_time - last_request_time < REQUEST_INTERVAL:
        return
    
    raw_mac = device.address
    current_mac = format_mac(raw_mac)
    target_mac = format_mac(TARGET_MAC)
    
    if current_mac != target_mac:
        return
    
    manufacturer_data = advertisement_data.manufacturer_data
    if 0x0157 not in manufacturer_data:
        return
    
    data = manufacturer_data[0x0157]
    if len(data) < 4:
        return
    
    heart_rate = data[3]
    display_value = "寄了" if heart_rate == 255 else heart_rate
    print(f"MAC：{raw_mac} | 心率: {display_value}")

    asyncio.create_task(send_heart_rate(heart_rate))

async def main():
    print(f"正在扫描设备: {TARGET_MAC}")
    
    scanner = BleakScanner(detection_callback=handle_device)
    await scanner.start()
    
    try:
        while True:
            await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        await scanner.stop()
        print("\n扫描已停止")

if __name__ == "__main__":
    asyncio.run(main())