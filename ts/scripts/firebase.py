import json

from django.conf import settings
# from firebase_admin import credentials
from firebase_admin import db, auth
import firebase_admin

# import pyrebase


def run():
    # refer : https://engineering.sada.com/how-to-use-json-web-tokens-for-service-to-service-authentication-b272059b7ed5

    project_id = 'trainstation-2-30223076'

    config = {
        "apiKey": "AIzaSyB_O_eamXZfqGmgHEksFKCpD4QEwciCBiM",
        "authDomain": f"{project_id}.firebaseapp.com",
        "databaseURL": "https://databaseName.firebaseio.com",
        "storageBucket": f"{project_id}.appspot.com"
    }

    # firebase = pyrebase.initialize_app(config)

    # credentials = settings.DJANGO_PATH / 'google-services-desktop.json'
    databaseURL = f"https://{project_id}.firebaseio.com/"

    token = json.loads(
"""
{"Success":true,"RequestId":"51692779-fb59-485e-aa8a-1c47bb79a526","Time":"2023-03-04T15:40:52Z","Data":{"Uid":"prod_76408422","Token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpc3MiOiJmaXJlYmFzZS1hZG1pbnNkay1nNmR6NkB0cmFpbnN0YXRpb24tMi0zMDIyMzA3Ni5pYW0uZ3NlcnZpY2VhY2NvdW50LmNvbSIsInN1YiI6ImZpcmViYXNlLWFkbWluc2RrLWc2ZHo2QHRyYWluc3RhdGlvbi0yLTMwMjIzMDc2LmlhbS5nc2VydmljZWFjY291bnQuY29tIiwiYXVkIjoiaHR0cHM6Ly9pZGVudGl0eXRvb2xraXQuZ29vZ2xlYXBpcy5jb20vZ29vZ2xlLmlkZW50aXR5LmlkZW50aXR5dG9vbGtpdC52MS5JZGVudGl0eVRvb2xraXQiLCJ1aWQiOiJwcm9kXzc2NDA4NDIyIiwiaWF0IjoxNjc3OTQ0NDUyLjY4NjY2MiwiZXhwIjoxNjc3OTQ4MDUyLjY4NjY2Mn0.0d1ZqUF_pQ0Y5Yd0ZH2zio9kznOeqDJ-7gOP9QMF8WWHMn0qpVR0magFYIi8a41Lzy5TTRXUQCh1IMRrB_aNNeUGxO9dDlb1H4DBt6NhdweR5ldtFBOONDbtvWJB0_L3hzeBU4PVWTn2Qhi2fEDt9A8AEbTJRDKaO9siNYG60dCwE9WfAtyYRNsz_y6R08ohoPJGUHxGO_c4o868VDLlifQ7aV3UFH-Ng4yspPrTIjpgYwHQGwtOiwL60PAv5F7O3dp-G-cfuvTAyZZy4Y50eyWDueW0LQjM_ZtD7exX9Jf9vibncDUbZW_C_MRAiBIdBBHfOusvxU8XtxTfTPAgLg","Env":"prod"}}
""", strict=False
    )
    cred_object = firebase_admin.auth

    default_app = firebase_admin.initialize_app()
    # cred_object = firebase_admin.credentials.ApplicationDefault
    # default_app = firebase_admin.initialize_app(cred_object, {
    #     'databaseURL': databaseURL
    #     })

    id_token = token['Data']['Token']
    decoded_token = firebase_admin.auth.verify_id_token(id_token)
    uid = decoded_token['uid']

    cred_object = firebase_admin.credentials.ApplicationDefault
    default_app = firebase_admin.initialize_app(cred_object, {
        'databaseURL':databaseURL
        })

    print(cred_object)
    print(default_app)

