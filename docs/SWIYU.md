# Swiss E-ID (swiyu) Integration

Dribdat supports authentication via the Swiss E-ID (swiyu) public beta using an OpenID Connect (OIDC) bridge.

## Configuration

To enable swiyu login, you need to configure the following environment variables:

- `OAUTH_TYPE`: Set this to `swiyu`.
- `OAUTH_ID`: Your Client ID from the swiyu developer portal or OIDC bridge.
- `OAUTH_SECRET`: Your Client Secret.
- `OAUTH_DOMAIN`: The base URL of your OIDC bridge (e.g., `sso.example.com`).
- `OAUTH_AUTH_URL`: (Optional) Full URL to the authorization endpoint if it doesn't follow the default `/authorize` path.
- `OAUTH_TOKEN_URL`: (Optional) Full URL to the token endpoint if it doesn't follow the default `/token` path.
- `OAUTH_USERINFO`: (Optional) Full URL or path to the userinfo endpoint (defaults to `/userinfo`).
- `OAUTH_SCOPE`: (Optional) Scopes to request, e.g., `openid,profile,email`.

## OID4VP Support

If you are using a direct OID4VP bridge that expects standard OIDC flows, you can also use `OAUTH_TYPE=oid4vp`. This will use the same configuration but display "Sign in with OID4VP" on the login page.

## Technical Details

The integration uses `Flask-Dance` and follows the standard OAuth2/OIDC Authorization Code flow. The flexible path configuration allows Dribdat to work with various OIDC bridges that might be used to interface with the Swiss Trust Infrastructure.

The following user claims are expected from the `userinfo` endpoint:
- `sub`: Unique identifier for the user (required).
- `email`: User's email address (required).
- `nickname`, `name`, or `preferred_username`: Used as the Dribdat username.

If no nickname is provided, the part of the email address before the `@` symbol will be used as a fallback.
