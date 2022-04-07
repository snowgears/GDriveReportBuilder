# Censys Generate Report
### This script creates a copy of a presentation in Google Drive, and auto-fills text placeholders with information from a given Censys ASM workspace.

# Steps for getting started:
- Install the libraries in requirements.txt
   - ```pip install --upgrade -r requirements.txt```
- Set the Censys ASM API key to the workspace you are reporting against
   - ```export CENSYS_ASM_API_KEY=xxxxxxxx-xxxx-xxxx-xxxxxxxxxxxx```
   - (find your ASM API key here: https://app.censys.io/integrations)
- Set the variables in the **generate_report.py** file
   - **TEMPLATE_FILE_ID** - the id of the google slides template presentation
     - You can locate this id by right clicking the file, and clicking *'Get link'*
     - Example:
       - https://docs.google.com/presentation/d/1yimWsG3k3QatKfdNky7iD6JzlJqbREb0w1HhFvEnphc/edit?usp=sharing
       - TEMPLATE_FILE_ID would be *1yimWsG3k3QatKfdNky7iD6JzlJqbREb0w1HhFvEnphc*
   - **COMPANY_NAME** - the name of the company
   - **AE_NAME** - the name of the account executive
   - **AE_EMAIL** - the email of the account executive
   - **SE_NAME** - the name of the solutions engineer
   - **SE_EMAIL** - the email of the solutions engineer

## Now just run the script:
``` 
python generate_report.py
```

You will be asked to sign in the with a Google account in your browser. Sign in to generate your OAuth token (token.json)
