
# EKS Project - CDK Python Project

This project provisions an EKS cluster along with several related resources using AWS CDK (Python). Below are the detailed instructions to set up and run the project.

## Resources Created
1. **EKS Cluster**: A simple EKS cluster using the [aws-cdk-lib.aws_eks](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_eks-readme.html).
2. **SSM Parameter**: An SSM parameter `/platform/account/env` containing values like `development`, `staging`, or `production`.
3. **Helm Chart**: Installation of [ingress-nginx](https://artifacthub.io/packages/helm/ingress-nginx/ingress-nginx) using Helm on the EKS cluster. The chart values are fetched dynamically from a CustomResource.
4. **CustomResource with Lambda**: A Lambda function retrieves the account environment from the SSM parameter and generates Helm chart values such as `controller.replicaCount`, which is referenced in the Helm chart deployment.
5. **Hellow World**: It will also deploy a Hello world app to see all works fine. 

## Inside cdk.json you have the configuration to define the environment
  "context": {
    "environment": "production"
    }



## Setup Instructions

### Step 1: Initialize the Python Virtual Environment
To set up your Python environment:



This is a blank project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
