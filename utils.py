import os
import subprocess
from mimetypes import guess_type

from global_variables import BASE_DATA_CONVERTED_RECORDINGS_DIRECTORY

def convert_to_wav(input_file_path):
    
    mime_type, encoding = guess_type(input_file_path)

    if mime_type is None:
        print(f"Could not determine the MIME type of the file: {input_file_path}")
        return ""
    
    main_type = mime_type.split('/')[0]

    filename = ".".join(os.path.basename(input_file_path).split(".")[:-1])
    output_file_path = os.path.join(BASE_DATA_CONVERTED_RECORDINGS_DIRECTORY, filename + ".wav")

    command = ["ffmpeg", "-i", input_file_path]

    if main_type == 'audio':
        command.extend(["-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le"])
    elif main_type == 'video':
        command.extend(["-vn", "-ac", "1", "-ar", "16000", "-acodec", "pcm_s16le"])
    else:
        print(f"Unsupported MIME main type: {main_type}")
        return ""
    
    command.extend([output_file_path, "-y"])

    try:
        subprocess.run(command, check=True)
        return output_file_path
    except subprocess.CalledProcessError as e:
        print("Error while converting using ffmpeg:", e)
        return ""
