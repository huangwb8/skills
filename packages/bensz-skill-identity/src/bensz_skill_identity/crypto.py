"""Ed25519 envelopes. Private key objects stay in caller memory."""

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from .protocol import (
    SCHEMA,
    IdentityError,
    canonical,
    fields,
    hex_value,
    publisher_id,
    require,
)


def public_hex(key: Ed25519PrivateKey | Ed25519PublicKey) -> str:
    public = key.public_key() if isinstance(key, Ed25519PrivateKey) else key
    return public.public_bytes(Encoding.Raw, PublicFormat.Raw).hex()


def sign(payload: dict, key: Ed25519PrivateKey, purpose: str) -> dict:
    require(purpose in {"manifest", "authorization", "security"})
    message = (SCHEMA + "/" + purpose + "\0").encode() + canonical(payload)
    return {
        "payload": payload,
        "public_key": public_hex(key),
        "signature": key.sign(message).hex(),
    }


def authenticate(
    envelope: dict, purpose: str, expected_public: str | None = None
) -> dict:
    fields(envelope, {"payload", "public_key", "signature"})
    public = hex_value(envelope["public_key"])
    if expected_public is not None:
        require(public == expected_public, "signature_invalid")
    signature = hex_value(envelope["signature"], 128)
    require(type(envelope["payload"]) is dict)
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public)).verify(
            bytes.fromhex(signature),
            (SCHEMA + "/" + purpose + "\0").encode() + canonical(envelope["payload"]),
        )
    except (InvalidSignature, ValueError) as exc:
        raise IdentityError("signature_invalid") from exc
    return envelope["payload"]


def authorize(
    root: Ed25519PrivateKey,
    release_public: str,
    keys: list[str],
    *,
    not_before: int,
    expires_at: int,
) -> dict:
    from .protocol import integer, skill_key

    require(type(keys) is list and keys and len(keys) == len(set(keys)))
    for key in keys:
        skill_key(key)
    integer(not_before)
    integer(expires_at)
    require(not_before < expires_at)
    return sign(
        {
            "schema": SCHEMA + "/authorization",
            "publisher_id": publisher_id(public_hex(root)),
            "release_public_key": hex_value(release_public),
            "skill_keys": sorted(keys),
            "not_before": not_before,
            "expires_at": expires_at,
        },
        root,
        "authorization",
    )


def security_metadata(
    root: Ed25519PrivateKey,
    *,
    revision: int,
    issued_at: int,
    expires_at: int,
    revoked_keys: list[str] | None = None,
    revoked_releases: list[str] | None = None,
    disabled: bool = False,
) -> dict:
    from .protocol import integer

    integer(revision)
    integer(issued_at)
    integer(expires_at)
    require(issued_at < expires_at and type(disabled) is bool)
    for key in (revoked_keys or []) + (revoked_releases or []):
        hex_value(key)
    return sign(
        {
            "schema": SCHEMA + "/security",
            "publisher_id": publisher_id(public_hex(root)),
            "revision": revision,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "revoked_keys": sorted(set(revoked_keys or [])),
            "revoked_releases": sorted(set(revoked_releases or [])),
            "disabled": disabled,
        },
        root,
        "security",
    )
