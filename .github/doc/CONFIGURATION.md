<!-- markdownlint-disable MD041 -->

## Configuration

The configuration is stored in a text file containing key value pairs of all the variables required by the application at execution.
This file helps to separate sensitive or environment-specific information from your source code, making it easier to manage and deploy the application.

In short, using a `.env` file will enable you to use environment variables for local development without polluting the global environment namespace. This file is untracked and should be included locally, and unconditionally never saved to source control so that you aren't putting potentially sensitive information at risk.

### Usage

See the [.env.sample](../.env.sample) file for more details. You can start by copying it to `.env` and filling the values with the following command:

```sh
cp .env.sample .env
```

See below the table of expected variables:

| environment variable        | type    | description                         | scope   | python setting                 |
|-----------------------------|---------|-------------------------------------|---------|--------------------------------|
| `DEBUG`                     | boolean | the debug mode flag (max verbosity) | global  | -                              |
| `MONGO_DB_URI`              | string  | the MongoDB connection uri          | global  | `MONGO_CONFIG.client_uri`      |
| `MONGO_DB_NAME`             | string  | the MongoDB database name           | global  | `MONGO_CONFIG.client_name`     |
| `YOUTUBE_APP_CLIENT_ID`     | string  | the Youtube client id               | publish | `YOUTUBE_CONFIG.client_id`     |
| `YOUTUBE_APP_CLIENT_SECRET` | string  | the Youtube client secret           | publish | `YOUTUBE_CONFIG.client_secret` |
| `YOUTUBE_APP_REDIRECT_URI`  | string  | the Youtube redirect uri            | publish | `YOUTUBE_CONFIG.redirect_uri`  | 
| `YOUTUBE_APP_EMAIL_ADDRESS` | string  | the authorized email for consent    | publish | `YOUTUBE_CONFIG.client_email`  | 
| `TWITCH_APP_CLIENT_ID`      | string  | the Twitch client id                | collect | `TWITCH_CONFIG.client_id`      | 
| `TWITCH_APP_CLIENT_SECRET`  | string  | the Twitch client secret            | collect | `TWITCH_CONFIG.client_secret`  |
| `TWITCH_APP_REDIRECT_URI`   | string  | the Twitch redirect uri             | collect | `TWITCH_CONFIG.redirect_uri`   |
