# Public.com API Reference

## Auth Flow
1. User provides `PUBLIC_API_SECRET_KEY` (from https://public.com/settings/security/api)
2. Agent exchanges the secret key for a short-lived access token at runtime
3. Token is valid for ~8 hours (480 minutes)

## Endpoints
- Account: `GET /userapigateway/trading/account`
- Positions: `GET /userapigateway/trading/positions`
- Orders: `POST /userapigateway/trading/orders`
- Quotes: `GET /userapigateway/marketdata/{account_id}/quotes`
- Expirations: `GET /userapigateway/options/expirations`
- Chain: `GET /userapigateway/options/chain`

## Rate Limits
Configured with 4 max attempts, 0.5s base delay, 8.0s max delay, 0.25s jitter.
