# lambda/index.py

import boto3
import json

def handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    request_type = event.get('RequestType', 'Create')
    physical_resource_id = event.get('PhysicalResourceId', 'CustomResourceUniqueId')

    ssm = boto3.client('ssm')
    parameter = ssm.get_parameter(Name='/platform/account/env')
    environment = parameter['Parameter']['Value']

    # Determine replica count based on environment
    if environment == 'development':
        replica_count = '1'
    elif environment in ['staging', 'production']:
        replica_count = '2'
    else:
        replica_count = '1'

    response = {
        'PhysicalResourceId': physical_resource_id,
        'Data': {
            'ReplicaCount': replica_count
        }
    }

    print(f"Response: {json.dumps(response)}")

    return response
