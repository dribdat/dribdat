# -*- coding: utf-8 -*-
"""Connect to generative A.I. tools."""

import logging
import openai

from flask import current_app
from .user.models import Project

# In seconds, how long to wait for API response
REQUEST_TIMEOUT = 30

# Default system prompt for our requests
SYSTEM_PROMPT = (
    "A hackathon project involves: "
    + "collecting data, designing a solution, and making a prototype. "
    + "Typical stages include team formation, role play, brainstorming, "
    + "design thinking, and prototyping with digital and physical tools."
    + "Be brief, wise and positive in your statements. Encourage fairness."
)

# Default challenge prompts
INITIAL_CHALLENGE_PROMPT = (
    "Write a challenge statement for a collaborative hackathon project. " +
    "Include a section with a basic introduction and first steps. " +
    "Describe in a second section some example datasets and resources. " +
    "The last section should explain what kind of skills are involved. " +
    "Use dashes (---) to separate the sections."
)
INITIAL_PROJECT_PROMPT = (
    "Suggest one clear and concise next step for a hackathon project."
)

# If no other stage advice is found
DEFAULT_STAGE_ADVICE = "Be excellent to each other"

DEFAULT_EVALUATION_PROMPT = (
    "You are a judge in a hackathon."
    + "Generate a short (100 words or less) evaluation of a project,"
    + "focusing on clarity and sustainability."
)

DEFAULT_RECOMMENDATION_PROMPT = (
    "Generate a short (100 words or less) "
    + "suggestion as a next step in a hackathon project."
)

# CHAT_TEMPLATE_1 = "{% if messages[0]['role'] == 'system' %}{% set loop_messages = messages[1:] %}{% set system_message = messages[0]['content'] %}{% else %}{% set loop_messages = messages %}{% set system_message = false %}{% endif %}{% for message in loop_messages %}{% if (message['role'] == 'user') != (loop.index0 % 2 == 0) %}{{ raise_exception('Conversation roles must alternate user/assistant/user/assistant/...') }}{% endif %}{% if loop.index0 == 0 and system_message != false %}{% set content = '<<SYS>>\n' + system_message + '\n<</SYS>>\n\n' + message['content'] %}{% else %}{% set content = message['content'] %}{% endif %}{% if message['role'] == 'user' %}{{ bos_token + '[INST] ' + content + ' [/INST]' }}{% elif message['role'] == 'assistant' %}{{ ' '  + content + ' ' + eos_token }}{% endif %}{% endfor %}"


def prompt_initial(project: Project):
    """Form a prompt used for a seed pitch in a project."""
    title = project.name
    topic = ""
    if project.category_id is not None:
        topic = project.category.description
    summary = project.summary
    if topic:
        topic = 'The topic is "%s".' % topic
    if summary:
        summary = 'On the theme of: "%s".' % summary
    basep = INITIAL_PROJECT_PROMPT
    if project.is_challenge:
        basep = INITIAL_CHALLENGE_PROMPT
    return (
        basep
        + ' The title is "%s". %s %s' % (title, topic, summary)
        + ' Do not include the word "Suggestion" or "Challenge".'
        + " Do not repeat the title or topic.\n\n"
    )


def prompt_ideas(project: Project):
    """Form a prompt that is used to generate posts."""
    basep = prompt_initial(project)
    # Collect project contents, preferring the pitch
    summary = project.longtext
    if project.autotext:
        summary = summary + "\n\n# README\n" + project.autotext
    summary = summary.replace("\n\n", "\n").replace("  ", " ")
    # Collect stage advice
    stage_advice = DEFAULT_STAGE_ADVICE
    if not project.stage:
        pass
    elif "prompt" in project.stage and project.stage["prompt"]:
        stage_advice = project.stage["prompt"]
    elif "tip" in project.stage and project.stage["tip"]:
        stage_advice = project.stage["tip"] + " "
        if "conditions" in project.stage:
            cc = []
            psc = project.stage["conditions"]
            if "validate" in psc and "help" in psc["validate"]:
                cc.append(psc["validate"]["help"])
            if "agree" in psc:
                cc.extend(psc["agree"])
            stage_advice = stage_advice + " ".join(cc)
    if summary:
        summary = "Improve upon the following prior results:\n%s" % (summary)

    # Generate the prompt
    return (
        basep + "\n\n%s\n\n%s" % (stage_advice, summary)
    )


def gen_project_pitch(project: Project):
    """Returns results from a prompt used for a seed pitch in a project."""
    return gen_project_post(project, False)


def gen_project_post(project: Project, as_boost: bool = False):
    """Returns results from a prompt that is used to generate posts."""
    prompt = " " + prompt_ideas(project)
    if as_boost:
        # Use an evaluation type prompt
        prompt = DEFAULT_EVALUATION_PROMPT + prompt
    elif project.is_challenge:
        # The challenge prompt will be applied later
        pass
    else:
        # Use the standard recommendation prompt
        prompt = DEFAULT_RECOMMENDATION_PROMPT + prompt
    #print(prompt)
    return gen_openai(prompt)


def gen_openai(prompt: str):
    """Request data from a text-completion API."""
    if not current_app.config["LLM_API_KEY"]:
        logging.error("Missing ChatGPT configuration (LLM_API_KEY)")
        return None

    # TODO: persist in app session
    if current_app.config["LLM_BASE_URL"]:
        ai_client = openai.OpenAI(
            api_key=current_app.config["LLM_API_KEY"],
            base_url=current_app.config["LLM_BASE_URL"],
        )
    elif current_app.config["LLM_API_KEY"]:
        logging.info("Using default OpenAI provider")
        ai_client = openai.OpenAI(
            api_key=current_app.config["LLM_API_KEY"],
        )
    else:
        logging.error("No LLM configuration available")
        return None

    # Attempt to get an interaction started
    try:
        completion = ai_client.chat.completions.create(
            model=current_app.config["LLM_MODEL"],
            timeout=REQUEST_TIMEOUT,
            # chat_template=CHAT_TEMPLATE_1,
            messages=[
                {"role": "user", "content": prompt.strip()},
                {"role": "system", "content": SYSTEM_PROMPT.strip()},
            ],
        )
    except openai.InternalServerError as e:
        logging.error("Server error (invalid model?)")
        logging.debug(e)
        return None
    except openai.APIConnectionError:
        logging.error("No LLM connection")
        return None
    except openai.RateLimitError:
        logging.error("Rate limits exceeded")
        return None
    except Exception as e:
        logging.error(e)
        return None

    # Return the obtained result
    if len(completion.choices) > 0:
        mymodel = current_app.config["LLM_MODEL"].upper()
        content = completion.choices[0].message.content or ""
        #content = content.replace("\n", "\n> ")
        return "🅰️ℹ️ `Generated with %s`\n\n%s" % (mymodel, content)
    else:
        logging.error("No LLM data in response")
        return None
