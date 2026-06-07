# Ultra X Morocco 2026 — Training Dashboard

Personal training dashboard for the Ultra X Morocco 100km 2-stage race (November 14-15, 2026).

## Setup Strava Sync

1. Go to [Strava API Settings](https://www.strava.com/settings/api) and create an app
2. Set the **Authorization Callback Domain** to `localhost`
3. Note your **Client ID** and **Client Secret**
4. Get a refresh token by visiting:
   ```
   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&scope=activity:read_all
   ```
5. After authorizing, grab the `code` from the redirect URL and exchange it:
   ```bash
   curl -X POST https://www.strava.com/oauth/token \
     -d client_id=YOUR_CLIENT_ID \
     -d client_secret=YOUR_CLIENT_SECRET \
     -d code=YOUR_CODE \
     -d grant_type=authorization_code
   ```
6. Add these GitHub repository secrets:
   - `STRAVA_CLIENT_ID`
   - `STRAVA_CLIENT_SECRET`
   - `STRAVA_REFRESH_TOKEN`

The GitHub Action syncs daily at 08:00 NL time and can be triggered manually.
