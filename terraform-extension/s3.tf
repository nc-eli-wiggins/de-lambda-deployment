resource "aws_s3_bucket" "jenkins_bucket" {
  bucket_prefix = "jenkins-example-"
  force_destroy = true
}