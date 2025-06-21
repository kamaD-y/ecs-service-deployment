import glob
from pathlib import Path
from typing import List, Optional, TypedDict

import yaml
from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from constructs import Construct


class ClusterService(TypedDict):
    service_name: str
    task_arn: str
    desired_count: int
    task_definition: ecs.ITaskDefinition


class ClusterInfo(TypedDict):
    name: str
    cluster: ecs.ICluster
    services: List[ClusterService]


# 既存リソースを取得するコンストラクタ
class ExistingResourceConstructor(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        vpc_id: str,
        sg_ids: List[str],
        cluster_services_glob_path: str,
    ) -> None:
        super().__init__(scope, id)
        self.vpc: Optional[ec2.IVpc] = None
        self.security_groups: List[ec2.ISecurityGroup] = []
        self.clusters: List[ClusterInfo] = []
        self.load_existing_resources(vpc_id, sg_ids, cluster_services_glob_path)

    def _load_existing_vpc(self, vpc_id: str) -> None:
        self.vpc = ec2.Vpc.from_lookup(self, "ImportedVpc", vpc_id=vpc_id)

    def _load_existing_security_groups(self, sg_ids: list) -> None:
        for i, sg_id in enumerate(sg_ids):
            self.security_groups.append(
                ec2.SecurityGroup.from_security_group_id(self, f"ImportedSecurityGroup{i}", security_group_id=sg_id)
            )

    def _load_existing_clusters(self, cluster_services_glob_path: str) -> None:
        for file_path in glob.glob(cluster_services_glob_path):
            cluster_info = {}
            cluster_name = Path(file_path).stem
            cluster_info["name"] = cluster_name
            cluster_info["cluster"] = ecs.Cluster.from_cluster_attributes(
                self,
                f"ImportedCluster-{cluster_name}",
                cluster_name=cluster_name,
                vpc=self.vpc,
                security_groups=self.security_groups,
            )
            with open(file_path, "r") as file:
                cluster_info["services"] = yaml.safe_load(file)
            for service in cluster_info["services"]:
                service["task_definition"] = ecs.TaskDefinition.from_task_definition_arn(
                    self,
                    f"ImportedTaskDef-{cluster_name}-{service['service_name']}",
                    task_definition_arn=service["task_arn"],
                )
            self.clusters.append(cluster_info)

    def load_existing_resources(self, vpc_id: str, sg_ids: list, cluster_services_glob_path: str) -> None:
        self._load_existing_vpc(vpc_id)
        self._load_existing_security_groups(sg_ids)
        self._load_existing_clusters(cluster_services_glob_path)
        # print(self.clusters)
        """
        [{
          'name': 'fargate-cluster-1',
          'cluster': <jsii._reference_map.InterfaceDynamicProxy object at 0x7f4618d7a000>,
          'services': [
            {'name': 'fargate-service-1',
            'task_arn': 'arn:aws:ecs:ap-northeast-1:123456789012:task-definition/task-1:1',
            'desired_count': 2,
            'task_definition': <jsii._reference_map.InterfaceDynamicProxy object at 0x7f4618cf5dc0>
            },
            {'name': 'fargate-service-2',
            'task_arn': 'arn:aws:ecs:ap-northeast-1:123456789012:task-definition/task-1:2',
            'desired_count': 3,
            'task_definition': <jsii._reference_map.InterfaceDynamicProxy object at 0x7f4618cf5760>
            },
          ]
        }]
        """


class EcsClustersStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, parameters, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        """
        既存リソース参照
        """
        vpc_id = parameters["vpc_id"]
        sg_ids = parameters["sg_ids"]
        cluster_services_glob_path = parameters["cluster_services_glob_path"]

        existing_resource = ExistingResourceConstructor(
            self, "ExistingResources", vpc_id, sg_ids, cluster_services_glob_path
        )

        """
        サービス作成
        """
        # 必須の何かがITaskDefinitionでは足りないらしく、既存のタスク定義では不可の為仕方なく一旦TaskDefinitionを作成する
        # 一時的にサービスにデフォルトタスク定義を紐づけておき、後で既存のタスク定義を紐づける
        # ref: https://github.com/aws/aws-cdk/issues/7863
        default_task_definition = ecs.TaskDefinition(
            self,
            "DefaultTaskDef",
            family="DefaultTaskDef",
            compatibility=ecs.Compatibility.FARGATE,
            cpu="256",
            memory_mib="512",
            network_mode=ecs.NetworkMode.AWS_VPC,
            task_role=None,
            execution_role=None,
        )
        default_task_definition.add_container(
            "DefaultContainer",
            image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample"),
            memory_limit_mib=512,
            cpu=256,
        )

        # 各クラスターのサービスを作成
        for cluster in existing_resource.clusters:
            for cluster_service in cluster["services"]:
                service_name = cluster_service["service_name"]

                # Fargateサービスを作成, 一時的にデフォルトタスク定義を関連付ける
                fargate_service = ecs.FargateService(
                    self,
                    f"FargateService-{cluster['name']}-{service_name}",
                    cluster=cluster["cluster"],
                    task_definition=default_task_definition,
                    desired_count=cluster_service["desired_count"],
                    service_name=service_name,
                    assign_public_ip=True,  # 必要に応じて設定
                )
                # 既存のタスク定義を関連付けし直す
                fargate_service.node.try_find_child("Service").task_definition = cluster_service[
                    "task_definition"
                ].task_definition_arn

                CfnOutput(
                    self,
                    f"ServiceARN-{cluster['name']}-{service_name}",
                    value=fargate_service.service_arn,
                    description=f"ARN of the {service_name} service",
                )
