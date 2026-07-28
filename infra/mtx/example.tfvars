region  = "us-east-1"
profile = "" # the profile name setup with aws configure sso, leave empty to use AWS credentials from environment variables
tags = {
  project = "medtrax-dev"
}
data_source_bucket_arn = "arn:aws:s3:::<name-of-your-s3-bucket>"
ecr_repository_name    = ""  