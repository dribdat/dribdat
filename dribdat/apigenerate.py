# -*- coding: utf-8 -*-
"""Connect to generative A.I. tools."""

import logging
import requests
import openai

from flask import current_app
from .user.models import Project

# In seconds, how long to wait for API response
REQUEST_TIMEOUT = 10

def prompt_initial(project: Project):
    title = project.name
    topic = ""
    if project.category_id is not None:
        topic = project.category.description
    summary = project.summary
    return "Write a challenge statement for a hackathon project, which involves " +\
        "collecting data, designing a solution, and making a prototype. " +\
        'Do not include the words "Challenge statement". ' +\
        'It is to be on the topic of "%s", involving "%s". Furthermore: %s' %\
        (title, topic, summary)

def prompt_ideas(project: Project):
    title = project.name
    topic = project.summary
    summary = project.longtext or project.autotext
    return "Generate a short (140 characters) suggestion of brainstorming, " +\
        "design thinking, or prototyping as a next step " +\
        'in a project with title "%s" on the topic of "%s", ' % (title, topic) +\
        "in which so far the following has been worked on: \n" +\
        summary

def gen_project_pitch(project: Project):
    prompt = prompt_initial(project)
    return gen_openai(prompt)

def gen_project_post(project: Project):
    prompt = prompt_ideas(project)
    return gen_openai(prompt)

def gen_openai(prompt: str):
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
    
    completion = ai_client.chat.completions.create(
        model=current_app.config['LLM_MODEL'], 
        timeout=REQUEST_TIMEOUT,
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ])
    completion.choices[0].message.content
    if len(completion.choices) > 0:
        return completion.choices[0].message.content
    else:
        logging.error('No LLM data in response')
        print(jsondata)
        return None

