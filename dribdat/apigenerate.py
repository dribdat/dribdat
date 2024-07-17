# -*- coding: utf-8 -*-
"""Connect to generative A.I. tools."""

import logging
import requests

import openai

from flask import current_app
from .user.models import Project

# In seconds, how long to wait for API response
REQUEST_TIMEOUT = 10

# System prompt for our requests
SYSTEM_PROMPT = "A hackathon project involves: " +\
        "collecting data, designing a solution, and making a prototype. " +\
        "Typical stages include team formation, role play, brainstorming, " +\
        "design thinking, and prototyping with digital and physical tools." +\
        "Be brief, wise and positive in your statements. Encourage fairness."

# We may want to provide the user with the raw prompts.

def prompt_initial(project: Project):
    """Form a prompt used for a seed pitch in a project."""
    title = project.name
    topic = ""
    if project.category_id is not None:
        topic = project.category.description
    summary = project.summary
    return "Write a challenge statement for a hackathon project. " +\
        'Do not include the words "Challenge statement". ' +\
        'It is to be on the topic of "%s", involving "%s". Furthermore: %s' %\
        (title, topic, summary)


def gen_project_pitch(project: Project):
    """Returns results from a prompt used for a seed pitch in a project."""
    prompt = prompt_initial(project)
    return gen_openai(prompt)


def prompt_ideas(project: Project):
    """Form a prompt that is used to generate posts."""
    title = project.name
    topic = project.summary
    summary = project.longtext or project.autotext
    return "Generate a short (100 words or less) suggestion as a next step " +\
        'in a hackathon project, with title "%s" on the topic of "%s", ' % (title, topic) +\
        "in which so far the following has been worked on: \n" +\
        summary


def gen_project_post(project: Project):
    """Returns results from a prompt that is used to generate posts."""
    prompt = prompt_ideas(project)
    return gen_openai(prompt)


def gen_openai(prompt: str):
    """Request data from an OpenAI API."""
    if not current_app.config['LLM_API_KEY']:
        logging.error('Missing ChatGPT configuration (LLM_API_KEY)')
        return None

    # TODO: persist in app session
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
    
    # Attempt to get an interaction started
    try:
        completion = ai_client.chat.completions.create(
            model=current_app.config['LLM_MODEL'], 
            timeout=REQUEST_TIMEOUT,
            messages = [
                {
                    "role": "user", "content": prompt
                },{
                    "role": "system", "content": SYSTEM_PROMPT
                }
            ])
    except openai.APIConnectionError as e:
        logging.error('No LLM connection')
        return None

    # Return the obtained result
    if len(completion.choices) > 0:
        if completion.choices[0].message.content:
            content = completion.choices[0].message.content
        else:
            content = completion.choices[0].message
        return "🅰️ℹ️ " + content
    else:
        logging.error('No LLM data in response')
        return None

