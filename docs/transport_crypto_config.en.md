> [简体中文](transport_crypto_config.md) | **English**

# Transport-Layer Encryption/Decryption Configuration Guide

## Mode Overview

`TRANSPORT_CRYPTO_MODE` supports three modes:

- `off`
  Transport-layer encryption/decryption is fully disabled. The middleware does not perform request decryption or response encryption, and the policy the frontend obtains via `/transport/crypto/frontend-config` is disabled accordingly.
- `optional`
  Optional encryption mode. Matched endpoints accept both plaintext and encrypted requests; if a request is already encrypted, the backend decrypts it before processing and automatically encrypts the matched JSON response. Suitable for gradual rollout and observation during the early launch phase.
- `required`
  Enforced encryption mode. Matched endpoints must carry a valid encryption envelope, and plaintext requests are rejected outright; anti-replay validation also runs in strict mode, rejecting requests even when Redis is unavailable. Suitable for the formal enforcement phase once the link is stable.

Additional notes:

- When `TRANSPORT_CRYPTO_ENABLED=false`, the overall effect is equivalent to being disabled, and the transport-layer encryption/decryption logic is no longer entered.
- `TRANSPORT_CRYPTO_ENABLED_PATHS`, `TRANSPORT_CRYPTO_REQUIRED_PATHS`, and `TRANSPORT_CRYPTO_EXCLUDE_PATHS` further constrain the matching scope on top of the modes above.

## Development Environment

For the development environment, simply use the working key pair provided by default in `.env.dev`.

Notes:

- Once transport-layer encryption/decryption is enabled, the backend must read a matching pair of `TRANSPORT_CRYPTO_PUBLIC_KEY` / `TRANSPORT_CRYPTO_PRIVATE_KEY` at startup.
- The frontend automatically reads `/transport/crypto/frontend-config` and follows the backend configuration to perform request encryption and response decryption.
- `/transport/crypto/frontend-config` and `/transport/crypto/public-key` are public endpoints with anonymous rate limiting already configured; the frontend calls these two endpoints directly to complete initialization.
- `TRANSPORT_CRYPTO_FRONTEND_CONFIG_TTL_SECONDS` controls how often the frontend re-fetches the runtime policy.
- `TRANSPORT_CRYPTO_PUBLIC_KEY_TTL_SECONDS` controls how often the frontend re-fetches the public key; the two are now independent.

## Production Environment

The production environment uses the key configuration in the backend's `.env.prod`; the repository provides a set of working example values by default, so replace them with your real keys before going live.

The recommended minimal configuration is as follows:

```env
TRANSPORT_CRYPTO_ENABLED=true
TRANSPORT_CRYPTO_MODE='optional'
TRANSPORT_CRYPTO_KID='2026-prod-v1'
TRANSPORT_CRYPTO_PUBLIC_KEY='-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----\n'
TRANSPORT_CRYPTO_PRIVATE_KEY='-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n'
TRANSPORT_CRYPTO_LEGACY_KEY_PAIRS='[]'
TRANSPORT_CRYPTO_FRONTEND_CONFIG_TTL_SECONDS=300
TRANSPORT_CRYPTO_PUBLIC_KEY_TTL_SECONDS=3600
TRANSPORT_CRYPTO_CLOCK_SKEW_SECONDS=120
TRANSPORT_CRYPTO_MAX_GET_URL_LENGTH=4096
```

Notes:

- `TRANSPORT_CRYPTO_PUBLIC_KEY` and `TRANSPORT_CRYPTO_PRIVATE_KEY` must be a matching pair; neither can be omitted.
- `TRANSPORT_CRYPTO_KID` denotes the currently active key version.
- `TRANSPORT_CRYPTO_FRONTEND_CONFIG_TTL_SECONDS` controls the frontend cache duration for `/transport/crypto/frontend-config`; it is best kept relatively short when the policy is adjusted frequently.
- `TRANSPORT_CRYPTO_PUBLIC_KEY_TTL_SECONDS` controls the frontend cache duration for `/transport/crypto/public-key`, mainly serving public-key caching and key rotation.
- `TRANSPORT_CRYPTO_CLOCK_SKEW_SECONDS` is recommended to be kept within `60-120` seconds, tightened to `120` seconds by default.
- `TRANSPORT_CRYPTO_REPLAY_TTL_SECONDS` controls the validity period of anti-replay nonces in Redis; if you plan to use `required` mode, it is recommended to ensure Redis is stably available.
- For the initial launch, it is recommended to start with `TRANSPORT_CRYPTO_MODE='optional'`, and only consider switching to `required` after confirming the link is stable.
- `TRANSPORT_CRYPTO_MAX_GET_URL_LENGTH` limits the URL length of encrypted GET/DELETE requests; the frontend automatically syncs this value via `/transport/crypto/frontend-config`, and when the limit is exceeded it directly prompts you to switch to POST or simplify the query conditions.
- Transport-layer encryption mainly targets query parameters, `application/json`, and `application/x-www-form-urlencoded` requests; `multipart/form-data` upload and download endpoints are excluded by default.

## Docker Environment

The current project's Docker deployment uses:

- `docker-compose.yml` (MySQL by default, `Dockerfile.my`)
- `docker-compose.yml --env-file .env.pg` (PostgreSQL, `Dockerfile.pg`)

The backend container startup commands are, respectively:

- `python app.py --env=dockermy`
- `python app.py --env=dockerpg`

Therefore, in the Docker environment you need to configure the transport-layer keys directly in the following files:

- `api/.env.dockermy`
- `api/.env.dockerpg`

The configuration approach is the same as for the production environment; `.env.dockermy` / `.env.dockerpg` also provide a set of working example values by default, so replace them with your real keys before going live.

To use them, you only need to:

1. Modify the corresponding `.env.dockermy` or `.env.dockerpg`
2. Rebuild and start the Docker services

## Key Generation

Generate a set of RSA keys using `openssl`:

```bash
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out transport_private.pem
openssl rsa -pubout -in transport_private.pem -out transport_public.pem
```

If you need to write them into `.env`, first convert them into a single-line format with `\n`:

```bash
awk 'NF {sub(/\r/, ""); printf "%s\\\\n",$0;}' transport_private.pem
awk 'NF {sub(/\r/, ""); printf "%s\\\\n",$0;}' transport_public.pem
```

## Usage Flow

1. At startup, the backend reads the current `TRANSPORT_CRYPTO_*` configuration and verifies that both the public and private keys are present and match each other.
2. The frontend obtains the current runtime policy via `/transport/crypto/frontend-config`, then obtains the current `kid`, protocol version, and public key via `/transport/crypto/public-key`.
3. `TRANSPORT_CRYPTO_FRONTEND_CONFIG_TTL_SECONDS` and `TRANSPORT_CRYPTO_PUBLIC_KEY_TTL_SECONDS` respectively control the refresh cycles for these two kinds of caches.
4. The frontend encrypts requests with the public key, and the backend decrypts requests with the private key.
5. The backend automatically encrypts matched JSON responses, and the frontend automatically decrypts them; excluded scenarios such as downloads and uploads remain in plaintext.

## Key Rotation

If you need to replace the keys:

1. Generate a new key pair.
2. Change `TRANSPORT_CRYPTO_KID` to the new version, for example `2026-prod-v2`.
3. Configure the new `TRANSPORT_CRYPTO_PUBLIC_KEY` and `TRANSPORT_CRYPTO_PRIVATE_KEY`.
4. Place the old private key into `TRANSPORT_CRYPTO_LEGACY_KEY_PAIRS`.

Additional notes:

- `TRANSPORT_CRYPTO_LEGACY_KEY_PAIRS` is mainly used for compatible decryption of legacy messages; at minimum you only need to provide the `kid` and the old private key. `publicKey` is optional, and when omitted the backend derives it from the private key.
- During rotation, it is recommended to retain the old private key until all old public-key caches have expired, covering at least the cache window corresponding to `TRANSPORT_CRYPTO_PUBLIC_KEY_TTL_SECONDS`.

Example:

```env
TRANSPORT_CRYPTO_KID='2026-prod-v2'
TRANSPORT_CRYPTO_LEGACY_KEY_PAIRS='[{"kid":"2026-prod-v1","privateKey":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"}]'
```
