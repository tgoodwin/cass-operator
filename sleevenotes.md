Need to install cert-manager before deploying to the cluster and integrating with webhooks


To run locally, use
```
WATCH_NAMESPACE=default go run cmd/main.go  --config config.json 
```
Webhook validation is turned off in config.json, so we dont have to deal with cert management
