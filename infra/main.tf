terraform {
    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "~> 5.0"
        }
    }
}

provider "aws" {
    region = "us-east-1"
}

resource "aws_s3_bucket" "raw_data" {
    bucket = "nyc-mobility-copilot-ms-15aug"
}

resource "aws_s3_bucket_versioning" "raw_data_versioning" {
    bucket = aws_s3_bucket.raw_data.id
    versioning_configuration {
        status = "Enabled"
    }
}
