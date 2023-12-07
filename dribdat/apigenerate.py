# -*- coding: utf-8 -*-
"""Connect to generative A.I. tools."""

import logging
import requests
from flask import current_app
from .user.models import Project

# In seconds, how long to wait for API response
REQUEST_TIMEOUT = 30


def gen_project_pitch(project: Project):
    return gen_challenge_openai(project.name, project.summary)
    
def gen_challenge_discolm(title: str, summary: str):
    API_URL = "https://api-inference.huggingface.co/models/DiscoResearch/DiscoLM-120b"
    headers = {"Authorization": "Bearer %s" % current_app.config['LLM_API_KEY']}
    payload = {
        "inputs": "Write a challenge statement for a tech sprint or hackathon project about " +\
            '%s. Do not include, but make it relevant to the title "%s"' % (summary, title)
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

def gen_challenge_openai(title: str, summary: str):
    if not current_app.config['LLM_API_KEY']:
        logging.error('Missing ChatGPT configuration (LLM_API_KEY)')
        return None
    API_URL = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": "Bearer %s" % current_app.config['LLM_API_KEY'],
               "Content-Type": "application/json" }
    prompt = "Write a challenge statement for a tech sprint or hackathon project about " +\
        '%s. Do not include, but make it relevant to the title "%s"' % (summary, title)
    payload = {
         "model": "gpt-3.5-turbo",
         "messages": [{"role": "user", "content": prompt}],
         "temperature": 0.7
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    jsondata = response.json()
    print (jsondata)
    if 'choices' in jsondata and len(jsondata['choices']) > 0:
        return jsondata['choices'][0]['message']['content']
    else:
        logging.error('No ChatGPT data')
        print (jsondata)
        return None

