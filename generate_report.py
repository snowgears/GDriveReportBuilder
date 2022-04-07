from __future__ import print_function

import datetime
import os.path
import os
import time
import requests
import json

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

CENSYS_API_KEY = os.getenv("CENSYS_ASM_API_KEY")
CENSYS_ENDPOINT = "https://app.censys.io/api"

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']
SHOW_TIMINGS = True

TEMPLATE_FILE_ID = '1yimWsG3k3QatKfdNky7iD6JzlJqbREb0w1HhFvEnphc'
COMPANY_NAME = 'Example Company'
AE_NAME = 'Tom Foobar'
AE_EMAIL = 'tom@sales.com'
SE_NAME = 'Adam Tech'
SE_EMAIL = 'adam@sales.com'

def main():
    start_time = time.time()
    creds = generate_google_credentials()
    try:
        # use the google creds to build the g-drive service and copy the template to its own file we will write to
        drive_service = build('drive', 'v3', credentials=creds)
        cloned_file = drive_service.files().copy(fileId=TEMPLATE_FILE_ID,
                           body={"parents": [{"kind": "drive#fileLink",
                                 "id": '1WuEO91PokKa_XsvMGwhvSs5YsCxyZ-9w'}], 'name': f'{COMPANY_NAME} - 2022 ASM Report'}).execute()

        # use the google creds to build the g-sheets service and make the replacements we want in the new file
        slides_service = build('slides', 'v1', credentials=creds)
        replace_text(slides_service, cloned_file['id'])

        # if SHOW_TIMINGS:
        #   print(f"--- total time to generate report: %s seconds ---" % (time.time() - start_time))

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')

def generate_google_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_all_counts():
    start_time = time.time()
    asset_counts = {}

    asset_counts["certificate_count"] = get_asset_counts("CERT")
    asset_counts["domain_count"] = get_asset_counts("DOMAIN")
    asset_counts["subdomain_count"] = get_asset_counts("SUBDOMAIN")
    asset_counts["host_count"] = get_asset_counts("HOST")
    asset_counts["software_count"] = get_asset_counts("SOFTWARE")
    asset_counts["storagebucket_count"] = get_asset_counts("STORAGE_BUCKET")

    # print(asset_counts)
    if SHOW_TIMINGS:
      print("--- get_all_counts: %s seconds ---" % (time.time() - start_time))

    return asset_counts

def replace_text(slides_service, file_id):
    date = datetime.datetime.now().strftime("%m/%d/%y")

    # Create the text merge (replaceAllText) requests for this presentation.
    requests_block = []
    requests_block.append(build_replace("<company name>", COMPANY_NAME, True))
    requests_block.append(build_replace("<date>", date, True))
    requests_block.append(build_replace("<AE Name>", AE_NAME, True))
    requests_block.append(build_replace("<AE Email>", AE_EMAIL, True))
    requests_block.append(build_replace("<SE Name>", SE_NAME, True))
    requests_block.append(build_replace("<SE Email>", SE_EMAIL, True))

    asset_counts = get_all_counts()
    requests_block.append(build_replace("<service_count>", str(asset_counts["software_count"]), True))
    requests_block.append(build_replace("<certificate_count>", str(asset_counts["certificate_count"]), True))
    requests_block.append(build_replace("<ip_count>", str(asset_counts["host_count"]), True))
    requests_block.append(build_replace("<domain_count>", str(asset_counts["domain_count"]), True))
    requests_block.append(build_replace("<subdomain_count>", str(asset_counts["subdomain_count"]), True))

    top_risks = get_top_risks()
    requests_block.append(build_replace("<risk1_name>", top_risks["risk1_name"], True))
    requests_block.append(build_replace("<risk1_count>", str(top_risks["risk1_count"]), True))
    requests_block.append(build_replace("<risk2_name>", top_risks["risk2_name"], True))
    requests_block.append(build_replace("<risk2_count>", str(top_risks["risk2_count"]), True))
    requests_block.append(build_replace("<risk3_name>", top_risks["risk3_name"], True))
    requests_block.append(build_replace("<risk3_count>", str(top_risks["risk3_count"]), True))
    requests_block.append(build_replace("<risk4_name>", top_risks["risk4_name"], True))
    requests_block.append(build_replace("<risk4_count>", str(top_risks["risk4_count"]), True))
    requests_block.append(build_replace("<risk5_name>", top_risks["risk5_name"], True))
    requests_block.append(build_replace("<risk5_count>", str(top_risks["risk5_count"]), True))

    requests_block.append(build_replace("<azure_risks>", str(get_cloud_risks("Microsoft Azure")), True))
    requests_block.append(build_replace("<aws_risks>", str(get_cloud_risks("Amazon AWS")), True))
    requests_block.append(build_replace("<gcp_risks>", str(get_cloud_risks("Google Cloud")), True))

    cloud_hosts = get_cloud_hosts()
    requests_block.append(build_replace("<azure_ips>", str(cloud_hosts["azure"]), True))
    requests_block.append(build_replace("<aws_ips>", str(cloud_hosts["aws"]), True))
    requests_block.append(build_replace("<gcp_ips>", str(cloud_hosts["gcp"]), True))
    requests_block.append(build_replace("<otherclouds_ips>", str(cloud_hosts["other"]), True))

    cloud_buckets = get_cloud_storage_buckets()
    requests_block.append(build_replace("<azure_buckets>", str(cloud_buckets["azure"]), True))
    requests_block.append(build_replace("<aws_buckets>", str(cloud_buckets["aws"]), True))
    requests_block.append(build_replace("<gcp_buckets>", str(cloud_buckets["gcp"]), True))
    requests_block.append(build_replace("<otherclouds_buckets>", str(cloud_buckets["other"]), True))

    print(cloud_buckets)

    cloud_domains = get_cloud_domains()
    requests_block.append(build_replace("<azure_domains>", str(cloud_domains["azure"]), True))
    requests_block.append(build_replace("<aws_domains>", str(cloud_domains["aws"]), True))
    requests_block.append(build_replace("<gcp_domains>", str(cloud_domains["gcp"]), True))
    requests_block.append(build_replace("<otherclouds_domains>", str(cloud_domains["other"]), True))

    print(cloud_domains)

    # Execute the batchupdate of text replace requests for this presentation.
    body = {
        'requests': requests_block
    }
    response = slides_service.presentations().batchUpdate(
        presentationId=file_id, body=body).execute()
    # print(response)

    # Count the total number of replacements made.
    num_replacements = 0
    for reply in response.get('replies'):
      try:
        num_replacements += reply.get('replaceAllText') \
            .get('occurrencesChanged')
      except TypeError:
        pass
    # print('Created presentation for %s with ID: %s' %
    #       (customer_name, presentation_copy_id))
    print('Replaced %d total text instances in the new report' % num_replacements)
    print('Created report for %s at https://docs.google.com/presentation/d/%s/edit?usp=sharing' %(COMPANY_NAME, file_id))


# this helps build the replaceAllText blocks that are needed to pass to the google batchUpdate method
def build_replace(text, replace_text, match_case):
    return {
              'replaceAllText': {
                  'containsText': {
                      'text': text,
                      'matchCase': match_case
                  },
                  'replaceText': replace_text
              }
          }


def list_files(drive_service):
    results = drive_service.files().list(
        pageSize=10, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])

    if not items:
        print('No files found.')
        return
    print('Files:')
    for item in items:
        print(u'{0} ({1})'.format(item['name'], item['id']))

#Handles copying of a file.
#If no new destination (parent) is provided, it is copied
#into the same location the original file was located.

# def copy(service, fileID, parents=None):
#     file_metadata = {}
#     if parents is not None: #If custom destination is specified, add it to the file metadata
#         file_metadata['parents'] = [parents]

#     #Copy the file
#     file = service.files().copy(
#         fileId=fileID,
#         body=file_metadata,
#         fields='id, name', #Can be whatever fields you want, I just like having access to the resulting file id & name
#         supportsAllDrives=True).execute()


# Retrieve counts of all asset categories
# CERT, DOMAIN, HOST, SOFTWARE, STORAGE_BUCKET, SUBDOMAIN
def get_asset_counts(asset_type):
    start_time = time.time()
    url = CENSYS_ENDPOINT + "/beta/assets/counts"

    payload={
      "assetType": asset_type
    }
    headers = {
        "Content-Type": "application/json",
        "censys-api-key": f"{CENSYS_API_KEY}"
    }
    
    response = requests.get(url, headers=headers, params=payload)

    data = json.loads(response.text)
    # print(data)
    if SHOW_TIMINGS:
      print(f"--- get_asset_counts({asset_type}): %s seconds ---" % (time.time() - start_time))
    return data["totalCount"]

def get_top_risks():
    start_time = time.time()
    url = CENSYS_ENDPOINT + "/v1/risks"

    payload={
      "pageNumber": 1
    }
    headers = {
        "Content-Type": "application/json",
        "censys-api-key": f"{CENSYS_API_KEY}"
    }
    
    response = requests.get(url, headers=headers, params=payload)
  
    data = json.loads(response.text)
    # print(data)

    top_risks = {}
    for x in range(1, 6):
      # risk names in v1 are not good so lets clean that up a bit
      risk_name = data["data"][x-1]["name"]
      period_index = risk_name.find(".", risk_name.find(".") + 1)
      top_risks[f"risk{x}_name"] = risk_name[(period_index+1):]
      top_risks[f"risk{x}_count"] = data["data"][x-1]["affectedAssetsCount"]

    if SHOW_TIMINGS:
      print("--- get_top_risks: %s seconds ---" % (time.time() - start_time))
    return top_risks

# get risks for a specific cloud
# Amazon AWS, Google Cloud, Microsoft Azure, otherCloud
def get_cloud_risks(cloud):
    start_time = time.time()
    url = CENSYS_ENDPOINT + "/v1/risks"

    payload={
      "cloud": cloud
    }
    headers = {
        "Content-Type": "application/json",
        "censys-api-key": f"{CENSYS_API_KEY}"
    }
    
    response = requests.get(url, headers=headers, params=payload)
  
    data = json.loads(response.text)
    # print(data)

    hosts_count = 0
    for risk in data["data"]:
      hosts_count += risk["affectedAssetsCount"]

    if SHOW_TIMINGS:
      print(f"--- get_cloud_risks({cloud}): %s seconds ---" % (time.time() - start_time))
    # print(hosts_count)
    return hosts_count

# get the host ip counts of every cloud
def get_cloud_hosts():
    start_time = time.time()
    url = CENSYS_ENDPOINT + "/v1/clouds/hostCounts/2015-01-01"

    payload={
    }
    headers = {
        "Content-Type": "application/json",
        "censys-api-key": f"{CENSYS_API_KEY}"
    }
    
    response = requests.get(url, headers=headers, params=payload)
  
    data = json.loads(response.text)
    # print(response.text)

    cloud_hosts = {}
    for cloud in data["assetCountByProvider"]:
      if cloud["cloudProvider"] == "Amazon AWS":
        cloud_hosts["aws"] = cloud["assetCount"]
      elif cloud["cloudProvider"] == "Google Cloud":
        cloud_hosts["gcp"] = cloud["assetCount"]
      elif cloud["cloudProvider"] == "Microsoft Azure":
        cloud_hosts["azure"] = cloud["assetCount"]
      elif cloud["cloudProvider"] == "otherCloud":
        cloud_hosts["other"] = cloud["assetCount"]
    

    if SHOW_TIMINGS:
      print("--- get_cloud_hosts: %s seconds ---" % (time.time() - start_time))
    # print(cloud_hosts)
    return cloud_hosts

# get the storage bucket counts of every cloud
def get_cloud_storage_buckets():
    start_time = time.time()
    url = CENSYS_ENDPOINT + "/v1/clouds/objectStoreCounts/2015-01-01"

    payload={
    }
    headers = {
        "Content-Type": "application/json",
        "censys-api-key": f"{CENSYS_API_KEY}"
    }
    
    response = requests.get(url, headers=headers, params=payload)
  
    data = json.loads(response.text)
    # print(response.text)

    cloud_buckets = {}
    for cloud in data["assetCountByProvider"]:
      if cloud["cloudProvider"] == "Amazon AWS":
        cloud_buckets["aws"] = cloud["assetCount"]
      elif cloud["cloudProvider"] == "Google Cloud":
        cloud_buckets["gcp"] = cloud["assetCount"]
      elif cloud["cloudProvider"] == "Microsoft Azure":
        cloud_buckets["azure"] = cloud["assetCount"]
      elif cloud["cloudProvider"] == "otherCloud":
        cloud_buckets["other"] = cloud["assetCount"]
    

    if SHOW_TIMINGS:
      print("--- get_cloud_storage_buckets: %s seconds ---" % (time.time() - start_time))
    # print(cloud_buckets)
    return cloud_buckets

# get the domain counts of every cloud
def get_cloud_domains():
    start_time = time.time()
    url = CENSYS_ENDPOINT + "/v1/clouds/domainCounts/2015-01-01"

    payload={
    }
    headers = {
        "Content-Type": "application/json",
        "censys-api-key": f"{CENSYS_API_KEY}"
    }
    
    response = requests.get(url, headers=headers, params=payload)
  
    data = json.loads(response.text)
    # print(response.text)

    cloud_domains = {}
    for cloud in data["assetCountByProvider"]:
      if cloud["cloudProvider"] == "Amazon AWS":
        cloud_domains["aws"] = cloud["assetCount"]
      elif cloud["cloudProvider"] == "Google Cloud":
        cloud_domains["gcp"] = cloud["assetCount"]
      elif cloud["cloudProvider"] == "Microsoft Azure":
        cloud_domains["azure"] = cloud["assetCount"]
      elif cloud["cloudProvider"] == "otherCloud":
        cloud_domains["other"] = cloud["assetCount"]
    

    if SHOW_TIMINGS:
      print("--- get_cloud_domains: %s seconds ---" % (time.time() - start_time))
    # print(cloud_domains)
    return cloud_domains

if __name__ == '__main__':
    main()
    # get_cloud_domains()
