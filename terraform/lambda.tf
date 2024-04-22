resource "aws_lambda_function" "s3_file_reader" {
    function_name = "${var.lambda_name}"
    s3_bucket = aws_s3_bucket.code_bucket.bucket
    s3_key = "s3_file_reader/function.zip"
    role = aws_iam_role.lambda_role.arn
    handler = "reader.lambda_handler"
    runtime = "python3.9"
}

data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/../src/file_reader/reader.py"
  output_path = "${path.module}/../function.zip"
}

resource "aws_lambda_permission" "allow_s3" {
  action = "lambda:InvokeFunction"
  function_name = aws_lambda_function.s3_file_reader.function_name
  principal = "s3.amazonaws.com"
  source_arn = aws_s3_bucket.data_bucket.arn
  source_account = data.aws_caller_identity.current.account_id
}