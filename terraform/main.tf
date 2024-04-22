terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket = "nc-de-demo-terraform-state"
    key = "de-s3-file-reader/terraform.tfstate"
    region = "eu-west-2"
  }
}

provider "aws" {
  region = "eu-west-2"
  default_tags {
    tags = {
      ProjectName = "S3 File Reader Demo"
      Team = "Data Engineering"
      DeployedFrom = "Terraform"
      Repository = "de-s3-file-reader"
      CostCentre = "DE"
      Environment = "dev"
      RetentionDate = "2024-05-31"
    }
  }
}