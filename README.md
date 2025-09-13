# s3にアップロードされた画像をリサイズするlambda関数をpyhonで作る方法

画像リサイズするのにPillowが必要なので用意する

・python3.12 を利用

ec2でzip生成した方がいい。
Mac や Windows で Pillow をインストールすると、ビルドされた .so ファイル（Cで書かれたネイティブライブラリ）が ローカルOS向け になってしまい、Lambdaで実行すると
cannot import name '_imaging' のようなエラーが出る。

・以下、zip生成方法

・開発ツールのインストール等
sudo dnf groupinstall "Development Tools" -y
sudo dnf update -y
sudo dnf install -y python3.12 python3.12-pip zip

・インストール確認
python3.12 --version
pip3.12 --version

・作業ディレクトリ作成
mkdir ~/pillow-layer
cd ~/pillow-layer
mkdir -p python/lib/python3.12/site-packages

・Pillow をインストール
pip3.12 install pillow -t python/lib/python3.12/site-packages

・ZIP ファイル作成
zip -r9 ../pillow-python312.zip python

・作成された ZIP を確認
ls -lh ../pillow-python312.zip

できあがった pillow-python312.zip をAWSにlambdaにアップロードしレイヤーを作成する。pillow312等任意の名前をつける。


ランタイム
    Python 3.12
ハンドラ情報
    lambda_function.lambda_handler （ファイル名: lambda_function.py 関数名: lambda_handler）
アーキテクチャ情報
    x86_64
とする。


lambda関数に作ったレイヤーを追加する。コードソースの下の方にレイヤー追加がある。


lambda関数にトリガーを追加
ソースはs3を選択しバケットはあらかじめs3で作ったバケットを指定
イベントタイプはすべてのオブジェクト作成イベント
プレフィックスを original/
サフィックスを.jpg
再帰呼び出しにチェックを入れて
追加

pythonコード（lambda_function.py）をデプロイ後に
s3のoriginal/ にjpg画像をアップロードすると
resized/ にリサイズされた画像が作られる。
