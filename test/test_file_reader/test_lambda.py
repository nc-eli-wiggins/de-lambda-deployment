import json
import pytest
import os
import boto3
from moto import mock_aws
import logging
from botocore.exceptions import ClientError
from src.file_reader.reader import lambda_handler, get_object_path, get_text_from_file

logger = logging.getLogger("test")
logger.setLevel(logging.INFO)
logger.propagate = True


@pytest.fixture
def valid_event():
    with open("test/test_file_reader/test_data/valid_test_event.json") as v:
        event = json.loads(v.read())
    return event


@pytest.fixture
def invalid_event():
    with open("test/test_file_reader/test_data/invalid_test_event.json") as i:
        event = json.loads(i.read())
    return event


@pytest.fixture
def missing_file_event():
    with open("test/test_file_reader/test_data/incorrect_file.json") as i:
        event = json.loads(i.read())
    return event


@pytest.fixture
def wrong_bucket_event():
    with open("test/test_file_reader/test_data/incorrect_bucket.json") as i:
        event = json.loads(i.read())
    return event


@pytest.fixture
def file_type_event():
    with open("test/test_file_reader/test_data/file_type_event.json") as i:
        event = json.loads(i.read())
    return event


@pytest.fixture
def wrong_type_event():
    with open("test/test_file_reader/test_data/wrong_type_event.json") as i:
        event = json.loads(i.read())
    return event


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "test"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
    os.environ["AWS_SECURITY_TOKEN"] = "test"
    os.environ["AWS_SESSION_TOKEN"] = "test"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@pytest.fixture(scope="function")
def s3(aws_credentials):
    with mock_aws():
        yield boto3.client("s3", region_name="eu-west-1")


@pytest.fixture
def bucket(s3):
    s3.create_bucket(
        Bucket="test_bucket",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )
    with open("test/test_file_reader/test_data/test_file.txt") as f:
        text_to_write = f.read()
        s3.put_object(
            Body=text_to_write, Bucket="test_bucket", Key="sample/test_file.txt"
        )
    with open("test/test_file_reader/test_data/wrong.txt", "rb") as f:
        s3.put_object(Body=f, Bucket="test_bucket", Key="sample/wrong.txt")


def test_get_object_path_returns_bucket_and_key(valid_event):
    bucket_result, key_result = get_object_path(valid_event["Records"])
    assert bucket_result == "test_bucket"
    assert key_result == "sample/test_file.txt"


def test_get_object_path_throws_key_error_if_item_not_present(invalid_event):
    with pytest.raises(KeyError):
        get_object_path(invalid_event["Records"])


def test_get_text_from_file_returns_correct_text(s3, bucket):
    test_text = get_text_from_file(s3, "test_bucket", "sample/test_file.txt")
    assert test_text[:14] == "There was once"


def test_get_text_from_file_throws_client_error_if_invalid_call(s3):
    with pytest.raises(ClientError):
        get_text_from_file(s3, "test_bucket", "sample/test_file.txt")


def test_lambda_handler_logs_correct_text(valid_event, caplog, s3, bucket):
    with caplog.at_level(logging.INFO):
        lambda_handler(valid_event, {})
        assert "There was once" in caplog.text


def test_lambda_handler_logs_if_no_such_key(missing_file_event, caplog, s3, bucket):
    with caplog.at_level(logging.INFO):
        lambda_handler(missing_file_event, {})
        assert "No object found - sample/wrong_file.txt" in caplog.text


def test_lambda_handler_logs_if_no_such_bucket(wrong_bucket_event, caplog, s3, bucket):
    with caplog.at_level(logging.INFO):
        lambda_handler(wrong_bucket_event, {})
        assert "No such bucket - wrong_bucket" in caplog.text


def test_lambda_handler_throws_logs_message_if_not_txt_file(
    file_type_event, caplog, s3, bucket
):
    with caplog.at_level(logging.INFO):
        lambda_handler(file_type_event, {})
        assert "File sample/test_file.png is not a valid text file" in caplog.text


def test_lambda_handler_throws_log_message_if_txt_file_invalid(
    wrong_type_event, caplog, s3, bucket
):
    with caplog.at_level(logging.INFO):
        lambda_handler(wrong_type_event, {})
        assert "File sample/wrong.txt is not a valid text file" in caplog.text
