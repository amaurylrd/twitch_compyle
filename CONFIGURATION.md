<!-- markdownlint-disable MD041 -->

## Configuration

The configuration is stored in a text file containing key value pairs of all the variables required by the application at execution.
This file helps to separate sensitive or environment-specific information from your source code, making it easier to manage and deploy the application.

In short, using a `.env` file will enable you to use environment variables for local development without polluting the global environment namespace. This file is untracked and should be included locally, and unconditionally never saved to source control so that you aren't putting potentially sensitive information at risk.

### Usage

See the `.env.example` file for more details. You can start by copying it to `.env` and filling the values with the following command:

```sh
cp .env.sample .env
```

See below the table of expected variables:

| environment variable        | type    | description                         | scope                | python setting             |
|-----------------------------|---------|-------------------------------------|----------------------|----------------------------|
| `DEBUG`                     | boolean | the debug mode flag (max verbosity) | collect,edit,publish |-                           |
| `YOUTUBE_APP_CLIENT_ID`     | string  | the Youtube client id               | publish              | `YOUTUBE["client_id"]`     |
| `YOUTUBE_APP_CLIENT_SECRET` | string  | the Youtube client secret           | publish              | `YOUTUBE["client_secret"]` |
| `YOUTUBE_APP_REDIRECT_URI`  | string  | the Youtube redirect uri            | publish              | `YOUTUBE["redirect_uri"]`  | 
| `YOUTUBE_APP_EMAIL_ADDRESS` | string  | the authorized email for consent    | publish              | `YOUTUBE["client_email"]`  | 
| `TWITCH_APP_CLIENT_ID`      | string  | the Twitch client id                | collect              | `TWITCH["client_id"]`      | 
| `TWITCH_APP_CLIENT_SECRET`  | string  | the Twitch client secret            | collect              | `TWITCH["client_secret"]`  |
| `TWITCH_APP_REDIRECT_URI`   | string  | the Twitch redirect uri             | collect              | `TWITCH["redirect_uri"]`   |
