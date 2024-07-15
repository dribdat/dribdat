# -*- coding: utf-8 -*-
"""Connect to generative A.I. tools."""

import logging
import requests
import openai

from flask import current_app
from .user.models import Project

# In seconds, how long to wait for API response
REQUEST_TIMEOUT = 10

def gen_project_pitch(project: Project):
    topic = ""
    if project.category:
        topic = project.category.name
    return gen_challenge_openai(project.name, topic, project.summary)
    
def gen_challenge_openai(title: str, topic: str, summary: str):
    """Request data from an OpenAI API."""
    if not current_app.config['LLM_API_KEY']:
        logging.error('Missing ChatGPT configuration (LLM_API_KEY)')
        return None
    # TODO: move to app.py
    if current_app.config['LLM_BASE_URL']:
        ai_client = openai.OpenAI(
            api_key=current_app.config['LLM_API_KEY'],
            base_url=current_app.config['LLM_BASE_URL']
        )
    elif current_app.config['LLM_API_KEY']:
        logging.info("Using default OpenAI provider")
        ai_client = openai.OpenAI(
            api_key=current_app.config['LLM_API_KEY'],
        )
    else:
        logging.error("No LLM configuration available")
        return None

    prompt = "Write a challenge statement for a hackathon project about the following: " +\
        '\n\n%s\n%s\n%s' % (title, topic, summary)
    
    response = ai_client.chat.completions.create(
        model=current_app.config['LLM_MODEL'], 
        timeout=REQUEST_TIMEOUT,
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ])
    jsondata = response.json()
    if 'choices' in jsondata and len(jsondata['choices']) > 0:
        return jsondata['choices'][0]['message']['content']
    else:
        logging.error('No LLM data in response')
        print(jsondata)
        return None

