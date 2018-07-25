
### Frichti-Slack

It's a slack bot that facilitate team lunch.

### Dependencies

 - serverless
 - serverless-python-requirements
 - docker
 - aws properly configured


### Deployment

At the root directory of the project execute :

```
sls deploy -a -s dev
```

Copy/paste the endpoint url to your slack api management interface. Both for the slash command and to the callback of interactive components

Enjoy it !
