import psutil
import subprocess
import json
import time
import pandas as pd
from datetime import datetime
from jinja2 import Template
import plotly.express as px

# 定数設定
COLLECTION_INTERVAL = 1  # データ収集間隔（秒）
METRICS_FILE = "metrics.json"
#LOGS_FILE = "logs.json"
NETWORK_FILE = "network.json"
MERGED_FILE = "merged_data.csv"

# データ収集関数
def collect_metrics():
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=COLLECTION_INTERVAL),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_io": psutil.disk_io_counters()._asdict(),
    }

# def collect_logs():
#     process = subprocess.Popen(["journalctl", "-f"], stdout=subprocess.PIPE, text=True)
#     # Popen： Python スクリプトから外部プログラム（コマンドやスクリプト）を実行できる。Python プログラムの中から他のプログラムを呼び出すことが可能！
#     # 非同期プロセスである
#     for line in process.stdout:
#         yield {"timestamp": datetime.now().isoformat(), "log": line.strip()}
#     # yield は、関数が値を返す方法の一つで、ここではログの情報を生成


# ネットワークの統計情報を取得
def collect_network():
    try:
        net_io = psutil.net_io_counters()
        network_info = {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv
        }
        return {
            "timestamp": datetime.now().isoformat(),
            "network": network_info
        }
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "network": str(e)
        }
        # 上記のように{}を使用することで、返り値としてdictionaryを指定することが可能！

# データ収集ループ
def data_collection_loop():
    with open(METRICS_FILE, "a") as metrics_file, \
         open(NETWORK_FILE, "a") as network_file:
        #logs_gen = collect_logs()
        while True:
            # メトリクス収集
            metrics = collect_metrics()
            metrics_file.write(json.dumps(metrics) + "\n")
            
            # ログ収集
            #try:
                #log = next(logs_gen)
                #logs_file.write(json.dumps(log) + "\n")
            #except StopIteration:
            #    pass
            
            # ネットワークデータ収集
            network = collect_network()
            network_file.write(json.dumps(network) + "\n")

# データ統合
def merge_data():
    # データ読み込み
    metrics = pd.read_json(METRICS_FILE, lines=True)
    #logs = pd.read_json(LOGS_FILE, lines=True)
    network = pd.read_json(NETWORK_FILE, lines=True)

    # タイムスタンプの整備
    metrics["timestamp"] = pd.to_datetime(metrics["timestamp"])
    #logs["timestamp"] = pd.to_datetime(logs["timestamp"])
    network["timestamp"] = pd.to_datetime(network["timestamp"])

    # データ統合
    #merged = pd.merge_asof(metrics.sort_values("timestamp"), logs.sort_values("timestamp"), on="timestamp")
    merged = pd.merge_asof(merged, network.sort_values("timestamp"), on="timestamp")

    # CSV保存
    merged.to_csv(MERGED_FILE, index=False)

# 可視化
def visualize_data():
    df = pd.read_csv(MERGED_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # CPU使用率とメモリ使用率の可視化
    fig = px.line(df, x="timestamp", y="cpu_percent", title="CPU Usage and Log Events")
    fig.add_scatter(x=df["timestamp"], y=df["memory_percent"], mode="lines", name="Memory Usage")
    fig.show()

    # ネットワークトラフィックの可視化
    fig = px.bar(df, x="timestamp", y="network", title="Network Traffic")
    fig.show()

# レポート生成
def generate_report():
    df = pd.read_csv(MERGED_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # 簡易異常検出
    anomalies = df[(df["cpu_percent"] > 80) | (df["memory_percent"] > 90)]

    # レポートテンプレート
    template = Template("""
    <html>
    <head><title>Performance Report</title></head>
    <body>
        <h1>Performance Analysis Report</h1>
        <h2>Anomalies Detected</h2>
        <ul>
        {% for _, row in anomalies.iterrows() %}
            <li>{{ row['timestamp'] }}: CPU {{ row['cpu_percent'] }}%, Memory {{ row['memory_percent'] }}%</li>
        {% endfor %}
        </ul>
    </body>
    </html>
    """)

    # レポート生成
    with open("report.html", "w") as f:
        f.write(template.render(anomalies=anomalies))

# メイン関数
if __name__ == "__main__":
    # データ収集をバックグラウンドで実行
    try:
        print("Starting data collection...")
        data_collection_loop()
    except KeyboardInterrupt:
        print("Stopping data collection...")

    # データ統合と可視化、レポート生成
    print("Merging data...")
    merge_data()
    print("Visualizing data...")
    visualize_data()
    print("Generating report...")
    generate_report()
