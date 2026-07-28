#!/bin/bash


UP_CLIENT_ID=""
USERNAME=""
PWD=""

SESSION_ID=""


: '
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id ${UP_CLIENT_ID} \
  --auth-parameters USERNAME=${USERNAME},PASSWORD='${PWD}'
'


# Update Password
: '
aws cognito-idp respond-to-auth-challenge \
  --region us-east-1 \
  --client-id ${UP_CLIENT_ID} \
  --challenge-name NEW_PASSWORD_REQUIRED \
  --session "${SESSION_ID}" \
  --challenge-responses \
      USERNAME=${USERNAME},NEW_PASSWORD='${PWD}'
'
