# tests/unit/test_lambda_function.py
import boto3
import pytest
from eks_solution.lambda_function.index import handler

class MockSSMClient:
    def __init__(self, env_value):
        self.env_value = env_value

    def get_parameter(self, Name):
        return {
            'Parameter': {
                'Name': Name,
                'Value': self.env_value
            }
        }

@pytest.fixture
def mock_boto3_client(monkeypatch):
    def _mock_boto3_client(env_value):
        def mock_client(service_name, *args, **kwargs):
            if service_name == 'ssm':
                return MockSSMClient(env_value)
            else:
                raise ValueError(f"Unsupported service: {service_name}")
        monkeypatch.setattr(boto3, 'client', mock_client)
    return _mock_boto3_client

def test_handler_development(mock_boto3_client):
    mock_boto3_client('development')
    event = {'RequestType': 'Create'}
    context = {}
    response = handler(event, context)
    assert response['Data']['ReplicaCount'] == '1'

def test_handler_staging(mock_boto3_client):
    mock_boto3_client('staging')
    event = {'RequestType': 'Create'}
    context = {}
    response = handler(event, context)
    assert response['Data']['ReplicaCount'] == '2'

def test_handler_production(mock_boto3_client):
    mock_boto3_client('production')
    event = {'RequestType': 'Create'}
    context = {}
    response = handler(event, context)
    assert response['Data']['ReplicaCount'] == '2'  

def test_handler_unknown_environment(mock_boto3_client):
    mock_boto3_client('unknown')
    event = {'RequestType': 'Create'}
    context = {}
    response = handler(event, context)
    assert response['Data']['ReplicaCount'] == '1'
