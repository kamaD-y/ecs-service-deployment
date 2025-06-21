# 概要
ECS サービスの展開を効率化する為の CDK のサンプルです。

以下が既に AWS 環境に作成済であることを想定しています。
- ECS クラスター
- タスク定義
- VPC
- SecurityGroup

# 利用手順

`config/cluster-services` に以下ルールでクラスター毎にファイルを作成します。

- `<クラスター名>.yml`
```yaml
- service_name: <サービス名>
  task_arn: <タスク定義 ARN(リビジョン番号含む)>
  desired_count: <指定タスクの実行数>
```

※リビジョン番号を指定しない場合は最新リビジョンがデプロイされますが、2回目以降差分が判別できなくなる点は非対応です。

# デプロイ

`app.py`に作成済の VPC-ID, SECURITY-GROUP-ID を記述の上以下コマンドを実行します。

```sh
# 差分確認
$ cdk diff

# デプロイ
$ cdk deploy
```
