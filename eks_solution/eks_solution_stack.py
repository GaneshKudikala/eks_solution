from aws_cdk import (
    Stack,
    Tags,
    aws_kms as kms,
    aws_ec2 as ec2,
    CfnOutput,
    aws_s3 as s3,
    aws_ssm as ssm,
    aws_iam as iam,
    aws_eks as eks,
    aws_lambda as _lambda,
    custom_resources as cr,
    aws_logs as logs,
    Fn,
    Duration,
    CustomResource,
)
from constructs import Construct
import json
from pathlib import Path

class EksSolutionStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # Enable Tags for the resources you can add more tags if you want add another line to add
        Tags.of(self).add("Owner", "GK")
        Tags.of(self).add("Project", "EksSolutionStack")

        # Create a VPC for the EKS cluster based on the configuration
        vpc = ec2.Vpc(
            self, 
            "EksVpc",
            max_azs=3, 
            nat_gateways=1,  
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="PublicSubnet",
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name="PrivateSubnet",
                    cidr_mask=24
                )
            ]
        )

        # Encryption for the EKS cluster using Custom Key instead of the default Key
        kms_key = kms.Key(self, "EksKmsKey",
                  enable_key_rotation=True,
                  alias="alias/eks-kms-key")

        # IAM Role for the Kubectl to access the EKS cluster after that you need to add your user ARN into the trusted relationship
        eks_role = iam.Role(self, "eksadmin",
                            assumed_by=iam.ServicePrincipal(service='ec2.amazonaws.com'),
                            role_name='eks-cluster-role',
                            managed_policies=[
                                iam.ManagedPolicy.from_aws_managed_policy_name('AdministratorAccess')
                            ])
        eks_instance_profile = iam.CfnInstanceProfile(self, 'instanceprofile',
                                                      roles=[eks_role.role_name],
                                                      instance_profile_name='eks-cluster-role')

        cluster = eks.Cluster(self, 'prod', cluster_name='cdk-eks',
                              version=eks.KubernetesVersion.V1_30,
                              vpc=vpc,
                              vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)],
                              default_capacity=0,
                              masters_role=eks_role,
                              secrets_encryption_key=kms_key,
                              cluster_logging=[
                                  eks.ClusterLoggingTypes.API,
                                  eks.ClusterLoggingTypes.AUTHENTICATOR,
                                  eks.ClusterLoggingTypes.AUDIT,
                                  eks.ClusterLoggingTypes.CONTROLLER_MANAGER,
                                  eks.ClusterLoggingTypes.SCHEDULER
                              ])

        # Create the Node Groups for the Kubernetes pods and the ingress
        nodegroup = cluster.add_nodegroup_capacity('eks-nodegroup',
                                                   instance_types=[ec2.InstanceType('t3.medium')],
                                                   disk_size=50,
                                                   min_size=2,
                                                   max_size=2,
                                                   desired_size=2,
                                                   subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS))

        # Create an SSM parameter with the name '/platform/account/env' and the value 'development', 'staging', or 'production'
        env = self.node.try_get_context("environment") or "development"
        ssm_parameter = ssm.StringParameter(
            self,
            "EnvironmentParameter",
            parameter_name="/platform/account/env",
            string_value=env  # THis ENV is passed form the cdk.context.json file
        )

        # Create a Lambda function to retrieve the SSM parameter
        lambda_function = _lambda.Function(
            self, "GetHelmValuesFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="index.handler",
            code=_lambda.Code.from_asset(str(Path(__file__).parent / 'lambda_function')),
            timeout=Duration.seconds(60),
            log_retention=logs.RetentionDays.ONE_DAY,
        )

        # Grant Lambda function read access to the SSM parameter
        ssm_parameter.grant_read(lambda_function)

        # Create the CustomResource provider
        provider = cr.Provider(
            self,
            "CustomResourceProvider",
            on_event_handler=lambda_function
        )

        # Create the CustomResource using aws_cloudformation.CustomResource
        custom_resource = CustomResource(
            self,
            "HelmValuesCustomResource",
            service_token=provider.service_token,
            properties={
            "Environment": env  # Add this property
            }
        )

        # Get the ReplicaCount from the CustomResource attribute
        replica_count = custom_resource.get_att("ReplicaCount").to_string()


        # Output the replica_count inside the Cloudformation console
        CfnOutput(self, "ReplicaCountOutput", value=replica_count)

        # Create the Helm values for the ingress-nginx chart
        helm_values = {
            "controller": {
                "replicaCount": replica_count
            }
        }

        # Install the ingress-nginx Helm chart into the EKS cluster
        ingress_chart = eks.HelmChart(
            self,
            "IngressNginxChart",
            cluster=cluster,
            chart="ingress-nginx",
            repository="https://kubernetes.github.io/ingress-nginx",
            namespace="ingress-nginx",
            release="ingress-nginx",
            create_namespace=True,
            values=helm_values,
            wait=True,
            timeout=Duration.minutes(15), 
        )
        #This is depdency of the custom resource
        ingress_chart.node.add_dependency(custom_resource)




        ########################################### THis is Hello World APP ###########################
        # Once CDK deployed you can find the ingress DNS to see the Hello world APP
        
        deployment_manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "hello-world-deployment"},
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": "hello-world"}},
                "template": {
                    "metadata": {"labels": {"app": "hello-world"}},
                    "spec": {
                        "containers": [
                            {
                                "name": "hello-world",
                                "image": "nginxdemos/hello:latest",  # Use the public image
                                "ports": [{"containerPort": 80}],
                            }
                        ]
                    },
                },
            },
        }

        # Define the Kubernetes service manifest
        service_manifest = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": "hello-world-service"},
            "spec": {
                "type": "ClusterIP",
                "selector": {"app": "hello-world"},
                "ports": [{"port": 80, "targetPort": 80}],
            },
        }

        # Deploy the manifests to the EKS cluster
        deployment = cluster.add_manifest("HelloWorldDeployment", deployment_manifest)
        service = cluster.add_manifest("HelloWorldService", service_manifest)

        # Define the Kubernetes Ingress manifest
        ingress_manifest = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": "hello-world-ingress",
            },
            "spec": {
                "ingressClassName": "nginx",
                "rules": [
                    {
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": "hello-world-service",
                                            "port": {"number": 80},
                                        }
                                    },
                                }
                            ]
                        }
                    }
                ]
            },
        }

        # Deploy the Ingress to the EKS cluster
        ingress = cluster.add_manifest("HelloWorldIngress", ingress_manifest)

        # Ensure that the deployment and service are created before the ingress
        ingress.node.add_dependency(deployment)
        ingress.node.add_dependency(service)

        # Add dependency to ensure that ingress-nginx is installed before the application manifests
        deployment.node.add_dependency(ingress_chart)
        service.node.add_dependency(ingress_chart)
        ingress.node.add_dependency(ingress_chart)
        