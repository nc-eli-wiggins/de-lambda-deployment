# Using the AWS CLI to Deploy Python Code to Lambda

## Prerequisites

It is assumed you have the AWS CLI installed correctly.

Fork and clone [this GitHub repository](https://github.com/northcoders/de-lambda-deployment). Note that this repo has two branches. Please fork both. Just uncheck the box marked "Fork main branch only".

## Introduction

One of the most common tools for deploying code in data engineering applications is the serverless function - in AWS called Lambda. It allows small jobs to be executed without requiring major server provision. We deployed a very small Lambda in a previous lecture.

In this lecture, we will deploy almost exactly the same Lambda - the code reads a file in S3 and writes the contents to a log file - but with something much more like a realistic deployment process. Furthermore, the code will be closer to production standard than the few lines we deployed previously.

Our goal will be to map out a process that we can use to deploy the code automatically, through an "infrastructure as code" tool such as Terraform, and CI/CD with GitHub Actions. Today's work will be our "dry run" for that automated deployment. We'll need to decide what steps are required for the deployment and how we can use the AWS CLI to deploy them.

## What steps are needed?

Recalling the last lecture, we carried out the following steps:

1. Create an S3 bucket for the data file
2. Create a Lambda function
3. Copy the code to the function
4. Add a special permission to the IAM role in the Lambda to allow access to S3
5. Add an event configuration to the bucket to trigger the Lambda

We'll need to carry out some of these steps, and we'll need more detail in some of them. The console deployment that we did last time obscured a couple of issues:

1. We just pasted the code into an on-screen editor - in this deployment, we will need to decide where the code is to be stored.
2. The console automatically created an IAM role and basic permissions for access to Cloudwatch logs. We will need to carry out these steps ourselves.
3. When we created the event notification, the console automatically added a further permission to the Lambda allowing it to be invoked by S3.

The standard procedure for deploying a Python Lambda is detailed [here](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html). Essentially, the code (and all its dependencies) has to be saved in a zip archive. The zip file can be saved either to the Lambda itself or to an S3 location. We are going to use an S3 location. The code is already written in the repository you cloned already, and we will not need to make any changes to it. We will look at the code in more detail in a later lecture.

So the overall architecture we need to deploy looks like this:
![Lambda.png](./Lambda.png)

The list of steps will be as follows:

1. Create two S3 buckets, one for the data and one for the code.
2. Create a deployment package for the code and copy it to the code bucket.
3. Create an IAM policy that allows read access to S3 - this will need to allow the Lambda to read the code from the code bucket as well as read the data from the data bucket.
4. Create an IAM policy that allows write access to Cloudwatch Logs and also allows Lambda to create its own log files.
5. Create an IAM role for Lambda with the two policies attached.
6. Create the function, using the code in the code bucket and the IAM role.
7. Create a [resource based permission](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_compare-resource-policies.html) to allow the S3 bucket to invoke the Lambda function
8. Finally, add the event notification to the S3 data bucket to invoke the function when an object is put in the bucket.

We'll do all this with the CLI.

One prior step: please make sure you are in the root directory of the repo to execute these commands.

## Step 1 - The S3 Buckets

We saw in the last talk how to create an S3 bucket. We also learned that bucket names have to be _globally_ unique, so we need to take steps to ensure that the name is valid.

Type the following:

```bash
SUFFIX=$(date +%s)
```

We are using the syntax that allows us to assign the output of a command to a variable. `SUFFIX` is assigned to the output of the command `date +%s`, which gives us a Unix timestamp.

Why do this? Well, we now have a handy suffix to attach onto the end of any names we create that can ensure they are unique. We can make another couple of variables to temporarily store our bucket names which we will definitely need later in the process:

```bash
DATA_BUCKET_NAME=nc-de-jm-data-${SUFFIX}
CODE_BUCKET_NAME=nc-de-jm-code-${SUFFIX}
```

Use your own text for the first part of the bucket. Note the syntax to refer to the value of the `SUFFIX` variable - we need to use a `$` to tell the shell that we are referring to a variable.

Now we are able to execute the AWS commands to create the buckets:

```bash
aws s3 mb s3://${DATA_BUCKET_NAME}
aws s3 mb s3://${CODE_BUCKET_NAME}
```

You should see a brief message similar to this:

```bash
make_bucket: nc-de-jm-data-1666009331
make_bucket: nc-de-jm-code-1666009331
```

Note the variable assignments and the CLI commands in your `deployment.txt` file.

We can check that the buckets have been properly created by typing:

```bash
aws s3 ls
```

See https://awscli.amazonaws.com/v2/documentation/api/latest/reference/s3/ls.html.

## Step 2 - The Deployment Package

To remind you what we are trying to do, the process for creating a Python deployment package for Lambda is detailed [here](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html). We need to create a zip archive of the code (which is in the file `src/file_reader/reader.py`) and then copy it to our S3 code bucket.

In principle, we should also include the dependencies of the code. In this case, our code relies on the §boto3§ library. However, AWS include the `boto3` library in every Python Lambda by default, so we no not need to do this step.

Prior to creating the deployment package, it will be useful to have decided on the name of our function. Although there is no requirement for uniqueness, it can be useful (when dealing with automated builds), so I recommend that you use the `SUFFIX` variable to create something like:

```bash
FUNCTION_NAME=s3-file-reader-${SUFFIX}
```

To create the zip archive:

```bash
cd src/file_reader
zip ../../function.zip reader.py
cd ../..
```

This creates the zip file `function.zip` in the root directory of the repo.

Now we need to copy the file from the local directory to S3. For this, we can use the [cp](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/s3/cp.html) command.

This is pretty straightforward. Type:

```bash
aws s3 cp function.zip s3://${CODE_BUCKET_NAME}/${FUNCTION_NAME}/function.zip
```

To check that the file has arrived:

```bash
aws s3 ls ${CODE_BUCKET_NAME} --recursive --human-readable --summarize
```


## Step 3 - The S3 IAM Policy

The documentation for creating an IAM policy is here: https://awscli.amazonaws.com/v2/documentation/api/latest/reference/iam/create-policy.html.

THe basic syntax is:

```bash
aws iam create-policy --policy-name [POLICY NAME] --policy-document file://[PATH TO JSON FILE]
```

The major input is a valid AWS policy file in `json` format. See [the documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_examples.html). A template has been provided for you at `deployments/templates/s3_read_policy_template.json` in the repo. It looks like this:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "VisualEditor0",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": ["Insert", "Insert"]
    }
  ]
}
```

To create the policy statement, just use an editor to replace the word "Insert" with the bucket ARNs, like so:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "VisualEditor0",
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": ["arn:aws:s3:::BUCKET_NAME/*", "arn:aws:s3:::BUCKET_NAME/*"]
    }
  ]
}
```

Now we can run our `create-policy` process. The documentation tells us that the command outputs some JSON like this:

```json
{
  "Policy": {
    "PolicyName": "my-policy",
    "CreateDate": "2015-06-01T19:31:18.620Z",
    "AttachmentCount": 0,
    "IsAttachable": true,
    "PolicyId": "ZXR6A36LTYANPAI7NJ5UV",
    "DefaultVersionId": "v1",
    "Path": "/",
    "Arn": "arn:aws:iam::0123456789012:policy/my-policy",
    "UpdateDate": "2015-06-01T19:31:18.620Z"
  }
}
```

It will be useful to have the policy ARN available for later use, so let's run the command using our `jq` tricks to extract this as a variable:

```bash
S3_POLICY=$(aws iam create-policy --policy-name s3-read-policy-${FUNCTION_NAME} \
--policy-document file://deployment/templates/s3_read_policy_template.json | jq .Policy.Arn | tr -d '"')
```

I've used the `FUNCTION_NAME` variable to make the policy name more specific.


## Step 4 - The Cloudwatch IAM Policy

The steps for the Cloudwatch policy are very similar. You will find the relevant template in the repo. The policy needs to end up looking like this:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "logs:CreateLogGroup",
      "Resource": "arn:aws:logs:eu-west-2:999999999999:*"
    },
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": [
        "arn:aws:logs:eu-west-2:999999999999:log-group:/aws/lambda/s3-file-reader-1666009331:*"
      ]
    }
  ]
}
```

Insert your own account number in place of the "999999999999" and your own function name instead of the "s3-file-reader-1666009331". If you don't know your account number, you can get it with this command:

```bash
AWS_ACCOUNT_ID=$(aws sts get-caller-identity | jq .Account | tr -d '"'
```

It will be usefult to save this in a variable for later use.

Then the `create-policy` command is much as before:

```bash
CLOUDWATCH_POLICY=$(aws iam create-policy --policy-name cloudwatch-policy-${FUNCTION_NAME} \
--policy-document file://deployment/templates/cloudwatch_log_policy_template.json | jq .Policy.Arn | tr -d '"')
```

## Step 5 - The IAM Role

An IAM _policy_ is basically a certificate that says "These actions are allowed on these resources." A _role_ is a document says "These particular user or services are allowed to hold the attached policies." In other words the role adds the information about who or what can perform the actions described in the policies.

The documentation about creating a role is here: https://awscli.amazonaws.com/v2/documentation/api/latest/reference/iam/create-role.html.

The basic syntax is similar to that for the policies:

```bash
aws iam create-role --role-name [ROLE NAME] --assume-role-policy-document file://[PATH_TO_JSON_FILE]
```

Here, the JSON document is called a _trust policy_ and simply says who or what holds the permssions. In this case, the AWS Lambda service can be granted the permissions, so you will find the required file (which does not need modification) in the repo as `deployment/trust_policy.json`.

As before, it will be useful to save the ARN of the created role for later use, so the required command is:

```bash
EXECUTION_ROLE=$(aws iam create-role --role-name lambda-execution-role-${FUNCTION_NAME} \
--assume-role-policy-document file://deployment/trust_policy.json | jq .Role.Arn | tr -d '"')
```

This creates a role, but there are no permissions attached to it, so it's basically sterile. To attach the policies we made, we need the [attach-role-policy](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/iam/attach-role-policy.html) command:

```bash
aws iam attach-role-policy --policy-arn ${CLOUDWATCH_POLICY} --role-name lambda-execution-role-${FUNCTION_NAME}
aws iam attach-role-policy --policy-arn ${S3_POLICY} --role-name lambda-execution-role-${FUNCTION_NAME}
```

Now the role grants the Lambda service the right to read data from specific buckets in S3 and create and write a log in Cloudwatch, and this is what we need.


## Step 6 - Creating the function

Now we are ready to create the Lambda function. The documentation is here:
https://awscli.amazonaws.com/v2/documentation/api/latest/reference/lambda/create-function.html.

There are a few points to clarify about this. It looks from the documentation as if the only required arguments are `function-name` and `role`. In fact, there has to be some method for attaching the code or a location for the code. We have uploaded a zip file with the code to S3, so the command for creating the function will take this form:

```bash
aws lambda create-function --function-name ${FUNCTION_NAME} --runtime python3.9 \
--role ${EXECUTION_ROLE} \
--package-type Zip --handler reader.lambda_handler \
--code S3Bucket=${CODE_BUCKET_NAME},S3Key=${FUNCTION_NAME}/function.zip
```

To explain the arguments individually:

- `function-name` is compulsory and we just pass our previously defined variable for this.
- `role` is compulsory and we use the variable that contains our role ARN.
- `runtime` is required when a zip file is used so that Lambda knows what language and version to expect. At the time of writing, `python3.9` is the default (and latest) Python version allowed.
- `package-type` could be `Image` (for a Docker image), but for us a zip file is adequate.
- `handler` tells Lambda which file and function to use as the entry point for code execution.
- `code` indicates the code location.


## Step 7 - Resource Permission

There is one more permission to add. We need to allow Lambda to be called by S3. In a sane world, this would be handled by the same IAM process we used earlier, but it isn't. Instead we need a _resource-based permission_. Somewhere in a deep basement in the AWS headquarters, there's a guy who knows why.

The required documentation is here, cunningly hidden in the Lambda pages rather than with IAM: https://awscli.amazonaws.com/v2/documentation/api/latest/reference/lambda/add-permission.html.

The required syntax is:

```bash
aws lambda add-permission --function-name ${FUNCTION_NAME} --principal s3.amazonaws.com \
--statement-id s3invoke --action "lambda:InvokeFunction" \
--source-arn arn:aws:s3:::${DATA_BUCKET_NAME} \
--source-account ${AWS_ACCOUNT_ID}
```

The `statement_id` field is nothing special - just a human-readable indicator to remind us what this is for.


## Step 8 - Event Notification

The final step is to add an event notification to S3 so that Lambda will be triggered when any new object is added to the data bucket. The necessary function is called `put-bucket-notification-configuration` and is part of the `s3api` service: https://awscli.amazonaws.com/v2/documentation/api/latest/reference/s3api/put-bucket-notification-configuration.html.

For this we need a configuration file. A template for this file is included at `deployment/templates/s3_event_config_template.json`. As before, we can modify this and save a new file that looks something like this:

```json
{
  "LambdaFunctionConfigurations": [
    {
      "LambdaFunctionArn": "arn:aws:lambda:eu-west-2:999999999999:function:s3-file-reader-1666009331",
      "Events": ["s3:ObjectCreated:*"]
    }
  ]
}
```

As usual, substitute the correct account number and function name.

Then the event notification is created like this:

```bash
aws s3api put-bucket-notification-configuration --bucket ${DATA_BUCKET_NAME} \
--notification-configuration file://deployment/templates/s3_event_config_template.json
```


## Wrapping up

We can test that the deployment worked by adding a small text file to the S3 bucket and watching the log. As in the previous lecture, if you need a small file to use, then you can type:

```bash
python -c "import this" > zen.txt
```

Then:

```bash
aws s3 cp zen.txt s3://${DATA_BUCKET_NAME}/data/zen.txt
```

This should have created a log. To check:

```bash
aws logs tail /aws/lambda/${FUNCTION_NAME}
```

You should see the required data.

You can also log into the console and visually inspect the infrastructure you have created.

How has all of this helped us? So far we've just managed to replicate what we did with the console last time.

Well, we can now perform the deployment with _code_. That means we can automate the process, making it repeatable, efficient and much less susceptible to human error. These steps could be turned into a reusable bash script. However, we will find that there is a useful tool called Terraform that will perform the same actions for us in a more robust way.
