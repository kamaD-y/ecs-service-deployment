import aws_cdk as core
import aws_cdk.assertions as assertions

from ecs_clusters.ecs_clusters_stack import EcsClustersStack


# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_ecs_clusters/cdk_ecs_clusters_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = EcsClustersStack(app, "ecs-clusters")
    template = assertions.Template.from_stack(stack)


#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
