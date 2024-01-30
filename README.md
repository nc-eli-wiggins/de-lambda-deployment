# Demonstration Project For AWS Infrastructure

The purpose of this project is to demonstrate (in a manner close to production-level code) how to deploy a simple AWS Lambda and associated infrastructure to an AWS account.

Features of the project:
1. A simple lambda handler (`src/file_reader/reader.py`) that accepts an S3 event, checks if it refers to a `txt` file, and then logs the contents of the file.
1. The code features trapping of specific errors (including a custom error) and handles unexpected `RuntimeErrors`.
1. The code is tested (`test/test_file_reader/test_lambda.py`) using the `moto` library to mock AWS artefacts. 
1. The project build is via a `Makefile` which allows `bandit` and `safety` checks for security vulnerabilities, and `black` checks for PEP8 compliance.


### Prerequisites for local development
- Python
- Make
- AWS CLI tool (__version 2__) - installation instructions here: [https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

### __Instructions for Students__
1. Fork and clone this project. 
1. In the terminal, navigate to the root directory of the project, and run:
    ```bash
    make requirements
    ```
1. Then run:
    ```bash
    make dev-setup
    make run-checks
    ```


 