---
id: twilio
title: Twilio
---

You can use the Twilio integration to call your LLMStack/Promptly app from a phone number via Twilio. To set up the Twilio integration, follow the steps below:

Go to https://console.twilio.com/ and setup your number. Once you have a number setup, get the `Account SID` and `Auth Token` from the dashboard and fill it up in the `integrations > Twilio` page of your LLMStack/Promptly app. Add the phone number associated with your Twilio account in the `Phone Number` field and click `Save App` (Do not add `+` in the phone number).

Copy the shown url in the integration page and set it as the messaging webhook url in your Twilio account for this number.

![Twilio Integration](/img/ui/twilio.png)

### Integration config from API

To add twilio configuration to an existing app from API, you can send a `PATCH` request to `/api/apps/<app_uuid>` with the following body:

:::info
Make sure to set the `Content-Type` header to `application/yaml` for the request if you are sending `YAML` data in the body.
:::

```yaml
twilio_config:
  account_sid: <account_sid>
  auth_token: <auth_token>
  phone_numbers: <comma_separated_phone_numbers>
```
