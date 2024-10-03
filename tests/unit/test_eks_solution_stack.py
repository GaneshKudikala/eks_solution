# tests/unit/test_eks_solution_stack.py

import unittest
from aws_cdk import App
from eks_solution.eks_solution_stack import EksSolutionStack
from aws_cdk.assertions import Template

class TestEksSolutionStack(unittest.TestCase):

    def setUp(self):
        self.app = App()
        self.stack = EksSolutionStack(self.app, "EksSolutionStack")
        self.template = Template.from_stack(self.stack)

    def test_vpc_created(self):
        # Check if a VPC resource is created
        self.template.resource_count_is("AWS::EC2::VPC", 1)

    def test_eks_cluster_created(self):
        self.template.resource_count_is("Custom::AWSCDK-EKS-Cluster", 1)

    def test_lambda_function_created(self):
        self.template.has_resource_properties("AWS::Lambda::Function", {
            "Handler": "index.handler",
            "Runtime": "python3.9",
        })

    def test_ssm_parameter_created(self):
        self.template.has_resource_properties("AWS::SSM::Parameter", {
            "Type": "String",
            "Name": "/platform/account/env",
        })


if __name__ == '__main__':
    unittest.main()
