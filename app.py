#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_ecs_clusters.cdk_ecs_clusters_stack import EcsClustersStack

app = cdk.App()
EcsClustersStack(
    app,
    "EcsClustersStack",
    parameters={
        "vpc_id": "<VPC-ID>",
        "sg_ids": ["<SECURITY-GROUP-ID>"],
        "cluster_services_glob_path": "config/cluster-services/*.yml",
    },
    # ap-northeast-1リージョンを指定
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region="ap-northeast-1"
    ),
)

app.synth()
