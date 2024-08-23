terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket = "<name of your s3 bucket here>"
    key = "jenkins-extension/terraform.tfstate"
    region = "eu-west-2"
  }
}

provider "aws" {
  region = "eu-west-2"
  default_tags {
    tags = {
      ProjectName = "Jenkins Extension"
      DeployedFrom = "Terraform"
      Repository = "de-lambda-deployment"
    }
  }
}
