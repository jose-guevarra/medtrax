import time

import boto3
import streamlit as st
from botocore.exceptions import ClientError

from core.config import Config


def _cognito_client(config: Config):
    return boto3.client("cognito-idp", region_name=config.aws_region)


def _extract_tokens(auth_result: dict) -> dict:
    return {
        "access_token": auth_result["AccessToken"],
        "id_token": auth_result["IdToken"],
        "refresh_token": auth_result.get("RefreshToken"),
        "expires_at": time.time() + auth_result["ExpiresIn"],
    }


def initiate_auth(config: Config, username: str, password: str) -> dict:
    """Returns {"challenge": "NEW_PASSWORD_REQUIRED", "session": ..., "username": ...}
    or {"tokens": {...}, "username": ...}."""
    resp = _cognito_client(config).initiate_auth(
        ClientId=config.cognito_client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": username, "PASSWORD": password},
    )
    if resp.get("ChallengeName") == "NEW_PASSWORD_REQUIRED":
        return {
            "challenge": "NEW_PASSWORD_REQUIRED",
            "session": resp["Session"],
            "username": username,
        }
    return {"tokens": _extract_tokens(resp["AuthenticationResult"]), "username": username}


def respond_new_password(config: Config, username: str, new_password: str, session: str) -> dict:
    resp = _cognito_client(config).respond_to_auth_challenge(
        ClientId=config.cognito_client_id,
        ChallengeName="NEW_PASSWORD_REQUIRED",
        ChallengeResponses={"USERNAME": username, "NEW_PASSWORD": new_password},
        Session=session,
    )
    return _extract_tokens(resp["AuthenticationResult"])


def _refresh_access_token(config: Config) -> bool:
    auth = st.session_state.get("auth")
    if not auth or not auth.get("refresh_token"):
        return False
    try:
        resp = _cognito_client(config).initiate_auth(
            ClientId=config.cognito_client_id,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": auth["refresh_token"]},
        )
        new_tokens = _extract_tokens(resp["AuthenticationResult"])
        new_tokens["refresh_token"] = auth["refresh_token"]  # not rotated by Cognito
        st.session_state.auth = {**auth, **new_tokens}
        return True
    except ClientError:
        st.session_state.auth = None
        return False


def is_authenticated(config: Config) -> bool:
    auth = st.session_state.get("auth")
    if not auth:
        return False
    if time.time() >= auth["expires_at"] - 60:
        return _refresh_access_token(config)
    return True


def get_access_token(config: Config) -> str | None:
    return st.session_state.auth["access_token"] if is_authenticated(config) else None


def logout():
    st.session_state.auth = None
    st.session_state.challenge = None
