from celery import current_app as celery
# from speech import get_speech_transcription
# from summary import get_minutes_of_meeting
import time

@celery.task(bind=True)
def process_audio(self, audio_path, filename):
    
    self.update_state(state='STARTED', meta={'info': 'Processing Audio File.', 'audio_path': audio_path, 'audio_filename': filename})
    time.sleep(10)
    
    # text = get_speech_transcription(audio_path)
    text = "Wow, what an audience. But if I'm being honest, I don't care what you think of my talk. I don't. I care what the internet thinks of my talk. Because they're the ones who get it seen and get it shared. And I think that's where most people get it wrong. They're talking to you here. Instead of talking to you random person, scrolling Facebook. Thanks for the click. You see, back in 2009, we all had these weird little things called attention spans. Yeah, they're gone. They're gone. We killed them. They're dead. I'm trying to think of the last time I watched an 18 minute TED Talk. It's been years, literally years. So if you're giving a TED Talk, keep it quick. I'm doing mine in under a minute. I'm at 44 seconds right now. That means we got time for one final joke. Why are balloons so expensive? Inflation. Thank you."
    
    self.update_state(state='PROGRESS', meta={'info': 'Text extracted, Summarizing now.', 'audio_path': audio_path, 'audio_filename': filename})
    time.sleep(10)
    
    # minutes_of_meeting = get_minutes_of_meeting(text)
    minutes_of_meeting = """Title 1: Perspective on Audience Engagement
    - The speaker emphasizes their indifference toward physical audience reception, focusing instead on online reactions.
    - Internet views are deemed more crucial as they increase visibility and sharing of content.

Title 2: Impact of Digital Media on Attention Spans
    - The speaker acknowledges the decline in attention spans due to digital media\'s influence since 2009."""
    
    self.update_state(state='SUCCESS', meta={'info': 'Summary Ready.', 'summary': minutes_of_meeting, 'audio_path': audio_path, 'audio_filename': filename})
    time.sleep(10)
    return {'summary': minutes_of_meeting, 'audio_path': audio_path, 'audio_filename': filename}

