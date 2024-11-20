許可したパスしか挙動を許可しないホワイトリスト型セキュリティプロダクト
不必要に肥大化した
登録したはずのライブラリがなくなってる！とか
意図しないパスが知らぬうちに追加されている！とか

使用しているライブラリを抽出列挙してそれらの関係性を可視化できるようなグラフ作成
なんか例えば怪しげなことやりそうな脅威を発見することに役立つかもしれない？
(将来的にはひもで結んで可視化できるような動的サイトの構築(なんかさわったらふよふよするやつ))

各試験を動かした際に、ソフトウェアがどんな反応するかを受信して返り値として具体的な値を取得する関数を複数作成し、
各項目ごとにグラフ化し、さらにそれらをもとに対応すべき項目として優先順位が上なのかどうなのかを自動的に判断し、
判断した根拠を合理的な理由とともに、pdfとしてレポーティングしてくれるデータ基盤構築を行う。

PCやスマートフォンなどはデバイス自体が画面を持っているので「動作が重たくなった」「ログインできない」「いつもと画面が違う」など、使用しているユーザーが異常に気づくことのできるタイミングがあります。
しかし、IoTデバイスは情報を処理することが主目的ではなく、それ自体に画面を持たないためユーザーが変化に気づくことはまれです。
例えばルーターの場合、一度インターネットにつながってしまえば、接続できなくなったなどのトラブルが起きない限り、設定の確認や変更はしないと思います。



!pip install networkx matplotlib pandas
!pip install plotly

import os
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import subprocess
import pkg_resources
import plotly.graph_objects as go
from plotly.offline import plot
from collections import defaultdict

# 1. ライブラリの抽出
def extract_libraries(base_path, limit):
    libraries = []
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(('.dll', '.so', '.exe', '.lib')):  # .soファイルの拡張子
                full_path = os.path.join(root, file)
                libraries.append(full_path)
                if len(libraries) >= limit:  # 指定した数に達したら終了
                    return libraries

# # 2. 依存性の関係性取得
def get_dep_linux(library):
    try:
        result = subprocess.run(['ldd', library], capture_output=True, text=True)
        dependencies = []
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) > 1:
                    dependencies.append(parts[0])  # 依存ライブラリの名前を取得
        return dependencies
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return []

# 3. 依存関係を重みづけて可視化 ===> ???
def create_sankey_diagram(dependencies):
    # 使用頻度をカウントする辞書
    usage_count = defaultdict(int)
    # defaultdict は、Python の標準ライブラリ collections に含まれる辞書の一種である。ここでは、整数をデフォルト値として持つ辞書を作成。
    # これにより、キーが存在しない場合に自動的に 0 が返されるため、カウントを簡単に行える。

    # 依存関係をカウント
    for lib, deps in dependencies.items():
        for dep in deps:
            usage_count[dep] += 1
    print(lib, deps)

    # サンキー図のリンクデータを初期化
    source, target, value = [], [], []

    # 対象共有ライブラリの他ライブラリへの依存度(個数)をカウントし、ソート
    sorted_libs = sorted(dependencies.items(), key=lambda item: len(item[1]), reverse=True)
    # dependencies という辞書（ライブラリとその依存関係のリストを持つデータ構造）から、すべてのライブラリとその依存関係のペアを取得したのち、依存関係の数に基づいて並べ替える
    # key 引数： ソートの基準を指定するために用いる = どのようにアイテムを比較して並べ替えるか
    # lambda関数： pythonにおいて簡単な関数を表現する無名関数。構文「lambda 引数: 戻り値」
    # item： item は、dependencies.items() から取得した各ライブラリとその依存関係のペアのタプル。item[0]=ライブラリ, item[1]=依存関係パーツ
    sorted_lib_labels = [lib for lib, _ in sorted_libs]
    # リスト内表記：構文 new_list = [exp for item in iterable]  exp=追加内容, iterable=リストやタプルなど反復可能なオブジェクト。新しいリストを作成する際に便利！
    # '_' は、Pythonで「使わない変数」を示すための慣習的な名前
    # ---> まとめると、新規 sorted_lib_labelsというリストを sorted_libs(list) という従来のリストの中からlibraryのインデックス、つまりitem[0]だけを繰り返して作成する
    #      = つまり!! リストから特定のインデックスの項目のみ取り出して新しいリストに作り替えるということをやっている。

    # 被対象構成ライブラリの対象ライブラリへの依存度(個数)をカウントし、ソート
    sorted_deps = sorted(usage_count.items(), key=lambda item: item[1], reverse=True)
    sorted_dep_labels = [dep for dep, _ in sorted_deps]

    # ソートされた依存関係に基づいてサンキー図の対象ライブラリ(node)と被依存ライブラリ(node)をつなぐedgeを作成
    for lib in sorted_lib_labels:
        for dep in dependencies[lib]:
            if dep in sorted_dep_labels:
                source_index = sorted_lib_labels.index(lib)  # 左側のノードのインデックス
                target_index = len(sorted_lib_labels) + sorted_dep_labels.index(dep)  # 右側のノードのインデックス
                source.append(source_index)
                target.append(target_index)
                value.append(1)  # edgeの太さに影響する'重み'として付与したいものがある場合、ここにappend

    # 注意！ #
    # ↑で頑張ってソートしたはいいが、サンキー図のノードの配置は依存関係の構造によって決定するため、視覚的には昇順に見えないことがあるらしい...。

    # サンキー図の作成
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=5,
            thickness=10,
            line=dict(color="black", width=1),
            label=sorted_lib_labels + sorted_dep_labels,  # 左側と右側のノードを結合
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
        ))])
  
    # レイアウトの設定
    fig.update_layout(
    title_text="Library Dependency Sankey Diagram (Weighted by Usage Frequency)",
    font_size=10,
    height=3500,  # 高さを指定
    width=1800    # 幅を指定
)

    # サンキー図の表示 or htmlとして保存
    #fig.show()
    plot(fig, filename='sankey_diagram.html', auto_open=True)


# メイン処理
if __name__ == "__main__": 
    base_path = "/usr/local/lib"
    libraries = extract_libraries(base_path, limit=150)
    
    dependencies = {}
    for library in libraries:
        deps = get_dep_linux(library)
        dependencies[library] = deps

    create_sankey_diagram(dependencies)

# def create_sankey_diagram(dependencies):
#     # ノードのラベルを作成
#     labels = list(dependencies.keys())
    
#     # 依存関係のインデックスとフローの強さを定義
#     source = []
#     target = []
#     value = []

#     # 使用頻度をカウントするための辞書
#     usage_count = defaultdict(int)

#     # 依存関係を解析
#     for lib, deps in dependencies.items():
#         for dep in deps:
#             if dep not in labels:
#                 labels.append(dep)  # 依存先がラベルにない場合は追加
#             source_index = labels.index(dep)   # 依存先のインデックス
#             target_index = labels.index(lib)   # 依存元のインデックス
            
#             # 使用頻度をカウント
#             usage_count[(dep, lib)] += 1

#     # フローの強さを使用頻度に基づいて設定
#     for (lib, dep), count in usage_count.items():
#         source_index = labels.index(dep)
#         target_index = labels.index(lib)
#         source.append(source_index)
#         target.append(target_index)
#         value.append(count)  # 使用頻度をフローの強さとして設定

#     # サンキー図の作成
#     fig = go.Figure(data=[go.Sankey(
#         node=dict(
#             pad=5,  # ノード間のパディング
#             thickness=10,  # ノードの厚さ
#             line=dict(color="black", width=1),  # ノードの境界線
#             label=labels,  # ノードのラベル
#         ),
#         link=dict(
#             source=source,  # 依存元
#             target=target,  # 依存先
#             value=value,    # フローの強さ
#         ))])

    # レイアウトの設定
    fig.update_layout(
    title_text="Library Dependency Sankey Diagram (Weighted by Usage Frequency)",
    font_size=10,
    height=3500,  # 高さを指定
    width=1800    # 幅を指定
)

    # サンキー図の表示
    #fig.show()
    plot(fig, filename='sankey_diagram.html', auto_open=True)


# メイン処理
if __name__ == "__main__":  # 追加
    base_path = "/usr/local/lib"  # ライブラリのパスを指定  # 追加
    libraries = extract_libraries(base_path, limit=150)  # 追加
    
    dependencies = {}  # 追加
    for library in libraries:  # 追加
        deps = get_dependencies_linux(library)  # 追加
        dependencies[library] = deps  # 追加

    create_sankey_diagram(dependencies)  # 追加


# def list_python_dependencies():
#     dependencies = {}
#     installed_packages = pkg_resources.working_set
    
#     for package in installed_packages:
#         dependencies[package.project_name] = [str(dep) for dep in package.requires()]
    
#     return dependencies

# def list_cpp_dependencies(base_path):
#     dependencies = {}
#     # C/C++の依存関係を調べるための簡単な方法
#     # ここでは、lddコマンドを使用して共有ライブラリの依存関係を取得します
#     for root, dirs, files in os.walk(base_path):
#         for file in files:
#             if file.endswith(('.so', '.dll', '.dylib')):  # 共有ライブラリの拡張子
#                 file_path = os.path.join(root, file)
#                 try:
#                     output = subprocess.check_output(['ldd', file_path]).decode('utf-8')
#                     dependencies[file_path] = [line.split()[0] for line in output.splitlines() if line]
#                 except subprocess.CalledProcessError:
#                     dependencies[file_path] = ["Coudn't get dependencies info"]
    
#     return dependencies

# def list_java_dependencies(base_path):
#     dependencies = {}
#     # Javaの依存関係を調べるための方法
#     # ここでは、Mavenの依存関係を取得するためのコマンドを使用します
#     for root, dirs, files in os.walk(base_path):
#         for file in files:
#             if file.endswith('pom.xml'):  # Mavenプロジェクトのpom.xmlを探す
#                 file_path = os.path.join(root, file)
#                 try:
#                     output = subprocess.check_output(['mvn', 'dependency:list'], cwd=root).decode('utf-8')
#                     dependencies[file_path] = output.splitlines()
#                 except subprocess.CalledProcessError:
#                     dependencies[file_path] = ["Coudn't get dependencies info"]
    
#     return dependencies

# def list_javascript_dependencies(base_path):
#     dependencies = {}
#     # JavaScriptの依存関係を調べるための方法
#     # ここでは、npmの依存関係を取得するためのコマンドを使用します
#     for root, dirs, files in os.walk(base_path):
#         for file in files:
#             if file == 'package.json':  # npmプロジェクトのpackage.jsonを探す
#                 file_path = os.path.join(root, file)
#                 try:
#                     output = subprocess.check_output(['npm', 'list', '--depth=0'], cwd=root).decode('utf-8')
#                     dependencies[file_path] = output.splitlines()
#                 except subprocess.CalledProcessError:
#                     dependencies[file_path] = ["Coudn't get dependencies info"]
    
#     return dependencies

# def dep_by_lang(dependencies, lang):
#     print(f"{lang} の依存関係:")
#     for item, deps in dependencies.items():
#         print(f"{item}:")
#         for dep in deps:
#             print(f"  - {dep}")
#         print()

# def desc_dep():
#     base_path = "/path/to/your/libraries"  # ライブラリのベースパス

#     # 各言語の依存関係をリストアップ
#     python_deps = list_python_dependencies()
#     cpp_deps = list_cpp_dependencies(base_path)
#     java_deps = list_java_dependencies(base_path)
#     js_deps = list_javascript_dependencies(base_path)

#     # 依存関係を出力
#     print_dependencies(python_deps, "Python")
#     print_dependencies(cpp_deps, "C/C++")
#     print_dependencies(java_deps, "Java")
#     print_dependencies(js_deps, "JavaScript")

# # 3. 脅威の検出
# def detect_threats(libraries, whitelist):
#     threats = []
#     for lib in libraries:
#         if lib not in whitelist:
#             threats.append(lib)  # ホワイトリストにないライブラリを検出
#     return threats

# # 4. 結果のレポート
# def generate_report(threats):
#     if threats:
#         print("不審なパス:")
#         for threat in threats:
#             print(f"- {threat}")
#     elif: #不審なメモリなどの動き
#         pass
#     else:
#         print("脅威は検出されませんでした。")

# # メイン関数
# def main():
#     base_path = "/"  # ライブラリのベースパス
#   # whitelist = set(["C:/path/to/your/libraries/allowed_lib.dll"])  # ホワイトリストの例
#     whitelist_file = "C:/path/to/your/whitelist.csv"  # ホワイトリストのCSVファイルのパス
#     whitelist = load_whitelist(whitelist_file)  # CSVからホワイトリストを読み込む

#     libraries = extract_libraries(base_path)  # ライブラリを抽出
#     visualize_relationships(libraries)  # 関係性を可視化
#     threats = detect_threats(libraries, whitelist)  # 脅威を検出
#     generate_report(threats)  # レポートを生成

# if __name__ == "__main__":
#     main()
