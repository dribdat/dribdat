# -*- coding: utf-8 -*-
"""Connect to generative A.I. tools."""

import logging
import requests

import openai

from flask import current_app
from .user.models import Project

# In seconds, how long to wait for API response
REQUEST_TIMEOUT = 30

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
    # Collect project contents, preferring the pitch
    summary = project.longtext + '\n# README\n' + project.autotext
    summary = summary.replace('\n\n','\n').replace('  ', ' ')
    # Collect stage advice
    stage_advice = 'Be excellent to each other'
    if project.stage and 'tip' in project.stage:
        stage_advice = project.stage['tip'] + ' '
        if 'conditions' in project.stage:
            cc = []
            psc = project.stage['conditions']
            if 'validate' in psc and 'help' in psc['validate']:
                cc.append(psc['validate']['help'])
            if 'agree' in psc:
                cc.extend(psc['agree'])
            stage_advice = stage_advice + ' '.join(cc)
    # Generate the prompt
    return 'The project title is "%s", on the topic of "%s". ' % (title, topic) +\
        'Do not include the word "Suggestion" or repeat the title. ' +\
        'Consider that the team at this stage should ensure the following:\n%s\n' % (stage_advice) +\
        'Note that the following results have already been documented in the project: \n' +\
        summary


def gen_project_post(project: Project, as_boost: bool=False):
    """Returns results from a prompt that is used to generate posts."""
    prompt = prompt_ideas(project)
    if as_boost:
        # Use an evaluation type prompt
        prompt = 'You are a judge in a hackathon. Generate a short (100 words or less)' +\
                 ' evaluation of a project, focusing on clarity and sustainability. ' + prompt
    else:
        # Use the standard recommendation prompt
        prompt = 'Generate a short (100 words or less) suggestion as a next' +\
                 ' step in a hackathon project.' + prompt
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
    except openai.InternalServerError as e:
        logging.error('Server error (invalid model?)')
        return None
    except openai.APIConnectionError as e:
        logging.error('No LLM connection')
        return None
    except openai.RateLimitError as e:
        logging.error('Show me the money!')
        return None
    except Exception as e:
        logging.error(e)
        return None

    # Return the obtained result
    if len(completion.choices) > 0:
        mymodel = current_app.config['LLM_MODEL'].upper()
        content = completion.choices[0].message.content
        content = content.replace("\n", "\n> ")
        return "🅰️ℹ️ `Generated with %s`\n\n%s" % (mymodel, content)
    else:
        logging.error('No LLM data in response')
        return None

