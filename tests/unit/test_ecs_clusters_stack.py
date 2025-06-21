import aws_cdk as cdk
import aws_cdk.assertions as assertions

from ecs_clusters.ecs_clusters_stack import EcsClustersStack


def test_snapshot(snapshot):
    app = cdk.App()
    stack = EcsClustersStack(
        app,
        "ecs-clusters",
        parameters={
            "vpc_id": "vpc-12345678",
            "sg_ids": ["sg-12345678"],
            "cluster_services_glob_path": "config/cluster-services/*.yml",
        },
        env=cdk.Environment(account="123456789012", region="ap-northeast-1"),
    )
    template = assertions.Template.from_stack(stack)

    assert template.to_json() == snapshot
