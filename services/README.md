# services

Her ligger alle ```serverless framework```-services som deployeres til aws.
De har hver sin ```serverless.yml``` som deployeres til et stage ved å kjøre
```serverless deploy --stage <stage>```.
Vi anbefaler å installere `serverless` globalt:
```bash
npm install --global serverless
```

Vi bruker disse stagesene:
* `prod`
* `dev` (default)
* `test` (for automatiske integrasjonstester m/ travis)

Deploy brukes også for å oppdatere stages som er live med ny kode, nye api-nøkler, roles, osv.
Hvis du kun skal oppdatere koden til en lambda trenger du ikke å kjøre deploy,
men kan kjøre ```serverless deploy function --stage <stage> --function myFunction```

OBS: det skal (i utgangspunktet) aldri være nødvendig å kjøre ```serverless remove``` for å
oppdatere noe, så tenk deg litt om.

Stagesene er i utgangspunktet helt uavhengige, men det meste av eksterne tjenester er bare koblet
til ```prod```, som for eksempel QuickSight, Slack og Github webhooks, Slack appen for events, osv.

Det er ikke en streng rekkefølge, men det er noen avhengigheter som bestemmer rekkefølgen
tjenestene kan deployeres (første gang).

før > etter:
* dynamodb > ingest
* dynamodb > fetch
* dynamodb > events_slack_app
* common_layers > ingest
* common_layers > fetch
* ingest > events_slack_app
* events_slack_app > structured_mysql

Kort sagt må ```dynamodb``` og ```common_layers``` deployeres først. For å deployere alle
services kan du kjøre:
```bash
./deploy_every_service.sh <stage>
```
Dette forutsetter at AWS systems manager inneholder verdiene som trengs for hver spesifikke
integrasjon. For en helt fresh deploy burde du derfor gå gjennom hver service sin README for
oppsett. For å populere SSM med API keys for et stage kan du kjøre
```bash
cd scripts/
python3 generate_keys.py
```


## QuickSight
NB: Disse instruksjonene gjelder første gang prod deployes, ikke for hvert datasett.

For å koble QuickSight til plattformen trenger du hostname og innlogginsinformasjon fra
prod-staget til `structured_mysql`. Etter du har deployet `structured_mysql`:
```bash
cat integration_tests/structured_mysql.serverless_outputs_prod.json
```
Her ligger alt du trenger for å legge til databasen som en data source i Quicksight. Bruk
`auroraClusterROEndpoint` som endpoint, siden QuickSight ikke trenger write access.
