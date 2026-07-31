resource "aws_dynamodb_table" "feedback" {
  name         = "medtrax-dev-feedback"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "message_id"
  range_key    = "feedback_id"

  attribute {
    name = "message_id"
    type = "S"
  }

  attribute {
    name = "feedback_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "retrievals" {
  name         = "medtrax-dev-retrievals"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "message_id"
  range_key    = "retrieval_id"

  attribute {
    name = "message_id"
    type = "S"
  }

  attribute {
    name = "retrieval_id"
    type = "S"
  }
}
