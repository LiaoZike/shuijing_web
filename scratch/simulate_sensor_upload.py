#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
simulate_sensor_upload.py
模擬硬體感測器上傳水質讀值的腳本。
支援自動讀取 Django 資料庫中的感測器金鑰，或手動指定金鑰進行模擬。
"""

import os
import sys
import time
import random
import requests
import argparse

# 預設 POST 的網址
DEFAULT_URL = "http://127.0.0.1:8000/water/api/upload/"

def setup_django():
    """設定 Django 環境以存取資料庫中的感測器金鑰"""
    try:
        # 將專案根目錄加入 path
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(project_root)
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shuijing.settings")
        import django
        django.setup()
        return True
    except Exception as e:
        print(f"⚠️ 無法初始化 Django 環境 (可能未在專案目錄下執行或未安裝相依套件): {e}")
        print("💡 將切換為【獨立運行模式】，請使用 --tokens 參數手動指定金鑰。")
        return False

def get_active_sensors():
    """從 Django 資料庫撈取所有啟用的感測器資訊"""
    from water.models import PondSensor
    sensors = PondSensor.objects.filter(is_active=True).select_related('pond')
    sensor_list = []
    for s in sensors:
        sensor_list.append({
            "id": s.pk,
            "name": s.name,
            "pond_name": s.pond.name,
            "token": s.secret_token,
            "type": s.sensor_type
        })
    return sensor_list

def generate_base_reading(anomaly_rate):
    """產生一個池區的基礎水質讀值"""
    # 決定這次是否產生異常數據
    is_anomaly = random.random() < anomaly_rate

    if is_anomaly:
        anomaly_type = random.choice(["low_do", "high_ph", "high_temp", "high_chem"])
        print(f"🚨 [模擬觸發異常狀態: {anomaly_type}]")
        if anomaly_type == "low_do":
            return {
                "temperature": random.uniform(26.0, 29.0),
                "ph": random.uniform(7.5, 8.2),
                "dissolved_oxygen": random.uniform(2.5, 4.0),  # 偏低 (標準一般 > 4.5)
                "ammonia_nitrogen": random.uniform(0.01, 0.05),
                "nitrite": random.uniform(0.02, 0.08),
                "salinity": random.uniform(12.0, 16.0)
            }
        elif anomaly_type == "high_ph":
            return {
                "temperature": random.uniform(26.0, 29.0),
                "ph": random.uniform(8.9, 9.5),  # 偏高 (標準一般 7.5~8.5)
                "dissolved_oxygen": random.uniform(5.5, 7.5),
                "ammonia_nitrogen": random.uniform(0.01, 0.05),
                "nitrite": random.uniform(0.02, 0.08),
                "salinity": random.uniform(12.0, 16.0)
            }
        elif anomaly_type == "high_temp":
            return {
                "temperature": random.uniform(32.5, 35.0),  # 偏高 (標準一般 20~30)
                "ph": random.uniform(7.8, 8.4),
                "dissolved_oxygen": random.uniform(5.0, 7.0),
                "ammonia_nitrogen": random.uniform(0.01, 0.05),
                "nitrite": random.uniform(0.02, 0.08),
                "salinity": random.uniform(12.0, 16.0)
            }
        else:  # high_chem
            return {
                "temperature": random.uniform(26.0, 29.0),
                "ph": random.uniform(7.8, 8.4),
                "dissolved_oxygen": random.uniform(5.5, 7.5),
                "ammonia_nitrogen": random.uniform(0.25, 0.45),  # 偏高 (標準一般 < 0.2)
                "nitrite": random.uniform(0.22, 0.35),  # 偏高 (標準一般 < 0.2)
                "salinity": random.uniform(12.0, 16.0)
            }
    else:
        # 正常狀態
        return {
            "temperature": random.uniform(27.5, 29.5),
            "ph": random.uniform(7.8, 8.3),
            "dissolved_oxygen": random.uniform(5.8, 7.2),
            "ammonia_nitrogen": random.uniform(0.01, 0.04),
            "nitrite": random.uniform(0.02, 0.06),
            "salinity": random.uniform(13.0, 15.0)
        }

def run_simulator(url, interval, anomaly_rate, limit, tokens_arg):
    print("=" * 60)
    print("🚀 水井村魚池感測數據上傳模擬器啟動")
    print(f"🔗 目標網址: {url}")
    print(f"⏱️ 發送間隔: {interval} 秒")
    print(f"⚡ 異常機率: {anomaly_rate * 100:.1f}%")
    if limit > 0:
        print(f"🔢 限制次數: {limit} 次")
    print("=" * 60)

    # 取得感測器金鑰
    sensors = []
    if tokens_arg:
        # 手動指定 tokens
        for idx, token in enumerate(tokens_arg):
            sensors.append({
                "id": idx + 1,
                "name": f"手動感測器_{idx+1}",
                "pond_name": "手動池區",
                "token": token,
                "type": "multi"
            })
    else:
        # 自資料庫讀取
        django_ok = setup_django()
        if django_ok:
            sensors = get_active_sensors()
            if not sensors:
                print("❌ 資料庫中沒有任何啟用的感測器，請先在網頁後台建立感測器。")
                return
        else:
            print("❌ 未指定 tokens 且無法連線資料庫，程式結束。")
            return

    print(f"📋 載入感測器清單 ({len(sensors)} 個):")
    for s in sensors:
        print(f"   - [{s['pond_name']}] {s['name']} (金鑰: {s['token'][:8]}...)")
    print("-" * 60)

    count = 0
    try:
        while True:
            # 依魚池分群，讓同一個池區的感測器數值相近（不至於兩個相鄰感測器溫差十度）
            ponds_base = {}
            
            for s in sensors:
                pond_name = s['pond_name']
                if pond_name not in ponds_base:
                    # 為該池區產生一個基礎水質快照
                    ponds_base[pond_name] = generate_base_reading(anomaly_rate)
                
                base = ponds_base[pond_name]
                
                # 加上微小雜訊，模擬不同位置的差異
                payload = {
                    "secret_token": s['token'],
                    "temperature": round(base['temperature'] + random.uniform(-0.2, 0.2), 1),
                    "ph": round(base['ph'] + random.uniform(-0.05, 0.05), 2),
                    "dissolved_oxygen": round(base['dissolved_oxygen'] + random.uniform(-0.15, 0.15), 1),
                }

                # 根據感測器類型決定是否發送化學指標與鹽度
                if s['type'] in ['multi', 'chem']:
                    payload["ammonia_nitrogen"] = round(base['ammonia_nitrogen'] + random.uniform(-0.002, 0.002), 3)
                    payload["nitrite"] = round(base['nitrite'] + random.uniform(-0.002, 0.002), 3)
                
                if s['type'] in ['multi']:
                    payload["salinity"] = round(base['salinity'] + random.uniform(-0.1, 0.1), 1)

                # 發送 POST 請求
                try:
                    res = requests.post(url, json=payload, timeout=5)
                    if res.status_code == 200:
                        res_data = res.json()
                        print(f"✅ [{s['pond_name']} - {s['name']}] 上傳成功 -> ID: {res_data.get('reading_id')}, "
                              f"Temp: {payload['temperature']}°C, pH: {payload['ph']}, DO: {payload['dissolved_oxygen']}")
                    else:
                        print(f"❌ [{s['pond_name']} - {s['name']}] 上傳失敗 ({res.status_code}) -> {res.text}")
                except Exception as ex:
                    print(f"⚠️ [{s['pond_name']} - {s['name']}] 連線失敗 -> {ex}")

            count += 1
            if limit > 0 and count >= limit:
                print("-" * 60)
                print(f"已達到限制發送次數 {limit} 次，模擬程式安全退出。")
                break

            time.sleep(interval)
            print("-" * 60)

    except KeyboardInterrupt:
        print("\n👋 模擬程式被使用者手動中斷。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="水井村感測器數據上傳模擬腳本")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"接收上傳的 API 端點 URL (預設: {DEFAULT_URL})")
    parser.add_argument("--interval", type=float, default=10.0, help="發送數據的間隔秒數 (預設: 10.0 秒)")
    parser.add_argument("--anomaly", type=float, default=0.1, help="異常數據出現的機率 (0.0 到 1.0, 預設: 0.1)")
    parser.add_argument("--limit", type=int, default=0, help="限制發送次數，0 代表無限次 (預設: 0)")
    parser.add_argument("--tokens", nargs="+", help="手動指定的感測器 secret_token 列表（若指定將跳過資料庫讀取）")

    args = parser.parse_args()
    
    # 限制合理範圍
    anomaly_rate = max(0.0, min(1.0, args.anomaly))
    interval = max(1.0, args.interval)

    run_simulator(
        url=args.url,
        interval=interval,
        anomaly_rate=anomaly_rate,
        limit=args.limit,
        tokens_arg=args.tokens
    )
