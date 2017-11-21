from __future__ import print_function
import httplib, urllib, base64, json


# --------------- Helpers that build all of the responses ----------------------

headers = {
    # Request headers
    'api_key': 'e13626d03d8e4c03ac07f95541b3091b',
}


def get_next_bus(stop_id):
    try:
        conn = httplib.HTTPSConnection('api.wmata.com')
        params = urllib.urlencode({
            # Request parameters
            'StopID': stop_id,
        })
        conn.request("GET", "/NextBusService.svc/json/jPredictions?%s" % params, "{body}", headers)
        response = conn.getresponse()
        data = response.read()
        resp_obj = json.loads(data)
        next_buses = []
        if 'Predictions' in resp_obj.keys():
            predictions = resp_obj["Predictions"]
            for p in predictions:
                if 'Minutes' in p.keys():
                    next_buses.append("%d minutes" % p["Minutes"])
            print(next_buses)
        conn.close()
        return next_buses
    except Exception as e:
        print(e)


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to DC Next Bus. " \
                    "Please tell me what bus stop number you'd like information for by saying, " \
                    "next bus for 1001872"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please tell me your bus stop number by saying, " \
                    "next bus for 1001872."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for trying DC Next Bus. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def create_bus_attributes(stop_id):
    return {"stopId": stop_id}


def set_stop_in_session(intent, session):
    """ Sets the bus number in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False

    if 'StopId' in intent['slots']:
        stop_id = intent['slots']['StopId']['value']
        session_attributes = create_bus_attributes(stop_id)
        speech_output = "Bus stop set as " + \
                        stop_id
        reprompt_text = "You can ask me for the next buses by saying, " \
                        "next bus?"
    else:
        speech_output = "I'm not sure what bus stop you want information for. " \
                        "Please try again."
        reprompt_text = "I'm not sure what bus stop you want information for.  " \
                        "You can get information by saying, " \
                        "next bus for 1001872"
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_info_from_session(intent, session):
    session_attributes = {}
    reprompt_text = None

    if session.get('attributes', {}) and "stopId" in session.get('attributes', {}):
        stop_id = session['attributes']['stopId']
        #fetch bus info
        next_buses = get_next_bus(stop_id)
        if len(next_buses) != 0:
            bus_str = ",".join(next_buses)
            speech_output = "The next buses are in: " + \
                        bus_str + \
                        ". Goodbye."
        else:
            speech_output = "There are no upcoming buses. " \
                        "Goodbye."
        should_end_session = True
    elif 'StopId' in intent['slots']:
        stop_id = intent['slots']['StopId']['value']
        session_attributes = create_bus_attributes(stop_id)
        #fetch bus info
        next_buses = get_next_bus(stop_id)
        if len(next_buses) != 0:
            bus_str = ",".join(next_buses)
            speech_output = "The next buses are in: " + \
                        bus_str + \
                        ". Goodbye."
        else:
            speech_output = "There are no upcoming buses. " \
                        "Goodbye."
        should_end_session = True
    else:
        speech_output = "I'm not sure what bus stop you want information for. " \
                        "You can say, next bus for 1001872."
        should_end_session = False

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "MyStopIs":
        return set_stop_in_session(intent, session)
    elif intent_name == "NextBus":
        return get_info_from_session(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])